"""Engine event log - structured, append-only observability for the system.

Every significant thing the engine does (task routed, gate result, audit
verdict, phase transition, budget charge, human intervention, pause/escalation)
is appended as one JSON line to data/events.jsonl. This is the flight recorder:
when something goes wrong, you read what actually happened instead of guessing.

Cheap (append-only, no LLM), secret-redacted, and never raises (logging must
not break the pipeline). Rotates at a size cap to stay bounded.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import config

MAX_BYTES = 5_000_000   # ~5 MB then rotate to events.jsonl.1


def _path() -> Path:
    return config.DATA_DIR / "events.jsonl"


def record(kind: str, project: str = "", **fields) -> None:
    """Append one event. kind = short verb (routed/gate/audit/phase/charge/...)."""
    try:
        from .storage import redact
        config.ensure_dirs()
        ev = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "kind": kind,
            "project": project,
        }
        for k, v in fields.items():
            ev[k] = redact(v) if isinstance(v, str) else v
        p = _path()
        # rotate if too big
        if p.exists() and p.stat().st_size > MAX_BYTES:
            try:
                p.replace(p.with_suffix(".jsonl.1"))
            except OSError:
                pass
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 - observability must never break the engine
        pass


def read(n: int = 50, project: str | None = None) -> list[dict]:
    """Return the last n events (optionally filtered by project), newest last."""
    p = _path()
    if not p.exists():
        return []
    out: list[dict] = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if project and ev.get("project") != project:
                continue
            out.append(ev)
    except OSError:
        return []
    return out[-n:]


def format_tail(n: int = 50, project: str | None = None) -> str:
    evs = read(n, project)
    if not evs:
        return "(sin eventos registrados)"
    lines = []
    for e in evs:
        extra = " ".join(f"{k}={v}" for k, v in e.items()
                         if k not in ("ts", "kind", "project"))
        proj = f"[{e['project']}] " if e.get("project") else ""
        lines.append(f"{e['ts']}  {e['kind']:<10} {proj}{extra}")
    return "\n".join(lines)
