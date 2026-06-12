"""Multi-model audit panel (S9) - criticality-scaled review before merge.

Rational-token design (human's policy):
- Normal work (author = free/cheap model): 1 auditor, a DIFFERENT free model
  (diversity costs nothing).
- Critical work (auth/payments/data or critical=True): 3 auditors - two free
  models + codex if its ration allows - majority consensus.
- Premium-authored work (claude) already passes a HUMAN checkpoint, so no
  premium auditor is spent by default.

Auditors are READ-ONLY: they receive the diff + context and return a verdict;
they do not get a worktree and are exempt from the memory-handoff protocol.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import config, subscription
from .brains import opencode as oc_brain
from .brains import codex as codex_brain

VERDICT_APPROVED = "APROBADO"
VERDICT_REJECTED = "RECHAZADO"


@dataclass
class AuditReport:
    approved: bool
    votes: list[tuple[str, bool]] = field(default_factory=list)  # (model, approved)
    details: str = ""


def _diff_of(worktree: Path, max_chars: int = 60_000) -> str:
    proc = subprocess.run(
        ["git", "-C", str(worktree), "diff", "main...HEAD", "--unified=3"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        stdin=subprocess.DEVNULL,
    )
    diff = proc.stdout or ""
    if not diff.strip():
        proc = subprocess.run(  # uncommitted work
            ["git", "-C", str(worktree), "diff", "--unified=3"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL,
        )
        diff = proc.stdout or ""
    return diff[:max_chars]


def _audit_prompt(diff: str, context: str) -> str:
    return (
        "Eres un auditor de código escéptico del equipo MG. Tu trabajo es ENCONTRAR "
        "problemas, no aprobar rápido. Audita este diff buscando: secretos hardcodeados, "
        "inputs sin validar, inyección (SQL/XSS/command), errores de lógica, desviaciones "
        "del contrato, manejo de errores ausente.\n\n"
        f"Contexto de la tarea: {context}\n\n"
        "=== DIFF ===\n" + diff + "\n=== FIN DIFF ===\n\n"
        f"Responde EXACTAMENTE en este formato:\nVEREDICTO: {VERDICT_APPROVED} o "
        f"{VERDICT_REJECTED}\nHALLAZGOS:\n- (lista, severidad crítico/mayor/menor; "
        "'ninguno' si no hay)\n"
        f"Rechaza SOLO si hay hallazgos críticos."
    )


def _parse_verdict(text: str) -> bool:
    up = (text or "").upper()
    if VERDICT_REJECTED in up:
        return False
    return VERDICT_APPROVED in up  # missing/garbled verdict counts as NOT approved


def audit_worktree(
    worktree: Path,
    author_model: str | None,
    context: str = "",
    critical: bool = False,
    timeout_s: int = 600,
) -> AuditReport:
    diff = _diff_of(worktree)
    if not diff.strip():
        return AuditReport(True, details="empty diff - nothing to audit")

    prompt = _audit_prompt(diff, context)

    # pick free auditors DIFFERENT from the author model (diversity for free)
    free_pool = [m for m in config.OPENCODE_FREE_MODELS if m != author_model]
    auditors = free_pool[:1] if not critical else free_pool[:2]

    votes: list[tuple[str, bool]] = []
    notes: list[str] = []
    for model in auditors:
        res = oc_brain.invoke(prompt, worktree, timeout_s, model)
        ok = res.status == "ok" and _parse_verdict(res.output)
        votes.append((model, ok))
        notes.append(f"[{model}] {'OK' if ok else 'REJECT/FAIL'}: {res.output[:400]}")

    if critical and subscription.available(config.BRAIN_CODEX):
        res = codex_brain.invoke(prompt, worktree, timeout_s)
        subscription.record_call(config.BRAIN_CODEX)
        if res.status == "rate_limited":
            subscription.report_rate_limit(config.BRAIN_CODEX)
            notes.append("[codex] rate-limited - skipped")
        else:
            ok = res.status == "ok" and _parse_verdict(res.output)
            votes.append(("codex", ok))
            notes.append(f"[codex] {'OK' if ok else 'REJECT/FAIL'}: {res.output[:400]}")

    if not votes:
        return AuditReport(False, details="no auditors could run")
    approvals = sum(1 for _, ok in votes if ok)
    approved = approvals > len(votes) / 2  # majority
    return AuditReport(approved, votes, "\n".join(notes))
