"""Project memory files + handoff verification (S4c, enforces ADR-015).

STATE.md / NOTES.md live in <project>/.project-memory/ and are the relay baton
between stateless agents. verify_handoff() checks that an invocation actually
updated them - if not, the task is NOT complete (hard rule).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from . import config

STATE_MD = "STATE.md"
NOTES_MD = "NOTES.md"


def memory_dir(project_path: Path) -> Path:
    return project_path / config.PROJECT_MEMORY_DIR


def init_memory(project_path: Path, project_name: str, brief_summary: str) -> None:
    d = memory_dir(project_path)
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (d / STATE_MD).write_text(
        f"# STATE — {project_name}\n\n"
        f"Created: {ts}\n\n"
        f"## Project summary\n{brief_summary}\n\n"
        f"## Current state\nProject just created. Nothing built yet.\n\n"
        f"## Done\n(nothing)\n\n## Pending\nThe whole pipeline.\n",
        encoding="utf-8",
    )
    (d / NOTES_MD).write_text(
        f"# NOTES — {project_name}\n\n"
        "Warnings and decisions from one agent to the next. The most recent agent writes AT THE TOP.\n\n"
        f"## {ts} — system\nProject initialized.\n",
        encoding="utf-8",
    )


def _sig(f: Path) -> tuple[float, int, str]:
    """(mtime, size, sha1) signature of a memory file; (0, -1, '') if missing."""
    if not f.exists():
        return (0.0, -1, "")
    data = f.read_bytes()
    return (f.stat().st_mtime, len(data), hashlib.sha1(data).hexdigest())


def snapshot_memory(project_path: Path) -> dict[str, tuple[float, int, str]]:
    """Signature of memory files BEFORE an invocation (mtime + size + content hash)."""
    d = memory_dir(project_path)
    return {name: _sig(d / name) for name in (STATE_MD, NOTES_MD)}


def verify_handoff(project_path: Path, before: dict[str, tuple[float, int, str]]) -> bool:
    """True if an agent made a REAL change to memory: a content hash or size
    differs. A bare mtime touch (re-saving identical content) does NOT count -
    the handoff must record actual work, not just touch the file."""
    after = snapshot_memory(project_path)
    for name, sig in after.items():
        b = before.get(name, (0.0, -1, ""))
        if sig[1] != b[1] or sig[2] != b[2]:   # size or content hash changed
            return True
    return False


def read_state(project_path: Path) -> str:
    f = memory_dir(project_path) / STATE_MD
    return f.read_text(encoding="utf-8") if f.exists() else ""


def read_notes(project_path: Path) -> str:
    f = memory_dir(project_path) / NOTES_MD
    return f.read_text(encoding="utf-8") if f.exists() else ""


def memory_paths_for_instruction(project_path: Path) -> list[str]:
    """Relative paths an agent must read first (ORIENTATION block)."""
    base = f"./{config.PROJECT_MEMORY_DIR}"
    return [f"{base}/{STATE_MD}", f"{base}/{NOTES_MD}"]


def memory_update_spec() -> list[str]:
    """Standard CLOSE-OUT block contents for any task."""
    base = f"./{config.PROJECT_MEMORY_DIR}"
    return [
        f"{base}/{STATE_MD}: update 'Done'/'Pending' with your work",
        f"{base}/{NOTES_MD}: add decisions, doubts and warnings for the next agent at the top",
    ]
