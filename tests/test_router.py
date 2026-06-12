from devteam import config
from devteam.router import fallback_chain, route


def test_design_roles_get_premium_brain():
    assert route("pm").brain == config.BRAIN_CLAUDE
    assert route("architect").brain == config.BRAIN_CLAUDE


def test_execution_roles_get_opencode_free_first():
    r = route("backend")
    assert r.brain == config.BRAIN_OPENCODE
    assert r.model in config.OPENCODE_FREE_MODELS


def test_execution_escalates_to_cheap_when_free_exhausted():
    r = route("frontend", free_tier_exhausted=True)
    assert r.model in config.OPENCODE_CHEAP_MODELS


def test_critical_overrides_role():
    # human's rule: complex/critical work goes to claude even if executor role
    r = route("backend", critical=True)
    assert r.brain == config.BRAIN_CLAUDE


def test_low_budget_degrades_design_to_cheap():
    r = route("architect", budget_remaining_usd=0.5)
    assert r.brain == config.BRAIN_OPENCODE


def test_audit_never_uses_author_brain():
    for author in (config.BRAIN_CLAUDE, config.BRAIN_CODEX, config.BRAIN_OPENCODE):
        r = route("review", author_brain=author)
        assert r.brain != author


def test_fallback_chain_excludes_current_and_ends_in_cheap():
    current = config.OPENCODE_FREE_MODELS[0]
    chain = fallback_chain(current)
    assert current not in chain
    assert chain[-1] in config.OPENCODE_CHEAP_MODELS
