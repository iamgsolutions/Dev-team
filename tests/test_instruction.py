import pytest

from devteam.instruction import Instruction, MalformedInstruction


def full_instruction(**overrides):
    kw = dict(
        role="backend",
        read_first=["./.project-memory/STATE.md", "./BRIEF.md"],
        current_state="fase backend",
        task="implementa el endpoint GET /health",
        acceptance_criteria=["devuelve 200", "tiene test"],
        model_info="opencode / free",
        budget_note="restante $10",
        memory_updates=["STATE.md: registra lo hecho"],
    )
    kw.update(overrides)
    return Instruction(**kw)


def test_complete_instruction_contains_four_blocks():
    text = full_instruction().build()
    for block in ("== ORIENTACIÓN ==", "== TAREA ==", "== RESTRICCIONES ==",
                  "== CIERRE (OBLIGATORIO antes de terminar) =="):
        assert block in text
    assert "STATELESS" in text
    assert "la tarea NO está completa" in text


@pytest.mark.parametrize("missing", [
    {"read_first": []},
    {"current_state": ""},
    {"task": ""},
    {"acceptance_criteria": []},
    {"model_info": ""},
    {"budget_note": ""},
    {"memory_updates": []},   # the CIERRE block - the protocol's heart
])
def test_missing_any_block_raises(missing):
    with pytest.raises(MalformedInstruction):
        full_instruction(**missing).build()
