import pytest

from devteam.budget import BudgetExceeded, charge, estimate_cost_usd, remaining
from devteam.state import Project


def make_project(tmp_path, cap=10.0):
    p = Project(name="b", path=tmp_path / "projects" / "b", budget_cap_usd=cap)
    p.save()
    return p


def test_charge_accumulates_and_persists(isolated_dirs):
    p = make_project(isolated_dirs)
    charge(p, 2.5, "task A")
    charge(p, 1.5, "task B")
    assert p.spent_usd == pytest.approx(4.0)
    assert remaining(p) == pytest.approx(6.0)
    assert Project.load(p.path).spent_usd == pytest.approx(4.0)


def test_alert_fires_once_at_80(isolated_dirs):
    p = make_project(isolated_dirs, cap=10.0)
    r1 = charge(p, 7.9)        # 79% - no alert
    assert not r1.alert_80
    r2 = charge(p, 0.2)        # crosses 80% - alert
    assert r2.alert_80
    r3 = charge(p, 0.5)        # already past - no re-alert
    assert not r3.alert_80


def test_cap_is_a_hard_stop(isolated_dirs):
    p = make_project(isolated_dirs, cap=10.0)
    charge(p, 9.0)
    with pytest.raises(BudgetExceeded):
        charge(p, 2.0)
    # the failed charge must NOT be recorded
    assert p.spent_usd == pytest.approx(9.0)


def test_free_models_cost_zero():
    assert estimate_cost_usd(
        "openrouter/meta-llama/llama-3.3-70b-instruct:free", 100_000, 50_000
    ) == 0.0
    assert estimate_cost_usd("openrouter/deepseek/deepseek-chat", 1_000_000, 0) == pytest.approx(0.30)
    # unknown models must never be assumed free
    assert estimate_cost_usd("totally-unknown-model", 1_000_000, 1_000_000) > 0
