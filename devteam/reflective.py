"""Reflective memory / model scorecard (S14) - accountability per model.

Every task outcome is recorded per model: ok, error, timeout, rate_limited,
handoff_violated, gate_failed, audit_rejected. Hermes (and the human) read the
scorecard to spot models that underperform and bench them (human's mandate:
"si algunos modelos cometen muchos fallos hay que quitarlos del equipo").

Traceability is double:
- git: every engine commit carries a `Model:` trailer (see worktree.commit_all)
- here: aggregated stats per model in data/scorecard.json

bench(model) marks a model as benched; the opencode fallback chain skips it.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import config

GOOD = "ok"
BAD_EVENTS = ("error", "timeout", "rate_limited", "handoff_violated",
              "gate_failed", "audit_rejected", "output_missing")


def _path() -> Path:
    return config.DATA_DIR / "scorecard.json"


def _load() -> dict:
    from .storage import load_json_safe
    d = load_json_safe(_path(), {"models": {}, "benched": []})
    d.setdefault("models", {})
    d.setdefault("benched", [])
    return d


def _save(d: dict) -> None:
    from .storage import atomic_write_json
    config.ensure_dirs()
    atomic_write_json(_path(), d)


def record(model: str, brain: str, event: str, note: str = "") -> None:
    if not model:
        return
    d = _load()
    m = d["models"].setdefault(model, {"brain": brain, "events": {}, "last": []})
    m["brain"] = brain
    m["events"][event] = m["events"].get(event, 0) + 1
    m["last"] = ([{"ts": datetime.now(timezone.utc).strftime("%m-%d %H:%M"),
                   "event": event, "note": note[:80]}] + m.get("last", []))[:20]
    _save(d)


def success_rate(model: str) -> float | None:
    d = _load()
    m = d["models"].get(model)
    if not m:
        return None
    ok = m["events"].get(GOOD, 0)
    bad = sum(m["events"].get(e, 0) for e in BAD_EVENTS)
    total = ok + bad
    return (ok / total) if total else None


def bench(model: str) -> None:
    d = _load()
    if model not in d["benched"]:
        d["benched"].append(model)
    _save(d)


def unbench(model: str) -> None:
    d = _load()
    d["benched"] = [m for m in d["benched"] if m != model]
    _save(d)


def is_benched(model: str) -> bool:
    return model in _load()["benched"]


def benched_models() -> list[str]:
    return list(_load()["benched"])


# Auto-bench thresholds: judge only with enough evidence, bench sustained losers.
AUTO_BENCH_MIN_TASKS = 8
AUTO_BENCH_MAX_RATE = 0.40      # < 40% success over the window -> bench
# Premium subscription brains are NEVER auto-benched (rate limits look like
# failures and we don't want to bench a paid brain over a transient window).
AUTO_BENCH_PROTECTED = {"claude", "codex", "gemini"}


def auto_bench() -> list[str]:
    """Bench models with sustained low success (>= MIN tasks, < MAX rate).
    Returns the models newly benched. Premium brains are protected."""
    d = _load()
    newly: list[str] = []
    for model, m in d["models"].items():
        if model in d["benched"] or m.get("brain") in AUTO_BENCH_PROTECTED:
            continue
        ok = m["events"].get(GOOD, 0)
        bad = sum(m["events"].get(e, 0) for e in BAD_EVENTS)
        total = ok + bad
        if total >= AUTO_BENCH_MIN_TASKS and (ok / total) < AUTO_BENCH_MAX_RATE:
            d["benched"].append(model)
            newly.append(model)
    if newly:
        _save(d)
    return newly


def format_report() -> str:
    d = _load()
    if not d["models"]:
        return "empty scorecard (no tasks recorded yet)"
    lines = [f"{'MODEL':<45} {'OK':>4} {'FAILS':>7} {'RATE':>6}  STATUS"]
    for model, m in sorted(d["models"].items()):
        ok = m["events"].get(GOOD, 0)
        bad = sum(m["events"].get(e, 0) for e in BAD_EVENTS)
        rate = f"{(ok/(ok+bad)*100):.0f}%" if (ok + bad) else "-"
        state = "BENCHED" if model in d["benched"] else "active"
        lines.append(f"{model:<45} {ok:>4} {bad:>7} {rate:>6}  {state}")
    if d["benched"]:
        lines.append("")
        lines.append("Benched models (excluded from fallback): " + ", ".join(d["benched"]))
    return "\n".join(lines)
