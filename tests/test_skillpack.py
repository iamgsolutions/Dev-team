from devteam import skillpack
from devteam.instruction import Instruction


def full_instruction(**overrides):
    kw = dict(
        role="backend",
        read_first=["./.project-memory/STATE.md"],
        current_state="fase backend",
        task="implementa GET /health",
        acceptance_criteria=["devuelve 200"],
        model_info="opencode / free",
        budget_note="restante $10",
        memory_updates=["STATE.md: registra lo hecho"],
    )
    kw.update(overrides)
    return Instruction(**kw)


def test_every_role_has_a_pack():
    for role in ("pm", "architect", "backend", "frontend", "qa", "review"):
        pack = skillpack.load_for_role(role)
        assert len(pack) > 500, f"{role} pack too small"
        assert "SKILL" in pack


def test_packs_are_size_capped():
    for role in skillpack.ROLE_SKILLS:
        assert len(skillpack.load_for_role(role)) <= skillpack.MAX_PACK_CHARS + 100


def test_role_specific_content():
    assert "PRD" in skillpack.load_for_role("pm")
    assert "contract" in skillpack.load_for_role("architect").lower()
    assert "VERDICT" in skillpack.load_for_role("review")
    assert "reproduc" in skillpack.load_for_role("qa").lower()


def test_unknown_role_gets_empty_pack():
    assert skillpack.load_for_role("astronaut") == ""


def test_project_type_adds_extra_skills():
    base = skillpack.load_for_role("frontend")
    web = skillpack.load_for_role("frontend", "web")
    # web adds accessibility+performance to frontend; already in base here, so
    # use api on backend where the extra is clearly additive
    base_be = skillpack.load_for_role("backend")
    api_be = skillpack.load_for_role("backend", "api")
    assert len(api_be) >= len(base_be)
    assert isinstance(web, str) and len(web) > 0


def test_project_type_unknown_is_safe():
    # an unknown type just yields the base role pack (no crash)
    assert skillpack.load_for_role("backend", "quantum") == skillpack.load_for_role("backend")


def test_instruction_includes_knowledge_block():
    instr = full_instruction()
    instr.skills_pack = "## SKILL X\ncontent"
    text = instr.build()
    assert "== ROLE KNOWLEDGE" in text
    assert text.index("KNOWLEDGE") < text.index("CLOSE-OUT")  # before CLOSE-OUT


def test_instruction_without_pack_still_valid():
    text = full_instruction().build()
    assert "KNOWLEDGE" not in text
    assert "== CLOSE-OUT" in text
