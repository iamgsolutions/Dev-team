"""Adopt an EXISTING project into the devteam system (brownfield onboarding).

Unlike intake (greenfield: brief -> empty repo), adopt takes a repo that
already has code/roadmap and wires the system around it WITHOUT touching
existing work:
- .project-memory/ created with STATE.md seeded from the repo's own docs
  (README/ROADMAP) so agents orient from what already exists
- AGENTS.md / docs/STANDARDS.md written ONLY if absent
- registered in the engine registry; initial state defaults to "qa"
  (director's rule for adopted projects: AUDIT FIRST, then bounce work
  back to backend/frontend as QA finds gaps)
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import config
from .intake import AGENTS_MD
from .standards import write_standards
from .state import Project, registry_add

ROADMAP_NAMES = ("ROADMAP.md", "roadmap.md", "docs/ROADMAP.md", "docs/roadmap.md",
                 "README.md", "readme.md")


def _seed_summary(path: Path, max_chars: int = 1500) -> str:
    """First meaningful chunk of the project's own docs, for STATE.md."""
    for name in ROADMAP_NAMES:
        f = path / name
        if f.exists():
            text = f.read_text(encoding="utf-8", errors="ignore").strip()
            return f"(de {name})\n" + text[:max_chars]
    return "(el repo no trae README/ROADMAP legible - el director debe pedir contexto)"


def adopt_project(
    path: Path,
    name: str | None = None,
    cap: float | None = None,
    discord_channel: str = "",
    initial_state: str = "qa",
) -> Project:
    path = Path(path)
    if not (path / ".git").exists():
        raise ValueError(f"{path} is not a git repository (clone it first)")
    name = name or path.name.lower()

    mem = path / config.PROJECT_MEMORY_DIR
    if (mem / "project.json").exists():
        raise FileExistsError(f"project already adopted: {mem}")

    mem.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    (mem / "STATE.md").write_text(
        f"# STATE — {name} (proyecto ADOPTADO)\n\n"
        f"Adoptado por el sistema: {ts}\n\n"
        f"## Resumen del proyecto (según su propia documentación)\n{_seed_summary(path)}\n\n"
        f"## Estado actual\nProyecto existente recién adoptado. PRIMERA MISIÓN: auditoría QA\n"
        f"completa (qué funciona de verdad, qué está a medias, qué falta vs roadmap).\n\n"
        f"## Hecho\n(heredado del repo - ver git log)\n\n"
        f"## Pendiente\nAuditoría inicial → backlog real → completar el roadmap.\n",
        encoding="utf-8",
    )
    (mem / "NOTES.md").write_text(
        f"# NOTES — {name}\n\n"
        "Avisos y decisiones de un agente al siguiente. El más reciente escribe ARRIBA.\n\n"
        f"## {ts} — sistema\nProyecto EXISTENTE adoptado. Respetar el código y las decisiones\n"
        "previas del repo; ante contradicción entre el roadmap del repo y STANDARDS.md,\n"
        "anotarla aquí y que decida el director.\n",
        encoding="utf-8",
    )

    # runtime state must not travel in shared repos (local paths, cursors)
    gi = path / ".gitignore"
    marker = ".project-memory/project.json"
    if not gi.exists() or marker not in gi.read_text(encoding="utf-8", errors="ignore"):
        with gi.open("a", encoding="utf-8") as f:
            f.write(f"\n# devteam runtime state (local)\n{marker}\n")

    if not (path / "AGENTS.md").exists():
        (path / "AGENTS.md").write_text(AGENTS_MD, encoding="utf-8")
    if not (path / "docs" / "STANDARDS.md").exists():
        write_standards(path)

    project = Project(
        name=name, path=path,
        budget_cap_usd=cap if cap is not None else config.DEFAULT_BUDGET_CAP_USD,
        discord_channel=discord_channel,
    )
    project.state = initial_state if initial_state in config.STATES else "qa"
    project.history.append({"event": "adopted", "note": f"estado inicial {project.state}"})
    project.save()
    registry_add(project)
    return project
