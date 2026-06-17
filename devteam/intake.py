"""Project intake (S1) - create a project from a markdown brief.

Validates the brief has the minimum template sections; missing critical info
sends the project to 'clarification' with grouped questions (spec R1/R12)
instead of building on assumptions.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from . import config, worktree
from .memory import init_memory
from .state import Project, registry_add

# Universal team rules, written into every project repo. The three coding
# CLIs (claude/codex/opencode) auto-read AGENTS.md from the working directory,
# so these rules apply on every invocation - belt AND suspenders with the
# engine's 4-block instructions. These rules are self-contained below.
AGENTS_MD = """\
# AGENTS.md - Team rules (mandatory for EVERY agent in this repo)

You work inside a 24/7 development team, run by the `devteam`
engine. These rules ALWAYS apply, in addition to the instruction you receive:

1. You are STATELESS. Read `.project-memory/STATE.md` and `.project-memory/NOTES.md`
   before acting. The brief is in `BRIEF.md`; the contracts in `docs/`.
2. BEFORE FINISHING update `.project-memory/STATE.md` (what you did, what is
   left) and `.project-memory/NOTES.md` (decisions, doubts, warnings for the
   next agent). Without this your task is NOT complete.
3. Stick to the assigned task. Do not "improve" things that were not asked for.
4. NEVER write secrets (keys, tokens) in code, commits or logs.
   Use environment variables (.env is in .gitignore).
5. Your output must compile and pass lint and tests. Write tests for what you
   produce.
6. Code, identifiers and commits in ENGLISH. Documentation in ENGLISH.
7. Follow the decisions in `docs/architecture.md` and `docs/api-contract.md`
   EXACTLY. If you think there is an error, note it in NOTES.md - do not
   change it on your own.
8. Work only in this directory. Do not touch other projects or the system.
9. Conventional commits: feat:/fix:/test:/docs:/chore:.
10. HONESTY: if something does not work or is not possible, say it clearly in
    NOTES.md. Do not fake success.
"""

# critical sections: without these we go to clarification. Bilingual patterns -
# the brief may arrive in Spanish (legacy templates) or English (the team's
# working language), so each regex matches the headers in either language.
CRITICAL_PATTERNS = {
    "objetivo": r"##\s*2?\.?\s*(objetivo|objective)|qué problema|what problem",
    "funcionalidades": r"##\s*3?\.?\s*(funcionalidades|features)",
    "criterios": r"criterios de éxito|success criteria|## 10",
}


def validate_brief(brief_text: str) -> list[str]:
    """Return list of missing-critical-section questions (empty = OK)."""
    questions = []
    low = brief_text.lower()
    if not re.search(CRITICAL_PATTERNS["objetivo"], low, re.IGNORECASE):
        questions.append("What is the project's objective and what problem does it solve?")
    if not re.search(CRITICAL_PATTERNS["funcionalidades"], low, re.IGNORECASE):
        questions.append("What features must it have (at least the essential ones)?")
    if not re.search(CRITICAL_PATTERNS["criterios"], low, re.IGNORECASE):
        questions.append("What are the verifiable success criteria ('done when...')?")
    return questions


def extract_name(brief_text: str, fallback: str = "project") -> str:
    # Bilingual: match the Spanish ("Nombre") or English ("Name") project field,
    # and the Spanish or English brief title.
    m = re.search(r"\*\*(?:Nombre|Name).*?:\*\*\s*(.+)", brief_text)
    if m:
        return worktree.slugify(m.group(1).strip())
    m = re.search(r"#\s*(?:Brief de Proyecto|Project Brief)\s*[—-]\s*(.+)", brief_text)
    if m:
        return worktree.slugify(m.group(1).strip())
    return fallback


def extract_budget_cap(brief_text: str) -> float:
    # Bilingual: "Tope de gasto" (ES) or "Spending cap"/"Budget cap" (EN).
    m = re.search(r"(?:Tope de gasto|Spending cap|Budget cap).*?\$?(\d+(?:[.,]\d+)?)", brief_text)
    if m:
        return float(m.group(1).replace(",", "."))
    return config.DEFAULT_BUDGET_CAP_USD


def detect_project_type(text: str) -> str:
    """Infer web | api | mobile from the brief (drives project-type skills).

    Bilingual keywords so it works whether the brief is in Spanish or English."""
    low = text.lower()
    if re.search(r"\bapp m[oó]vil|mobile app|react native|expo|android|ios|aplicaci[oó]n m[oó]vil|móvil\b", low):
        return "mobile"
    if re.search(r"\b(api|backend) (rest|pura|sola|only|standalone)|solo (api|backend)|(api|backend) only|microservicio|microservice\b", low):
        return "api"
    return "web"


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

    # AGENTS.md: claude/codex/opencode read this automatically from the cwd -
    # it reinforces the universal team rules on EVERY invocation, in addition
    # to the 4-block instruction the engine injects.
    (project_path / "AGENTS.md").write_text(AGENTS_MD, encoding="utf-8")

    # STANDARDS.md: the team's single way of building (structure, code rules,
    # security, tests). The Architect follows it instead of inventing.
    from .standards import write_standards
    write_standards(project_path)

    first_line = next((ln.strip("# ").strip() for ln in brief_text.splitlines() if ln.strip()), name)
    init_memory(project_path, name, first_line)

    questions = validate_brief(brief_text)
    project = Project(
        name=name, path=project_path, budget_cap_usd=cap, discord_channel=discord_channel,
        project_type=detect_project_type(brief_text),
    )
    project.save()
    if questions:
        project.transition("clarification", "incomplete brief: questions for the human")
    else:
        project.transition("pm", "valid brief: PM starts")
    registry_add(project)
    worktree.commit_all(project_path, "chore: project intake (brief + memory)")
    return project, questions
