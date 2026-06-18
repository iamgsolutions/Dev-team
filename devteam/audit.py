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

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import config, subscription
from .brains import opencode as oc_brain
from .brains import codex as codex_brain
from .brains import gemini as gemini_brain

VERDICT_APPROVED = "APPROVED"
VERDICT_REJECTED = "REJECTED"
# Accept both English and Spanish verdict tokens so the parser never breaks if a
# model answers in either language (the skills are English; some models reply ES).
_APPROVED_TOKENS = ("APPROVED", "APROBADO")
_REJECTED_TOKENS = ("REJECTED", "RECHAZADO")
# A findings line marked critical (EN or ES), e.g. "- critical: ..." / "- [crítico] ...".
# The engine ENFORCES critical => rejected, instead of trusting the verdict token
# alone (a model that lists a critical bug but writes APPROVED is still rejected).
_CRITICAL_FINDING_RE = re.compile(r"^\s*[-*]\s*\[?\s*(critical|cr[ií]tico)\b",
                                  re.IGNORECASE | re.MULTILINE)


@dataclass
class AuditReport:
    approved: bool
    votes: list[tuple[str, bool]] = field(default_factory=list)  # (model, approved)
    details: str = ""


def _diff_of(worktree: Path, max_chars: int = 60_000) -> str:
    def _run(args: list[str]) -> str:
        try:
            proc = subprocess.run(
                ["git", "-C", str(worktree), *args],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                stdin=subprocess.DEVNULL, timeout=60,
            )
            return proc.stdout or ""
        except subprocess.TimeoutExpired:
            return ""
    diff = _run(["diff", "main...HEAD", "--unified=3"])
    if not diff.strip():
        diff = _run(["diff", "--unified=3"])   # uncommitted work
    return diff[:max_chars]


def _audit_prompt(diff: str, context: str) -> str:
    return (
        "You are a skeptical code auditor on the MG team. Your job is to FIND "
        "problems, not to approve fast. Audit this diff for: hardcoded secrets, "
        "unvalidated inputs, injection (SQL/XSS/command), logic errors, contract "
        "deviations, missing error handling.\n\n"
        f"Task context: {context}\n\n"
        "=== DIFF ===\n" + diff + "\n=== END DIFF ===\n\n"
        f"Reply EXACTLY in this format:\nVERDICT: {VERDICT_APPROVED} or "
        f"{VERDICT_REJECTED}\nFINDINGS:\n- (list, severity critical/major/minor; "
        "'none' if there are none)\n"
        "Reject ONLY if there are critical findings."
    )


def _parse_verdict(text: str) -> bool:
    t = text or ""
    up = t.upper()
    if any(tok in up for tok in _REJECTED_TOKENS):
        return False
    # Safety net: a stated APPROVED is overridden if the auditor listed a CRITICAL
    # finding (skills + audit prompt say critical => reject; enforce it here).
    if _CRITICAL_FINDING_RE.search(t):
        return False
    return any(tok in up for tok in _APPROVED_TOKENS)  # missing/garbled = NOT approved


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

    if critical:
        # Premium vote for critical work: prefer GEMINI (saves codex ration),
        # fall back to codex if gemini is resting.
        premium = None
        if subscription.available(config.BRAIN_GEMINI):
            premium = (config.BRAIN_GEMINI, gemini_brain.invoke)
        elif subscription.available(config.BRAIN_CODEX):
            premium = (config.BRAIN_CODEX, codex_brain.invoke)
        if premium:
            name, inv = premium
            res = inv(prompt, worktree, timeout_s)
            subscription.record_call(name)
            if res.status == "rate_limited":
                subscription.report_rate_limit(name)
                notes.append(f"[{name}] rate-limited - skipped")
            else:
                ok = res.status == "ok" and _parse_verdict(res.output)
                votes.append((name, ok))
                notes.append(f"[{name}] {'OK' if ok else 'REJECT/FAIL'}: {res.output[:400]}")

    if not votes:
        return AuditReport(False, details="no auditors could run")
    approvals = sum(1 for _, ok in votes if ok)
    approved = approvals > len(votes) / 2  # majority
    return AuditReport(approved, votes, "\n".join(notes))
