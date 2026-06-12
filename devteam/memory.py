"""Project memory files + handoff verification (S4c, enforces ADR-015).

STATE.md / NOTES.md live in <project>/.project-memory/ and are the relay baton
between stateless agents. verify_handoff() checks that an invocation actually
updated them - if not, the task is NOT complete (hard rule).
"""
from __future__ import annotations

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
        f"Creado: {ts}\n\n"
        f"## Resumen del proyecto\n{brief_summary}\n\n"
        f"## Estado actual\nProyecto recién creado. Nada construido aún.\n\n"
        f"## Hecho\n(nada)\n\n## Pendiente\nTodo el pipeline.\n",
        encoding="utf-8",
    )
    (d / NOTES_MD).write_text(
        f"# NOTES — {project_name}\n\n"
        "Avisos y decisiones de un agente al siguiente. El agente más reciente escribe ARRIBA.\n\n"
        f"## {ts} — sistema\nProyecto inicializado.\n",
        encoding="utf-8",
    )


def snapshot_mtimes(project_path: Path) -> dict[str, float]:
    """Take mtimes of memory files before an invocation."""
    d = memory_dir(project_path)
    out: dict[str, float] = {}
    for name in (STATE_MD, NOTES_MD):
        f = d / name
        out[name] = f.stat().st_mtime if f.exists() else 0.0
    return out


def verify_handoff(project_path: Path, before: dict[str, float]) -> bool:
    """True if at least one memory file was modified since the snapshot."""
    after = snapshot_mtimes(project_path)
    return any(after[k] > before.get(k, 0.0) for k in after)


def read_state(project_path: Path) -> str:
    f = memory_dir(project_path) / STATE_MD
    return f.read_text(encoding="utf-8") if f.exists() else ""


def read_notes(project_path: Path) -> str:
    f = memory_dir(project_path) / NOTES_MD
    return f.read_text(encoding="utf-8") if f.exists() else ""


def memory_paths_for_instruction(project_path: Path) -> list[str]:
    """Relative paths an agent must read first (ORIENTACION block)."""
    base = f"./{config.PROJECT_MEMORY_DIR}"
    return [f"{base}/{STATE_MD}", f"{base}/{NOTES_MD}"]


def memory_update_spec() -> list[str]:
    """Standard CIERRE block contents for any task."""
    base = f"./{config.PROJECT_MEMORY_DIR}"
    return [
        f"{base}/{STATE_MD}: actualiza 'Hecho'/'Pendiente' con tu trabajo",
        f"{base}/{NOTES_MD}: añade arriba decisiones, dudas y avisos al siguiente agente",
    ]
