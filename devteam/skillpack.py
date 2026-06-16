"""Skill packs - pre-installed role knowledge injected into every instruction.

Each role gets its OWN craft file plus relevant cross-cutting files (security,
testing, language). The pack rides into the instruction as an extra knowledge
block, so every agent - even a free model - works with senior-level checklists,
patterns and anti-patterns (Fable mentorship, 2026-06-12).

Size-capped: knowledge must sharpen the agent, not drown the task.
"""
from __future__ import annotations

from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"
MAX_PACK_CHARS = 9000   # keep instructions lean; files are written compact

# role -> ordered skill files (first = most important, kept under truncation)
# audit fixes: qa now gets `testing`; frontend gets `security` (XSS/CSRF/auth);
# `deploy` role added (was an orphan phase). New craft skills wired in.
ROLE_SKILLS: dict[str, list[str]] = {
    "pm": ["pm", "product-quality", "data-privacy"],
    "architect": ["architect", "security", "api-design", "database", "performance"],
    "backend": ["backend", "python", "testing", "security", "database", "observability"],
    "frontend": ["frontend", "typescript", "testing", "security", "accessibility", "performance"],
    "qa": ["qa", "testing", "debugging", "api-design"],
    "review": ["review", "security", "code-style"],
    "audit": ["review", "security", "code-style"],
    "deploy": ["devops", "observability", "security"],
}

# Second dimension: per project TYPE, extra skills layered on the role pack so
# the injected knowledge is always pertinent to what's being built (Auditor 4's
# top architectural rec). The role pack is the base; these are additive.
PROJECT_TYPE_SKILLS: dict[str, dict[str, list[str]]] = {
    "web":    {"frontend": ["accessibility", "performance"], "architect": ["performance"]},
    "api":    {"backend": ["api-design", "performance", "observability"],
               "architect": ["api-design", "performance"]},
    "mobile": {"frontend": ["performance"], "architect": ["performance"]},
}


def load_for_role(role: str, project_type: str | None = None) -> str:
    """Compose the knowledge pack for a role (+ project-type extras + lessons).

    Appends the role's accumulated LESSONS (skills/<role>-lessons.md) when
    present - the learning loop: failures distilled by the director become
    permanent craft for that role (closes reflective <-> skills)."""
    role = role.lower()
    names = list(ROLE_SKILLS.get(role, []))
    # project-type extras (deduped, preserving order)
    if project_type:
        for extra in PROJECT_TYPE_SKILLS.get(project_type.lower(), {}).get(role, []):
            if extra not in names:
                names.append(extra)
    lessons = SKILLS_DIR / f"{role}-lessons.md"
    if lessons.exists():
        names.append(f"{role}-lessons")
    parts: list[str] = []
    total = 0
    for name in names:
        f = SKILLS_DIR / f"{name}.md"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="replace").strip()
        if total + len(text) > MAX_PACK_CHARS:
            remaining = MAX_PACK_CHARS - total
            if remaining < 400:
                break
            text = text[:remaining] + "\n[...recortado por tamaño...]"
        parts.append(text)
        total += len(text)
    return "\n\n---\n\n".join(parts)


def available_skills() -> list[str]:
    return sorted(p.stem for p in SKILLS_DIR.glob("*.md"))


def append_lesson(role: str, lesson: str) -> Path:
    """Add a distilled lesson to a role's lessons file (learning loop).

    The director calls this when a failure pattern repeats (from qa-report /
    audit). It becomes permanent craft injected into that role's pack from then
    on. Kept compact (lessons file is capped at load time by MAX_PACK_CHARS)."""
    from datetime import datetime, timezone
    role = role.lower()
    f = SKILLS_DIR / f"{role}-lessons.md"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not f.exists():
        header = (f"# LECCIONES APRENDIDAS — rol {role}\n\n"
                  "Patrones de fallo destilados de proyectos reales. Evítalos.\n")
        f.write_text(header, encoding="utf-8")
    with f.open("a", encoding="utf-8") as fh:
        fh.write(f"\n- ({stamp}) {lesson.strip()}")
    return f
