"""M4 pipeline tests - executor and Discord mocked (no real brains/messages)."""
import pytest

from devteam import pipeline
from devteam.executor import TaskResult
from devteam.roles import PHASE_TASKS
from devteam.state import Project


@pytest.fixture(autouse=True)
def silence_discord(monkeypatch):
    sent = []
    monkeypatch.setattr(pipeline, "milestone", lambda t, m: sent.append(("hito", m)) or True)
    monkeypatch.setattr(pipeline, "blocker", lambda t, m: sent.append(("bloqueo", m)) or True)
    return sent


def ok_result(branch=None):
    return TaskResult("ok", "opencode", "test-model", 0.01, "done", branch, "test route")


def make_project(tmp, state="pm"):
    p = Project(name="pl", path=tmp / "projects" / "pl")
    p.save()
    if state != "new":
        # walk legally to the target state
        order = ["pm", "architect", "backend", "frontend", "qa", "deploy", "review", "done"]
        for s in order[: order.index(state) + 1]:
            p.transition(s)
    return p


def test_roles_generate_complete_tasks(isolated_dirs):
    p = make_project(isolated_dirs)
    for phase, gen in PHASE_TASKS.items():
        spec = gen(p)
        assert spec.role and spec.task and spec.acceptance_criteria
    assert PHASE_TASKS["pm"](p).critical and PHASE_TASKS["architect"](p).critical
    assert not PHASE_TASKS["backend"](p).critical


def test_pm_phase_stops_at_human_checkpoint(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs, "pm")
    monkeypatch.setattr(pipeline, "execute_task", lambda **kw: ok_result())
    out = pipeline.run_phase(p)
    assert out.waiting_human          # PRD approval required
    assert out.advanced_to is None
    assert p.state == "pm"            # did NOT advance on its own


def test_approve_advances_past_checkpoint(isolated_dirs):
    p = make_project(isolated_dirs, "pm")
    msg = pipeline.approve(p)
    assert p.state == "architect"
    assert "architect" in msg


def test_backend_phase_autoadvances(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs, "backend")
    monkeypatch.setattr(pipeline, "execute_task", lambda **kw: ok_result())
    out = pipeline.run_phase(p)
    assert out.advanced_to == "frontend"
    assert p.state == "frontend"


def test_failed_task_blocks_and_does_not_advance(isolated_dirs, monkeypatch, silence_discord):
    p = make_project(isolated_dirs, "backend")
    monkeypatch.setattr(
        pipeline, "execute_task",
        lambda **kw: TaskResult("error", "opencode", "m", 0.0, "boom", None, "r"),
    )
    out = pipeline.run_phase(p)
    assert out.advanced_to is None
    assert p.state == "backend"
    assert any(kind == "bloqueo" for kind, _ in silence_discord)


def test_paused_project_never_executes(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs, "backend")
    p.pause()
    called = []
    monkeypatch.setattr(pipeline, "execute_task", lambda **kw: called.append(1) or ok_result())
    out = pipeline.run_phase(p)
    assert not called
    assert "pausado" in out.note


def test_review_approval_finishes_project(isolated_dirs):
    p = make_project(isolated_dirs, "review")
    pipeline.approve(p)
    assert p.state == "done"


def test_no_checkpoint_approve_is_noop(isolated_dirs):
    p = make_project(isolated_dirs, "backend")
    msg = pipeline.approve(p)
    assert "no hay checkpoint" in msg
    assert p.state == "backend"
