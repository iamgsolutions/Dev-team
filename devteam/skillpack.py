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
ROLE_SKILLS: dict[str, list[str]] = {
    "pm": ["pm", "product-quality"],
    "architect": ["architect", "security", "api-design"],
    "backend": ["backend", "python", "testing", "security"],
    "frontend": ["frontend", "typescript", "testing"],
    "qa": ["qa", "debugging", "api-design"],
    "review": ["review", "security"],
    "audit": ["review", "security"],
}


def load_for_role(role: str) -> str:
    """Compose the knowledge pack for a role. Empty string if none defined."""
    names = ROLE_SKILLS.get(role.lower(), [])
    parts: list[str] = []
    total = 0
    for name in names:
        f = SKILLS_DIR / f"{name}.md"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8").strip()
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
