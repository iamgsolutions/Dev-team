"""Error-correction cascade: agents fix their own failures before escalating."""
import pytest

from devteam import pipeline
from devteam.executor import TaskResult
from devteam.gates import GateCheck, GateReport
from devteam.state import Project


@pytest.fixture(autouse=True)
def silence_discord(monkeypatch):
    sent = []
    monkeypatch.setattr(pipeline, "milestone", lambda t, m: sent.append(("hito", m)) or True)
    monkeypatch.setattr(pipeline, "blocker", lambda t, m: sent.append(("bloqueo", m)) or True)
    return sent


def make_project(tmp, state="backend"):
    p = Project(name="csc", path=tmp / "projects" / "csc")
    p.save()
    for s in ["pm", "architect", "backend"][: ["pm", "architect", "backend"].index(state) + 1]:
        p.transition(s)
    return p


def ok_result():
    return TaskResult("ok", "opencode", "m1", 0.0, "done", None, "r", None)  # no worktree -> skip gates


def test_corrective_feedback_reaches_second_attempt(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs)
    calls = []

    def fake_execute(**kw):
        calls.append(kw["task"])
        if len(calls) == 1:
            return TaskResult("error", "opencode", "m1", 0.0, "boom: syntax error", None, "r", None)
        return ok_result()

    monkeypatch.setattr(pipeline, "execute_task", fake_execute)
    out = pipeline.run_phase(p)
    assert out.advanced_to == "frontend"
    assert len(calls) == 2
    assert "CORRECCIÓN" in calls[1] and "boom" in calls[1]   # feedback injected


def test_cascade_exhaustion_escalates_to_blocker(isolated_dirs, monkeypatch, silence_discord):
    p = make_project(isolated_dirs)
    monkeypatch.setattr(pipeline, "execute_task",
                        lambda **kw: TaskResult("error", "opencode", "m1", 0.0, "always fails",
                                                None, "r", None))
    out = pipeline.run_phase(p)
    assert out.advanced_to is None
    assert "cascada agotada" in out.note
    assert any(k == "bloqueo" and "autocorrección" in m for k, m in silence_discord)


def test_gate_failure_triggers_self_heal(isolated_dirs, monkeypatch, tmp_path):
    p = make_project(isolated_dirs)
    wt = tmp_path / "wt"; wt.mkdir()
    calls = []

    def fake_execute(**kw):
        calls.append(kw["task"])
        return TaskResult("ok", "opencode", "m1", 0.0, "done", None, "r", str(wt))

    fails_then_passes = [GateReport(False, [GateCheck("tests", False, output="2 failed")]),
                         GateReport(True, [GateCheck("tests", True)])]
    monkeypatch.setattr(pipeline, "execute_task", fake_execute)
    import devteam.pipeline as pl
    monkeypatch.setattr("devteam.gates.run_gates", lambda w: fails_then_passes.pop(0))
    out = pipeline.run_phase(p)
    assert len(calls) == 2
    assert "GATES fallidos" in calls[1]
    assert out.advanced_to == "frontend"


def test_deferred_does_not_burn_retries(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs)
    monkeypatch.setattr(pipeline, "execute_task",
                        lambda **kw: TaskResult("deferred", "", "", 0.0, "resting", None, "r", None))
    out = pipeline.run_phase(p)
    assert "aplazada" in out.note
    assert p.state == "backend"
