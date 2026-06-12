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

BRAIN_DEFER = "defer"  # premium needed but resting -> task waits for the next batch window


@dataclass
class Route:
    brain: str                 # claude | codex | opencode | defer
    model: str | None          # explicit model for opencode; None = CLI default
    justification: str


def route(
    role: str,
    critical: bool = False,
    budget_remaining_usd: float = 999.0,
    author_brain: str | None = None,
    free_tier_exhausted: bool = False,
    claude_available: bool = True,
    codex_available: bool = True,
    gemini_available: bool = True,
) -> Route:
    """Pick a brain. Subscription guardian (premium availability) feeds in
    here: premium work without an available premium brain DEFERS instead of
    silently degrading (human's batching policy - quality over speed)."""
    role = role.lower()

    # Audit: must differ from author (diversity principle). Gemini is the
    # PREFERRED auditor: diverse, huge context, and saves the codex ration.
    if role in AUDIT_ROLES:
        candidates = []
        if gemini_available and author_brain != config.BRAIN_GEMINI:
            candidates.append((config.BRAIN_GEMINI, "audit: gemini (diverse, big context)"))
        if codex_available and author_brain != config.BRAIN_CODEX:
            candidates.append((config.BRAIN_CODEX, "audit: codex (diverse)"))
        for brain, why in candidates:
            if budget_remaining_usd > 1.0:
                return Route(brain, None, f"{why}; author was {author_brain or 'unknown'}")
        return Route(config.BRAIN_OPENCODE, _opencode_model(free_tier_exhausted),
                     f"audit: cheap diverse model (premium resting or budget low; author {author_brain or 'unknown'})")

    # Critical / design work wants a premium brain. Escalation chain:
    # claude -> codex -> gemini -> DEFER (the daemon retries later).
    if critical or role in DESIGN_ROLES:
        if budget_remaining_usd <= 2.0:
            return Route(config.BRAIN_OPENCODE, _opencode_model(free_tier_exhausted=True),
                         f"{role}: premium-grade task but project budget nearly exhausted -> best cheap model")
        if claude_available:
            return Route(config.BRAIN_CLAUDE, None, f"{role}: premium-grade task -> claude")
        if codex_available:
            return Route(config.BRAIN_CODEX, None,
                         f"{role}: claude resting -> codex (second premium brain)")
        if gemini_available:
            return Route(config.BRAIN_GEMINI, None,
                         f"{role}: claude+codex resting -> gemini (third premium brain)")
        return Route(BRAIN_DEFER, None,
                     f"{role}: premium-grade task, all premium brains resting -> defer to next batch")

    # Execution (default): free first, escalate to cheap when free is exhausted.
    return Route(config.BRAIN_OPENCODE, _opencode_model(free_tier_exhausted),
                 f"{role}: execution role -> opencode ({'cheap' if free_tier_exhausted else 'free'} tier)")


def _opencode_model(free_tier_exhausted: bool) -> str:
    if free_tier_exhausted:
        return config.OPENCODE_CHEAP_MODELS[0]
    return config.OPENCODE_FREE_MODELS[0]


def fallback_chain(current_model: str | None) -> list[str]:
    """Models to try (in order) when the current one fails / rate-limits.
    Benched models (scorecard: too many failures) are excluded - a model the
    director sent to the bench never re-enters silently."""
    from .reflective import benched_models
    benched = set(benched_models())
    chain = [m for m in config.OPENCODE_FREE_MODELS if m != current_model and m not in benched]
    chain += [m for m in config.OPENCODE_CHEAP_MODELS if m != current_model and m not in benched]
    return chain
