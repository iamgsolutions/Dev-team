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
    assert "contrato" in skillpack.load_for_role("architect").lower()
    assert "VEREDICTO" in skillpack.load_for_role("review")
    assert "reproduc" in skillpack.load_for_role("qa").lower()


def test_unknown_role_gets_empty_pack():
    assert skillpack.load_for_role("astronaut") == ""


def test_instruction_includes_knowledge_block():
    instr = full_instruction()
    instr.skills_pack = "## SKILL X\ncontenido"
    text = instr.build()
    assert "== CONOCIMIENTO DEL ROL" in text
    assert text.index("CONOCIMIENTO") < text.index("CIERRE")  # before CIERRE


def test_instruction_without_pack_still_valid():
    text = full_instruction().build()
    assert "CONOCIMIENTO" not in text
    assert "== CIERRE" in text
