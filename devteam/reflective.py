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
              "gate_failed", "audit_rejected")


def _path() -> Path:
    return config.DATA_DIR / "scorecard.json"


def _load() -> dict:
    p = _path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"models": {}, "benched": []}


def _save(d: dict) -> None:
    config.ensure_dirs()
    _path().write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


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


def format_report() -> str:
    d = _load()
    if not d["models"]:
        return "scorecard vacío (aún sin tareas registradas)"
    lines = [f"{'MODELO':<45} {'OK':>4} {'FALLOS':>7} {'TASA':>6}  ESTADO"]
    for model, m in sorted(d["models"].items()):
        ok = m["events"].get(GOOD, 0)
        bad = sum(m["events"].get(e, 0) for e in BAD_EVENTS)
        rate = f"{(ok/(ok+bad)*100):.0f}%" if (ok + bad) else "-"
        state = "BANQUILLO" if model in d["benched"] else "activo"
        lines.append(f"{model:<45} {ok:>4} {bad:>7} {rate:>6}  {state}")
    if d["benched"]:
        lines.append("")
        lines.append("Modelos en el banquillo (excluidos del fallback): " + ", ".join(d["benched"]))
    return "\n".join(lines)
