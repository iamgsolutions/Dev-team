"""Brain router (S3) - dynamic, cost-aware routing (ADR-012/013 + R10 refinement).

Default rules (07-technical-decisions):
- design roles (pm, architect)            -> claude (premium designs, few tokens)
- execution roles (backend, frontend, qa) -> opencode free -> cheap escalation
- audit/review                            -> a brain DIFFERENT from the author
- critical tasks                          -> escalate to claude regardless of role
- budget nearly exhausted                 -> degrade to free models only

Every decision returns a justification string and is recorded by the caller
into reflective memory (S14) to improve routing over time.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config


DESIGN_ROLES = {"pm", "architect"}
EXEC_ROLES = {"backend", "frontend", "qa"}
AUDIT_ROLES = {"review", "audit"}


@dataclass
class Route:
    brain: str                 # claude | codex | opencode
    model: str | None          # explicit model for opencode; None = CLI default
    justification: str


def route(
    role: str,
    critical: bool = False,
    budget_remaining_usd: float = 999.0,
    author_brain: str | None = None,
    free_tier_exhausted: bool = False,
) -> Route:
    role = role.lower()

    # Audit: must differ from author (diversity principle).
    if role in AUDIT_ROLES:
        if author_brain == config.BRAIN_CODEX:
            return Route(config.BRAIN_OPENCODE, _opencode_model(free_tier_exhausted),
                         "audit: diverse brain (author was codex)")
        if author_brain == config.BRAIN_CLAUDE:
            return Route(config.BRAIN_CODEX, None, "audit: diverse brain (author was claude)")
        # author was opencode (or unknown): prefer codex if affordable, else another oc model
        if budget_remaining_usd > 1.0:
            return Route(config.BRAIN_CODEX, None, "audit: diverse brain (author was opencode)")
        return Route(config.BRAIN_OPENCODE, _opencode_model(free_tier_exhausted),
                     "audit: diverse-ish (budget too low for premium)")

    # Critical work goes to the premium designer brain (human's explicit rule:
    # "habrá veces que Hermes decida que Claude desarrolle esa parte").
    if critical:
        if budget_remaining_usd > 2.0:
            return Route(config.BRAIN_CLAUDE, None, "critical task -> premium brain")
        return Route(config.BRAIN_OPENCODE, _opencode_model(free_tier_exhausted=True),
                     "critical but budget nearly exhausted -> best cheap model")

    if role in DESIGN_ROLES:
        if budget_remaining_usd > 2.0:
            return Route(config.BRAIN_CLAUDE, None, f"{role}: design role -> premium brain")
        return Route(config.BRAIN_OPENCODE, _opencode_model(free_tier_exhausted=True),
                     f"{role}: design role but budget low -> cheap-strong model")

    # Execution (default): free first, escalate to cheap when free is exhausted.
    return Route(config.BRAIN_OPENCODE, _opencode_model(free_tier_exhausted),
                 f"{role}: execution role -> opencode ({'cheap' if free_tier_exhausted else 'free'} tier)")


def _opencode_model(free_tier_exhausted: bool) -> str:
    if free_tier_exhausted:
        return config.OPENCODE_CHEAP_MODELS[0]
    return config.OPENCODE_FREE_MODELS[0]


def fallback_chain(current_model: str | None) -> list[str]:
    """Models to try (in order) when the current one fails / rate-limits."""
    chain = [m for m in config.OPENCODE_FREE_MODELS if m != current_model]
    chain += [m for m in config.OPENCODE_CHEAP_MODELS if m != current_model]
    return chain
