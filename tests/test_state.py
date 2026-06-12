import pytest

from devteam import config
from devteam.state import InvalidTransition, Project


def make_project(tmp_path, name="demo"):
    p = Project(name=name, path=tmp_path / "projects" / name)
    p.save()
    return p


def test_valid_pipeline_walk(isolated_dirs):
    p = make_project(isolated_dirs)
    for nxt in ["pm", "architect", "backend", "frontend", "qa", "deploy", "review", "done"]:
        p.transition(nxt)
    assert p.state == "done"
    assert len(p.history) == 8


def test_invalid_transition_raises(isolated_dirs):
    p = make_project(isolated_dirs)
    with pytest.raises(InvalidTransition):
        p.transition("deploy")  # cannot jump new -> deploy


def test_qa_can_bounce_back(isolated_dirs):
    p = make_project(isolated_dirs)
    for nxt in ["pm", "architect", "backend", "frontend", "qa"]:
        p.transition(nxt)
    p.transition("backend", "QA found API bugs")  # bounce-back allowed
    assert p.state == "backend"


def test_persistence_roundtrip(isolated_dirs):
    p = make_project(isolated_dirs)
    p.transition("pm")
    p.pause("test pause")
    loaded = Project.load(p.path)
    assert loaded.state == "pm"
    assert loaded.paused is True
    assert loaded.budget_cap_usd == config.DEFAULT_BUDGET_CAP_USD


def test_human_checkpoints_flagged(isolated_dirs):
    p = make_project(isolated_dirs)
    p.transition("pm")
    assert p.requires_human_checkpoint()  # PRD approval
    p.transition("architect")
    assert p.requires_human_checkpoint()  # architecture approval
    p.transition("backend")
    assert p.requires_human_checkpoint() is None
