from devteam import config, presets


def test_builtin_presets_exist_for_each_core_role():
    roles = {p.role for p in presets.all_presets()}
    for r in ("architect", "backend", "frontend", "review", "qa", "deploy"):
        assert r in roles, r


def test_get_and_by_role():
    p = presets.get("auditor-gemini")
    assert p and p.brain == config.BRAIN_GEMINI and p.role == "review"
    assert {x.name for x in presets.by_role("architect")} == {"architect-claude", "architect-codex"}
    assert presets.get("nope") is None


def test_preset_loads_role_skills():
    p = presets.get("backend-free")
    pack = p.skills()
    assert "SKILL" in pack and len(pack) > 500   # carries the backend craft


def test_presets_declare_models_and_mcps():
    # swapping the model is the whole point: same role, different model
    assert presets.get("backend-free").model in config.OPENCODE_FREE_MODELS
    assert presets.get("backend-deepseek").model in config.OPENCODE_CHEAP_MODELS
    assert "filesystem" in presets.get("backend-free").mcps


def test_format_report_lists_all():
    rep = presets.format_report()
    for p in presets.all_presets():
        assert p.name in rep
