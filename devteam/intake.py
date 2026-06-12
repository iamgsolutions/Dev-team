"""Project intake (S1) - create a project from a markdown brief.

Validates the brief has the minimum sections of the template
(mg-kb/templates/project-brief-template.md); missing critical info sends the
project to 'clarification' with grouped questions (spec R1/R12) instead of
building on assumptions.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from . import config, worktree
from .memory import init_memory
from .state import Project, registry_add

# critical sections: without these we go to clarification
CRITICAL_PATTERNS = {
    "objetivo": r"##\s*2?\.?\s*Objetivo|qué problema",
    "funcionalidades": r"##\s*3?\.?\s*Funcionalidades",
    "criterios": r"criterios de éxito|## 10",
}


def validate_brief(brief_text: str) -> list[str]:
    """Return list of missing-critical-section questions (empty = OK)."""
    questions = []
    low = brief_text.lower()
    if not re.search(CRITICAL_PATTERNS["objetivo"], low, re.IGNORECASE):
        questions.append("¿Cuál es el objetivo del proyecto y qué problema resuelve?")
    if not re.search(CRITICAL_PATTERNS["funcionalidades"], low, re.IGNORECASE):
        questions.append("¿Qué funcionalidades debe tener (al menos las imprescindibles)?")
    if not re.search(CRITICAL_PATTERNS["criterios"], low, re.IGNORECASE):
        questions.append("¿Cuáles son los criterios de éxito verificables ('terminado cuando...')?")
    return questions


def extract_name(brief_text: str, fallback: str = "project") -> str:
    m = re.search(r"\*\*Nombre.*?:\*\*\s*(.+)", brief_text)
    if m:
        return worktree.slugify(m.group(1).strip())
    m = re.search(r"#\s*Brief de Proyecto\s*[—-]\s*(.+)", brief_text)
    if m:
        return worktree.slugify(m.group(1).strip())
    return fallback


def extract_budget_cap(brief_text: str) -> float:
    m = re.search(r"Tope de gasto.*?\$?(\d+(?:[.,]\d+)?)", brief_text)
    if m:
        return float(m.group(1).replace(",", "."))
    return config.DEFAULT_BUDGET_CAP_USD


def new_project(
    brief_path: Path,
    name: str | None = None,
    cap: float | None = None,
    discord_channel: str = "",
) -> tuple[Project, list[str]]:
    """Create the project skeleton. Returns (project, clarification_questions).

    If questions is non-empty the project starts in 'clarification' state and
    the caller must relay the questions to the human (grouped, per spec).
    """
    brief_text = brief_path.read_text(encoding="utf-8")
    name = name or extract_name(brief_text, fallback=brief_path.stem)
    cap = cap if cap is not None else extract_budget_cap(brief_text)

    config.ensure_dirs()
    project_path = config.PROJECTS_ROOT / name
    if (project_path / config.PROJECT_MEMORY_DIR / "project.json").exists():
        raise FileExistsError(f"project {name!r} already exists at {project_path}")

    project_path.mkdir(parents=True, exist_ok=True)
    worktree.ensure_repo(project_path)
    shutil.copy(brief_path, project_path / "BRIEF.md")

    first_line = next((ln.strip("# ").strip() for ln in brief_text.splitlines() if ln.strip()), name)
    init_memory(project_path, name, first_line)

    questions = validate_brief(brief_text)
    project = Project(
        name=name, path=project_path, budget_cap_usd=cap, discord_channel=discord_channel,
    )
    project.save()
    if questions:
        project.transition("clarification", "brief incompleto: preguntas al humano")
    else:
        project.transition("pm", "brief válido: arranca PM")
    registry_add(project)
    worktree.commit_all(project_path, "chore: project intake (brief + memory)")
    return project, questions
