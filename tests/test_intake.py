from devteam import config
from devteam.intake import extract_budget_cap, new_project, validate_brief
from devteam.state import registry_get

GOOD_BRIEF = """# Brief de Proyecto — testapp

## 1. Identidad
- **Nombre del proyecto:** testapp

## 2. Objetivo y problema
- **Qué problema resuelve:** probar el intake.

## 3. Funcionalidades
- [x] (M) una cosa

## 10. Criterios de éxito
- **El proyecto está listo cuando:** el test pasa.

## 12. Presupuesto y límites
- **Tope de gasto en APIs de pago para este proyecto:** $15
"""

BAD_BRIEF = """# Brief — vago
Quiero una app que mole.
"""


def test_good_brief_goes_to_pm(isolated_dirs, tmp_path):
    brief = tmp_path / "brief.md"
    brief.write_text(GOOD_BRIEF, encoding="utf-8")
    project, questions = new_project(brief)
    assert questions == []
    assert project.state == "pm"
    assert project.name == "testapp"
    assert project.budget_cap_usd == 15.0
    # memory files created (handoff protocol baseline)
    mem = project.path / config.PROJECT_MEMORY_DIR
    assert (mem / "STATE.md").exists()
    assert (mem / "NOTES.md").exists()
    assert (project.path / "BRIEF.md").exists()
    assert (project.path / ".git").exists()
    # registered in the engine registry
    assert registry_get("testapp").name == "testapp"


def test_vague_brief_goes_to_clarification(isolated_dirs, tmp_path):
    brief = tmp_path / "bad.md"
    brief.write_text(BAD_BRIEF, encoding="utf-8")
    project, questions = new_project(brief, name="vago")
    assert project.state == "clarification"
    assert len(questions) >= 2  # grouped questions for the human


def test_validate_and_cap_helpers():
    assert validate_brief(GOOD_BRIEF) == []
    assert len(validate_brief(BAD_BRIEF)) == 3
    assert extract_budget_cap(GOOD_BRIEF) == 15.0
    assert extract_budget_cap(BAD_BRIEF) == config.DEFAULT_BUDGET_CAP_USD
