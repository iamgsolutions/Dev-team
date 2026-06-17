"""Deploy phase + review acceptance gate are no longer orphan states."""
import pytest

from devteam import pipeline, skillpack
from devteam.executor import TaskResult
from devteam.roles import PHASE_TASKS, deploy_task
from devteam.state import Project


@pytest.fixture(autouse=True)
def silence_discord(monkeypatch):
    monkeypatch.setattr(pipeline, "milestone", lambda t, m: True)
    monkeypatch.setattr(pipeline, "blocker", lambda t, m: True)


def walk_to(p, state):
    order = ["pm", "architect", "backend", "frontend", "qa", "deploy", "review", "done"]
    for s in order[: order.index(state) + 1]:
        p.transition(s)


def test_deploy_is_a_real_phase():
    assert "deploy" in PHASE_TASKS
    assert "deploy" in skillpack.ROLE_SKILLS
    spec = deploy_task.__wrapped__ if hasattr(deploy_task, "__wrapped__") else deploy_task
    # deploy pack must include devops craft
    assert "devops" in skillpack.ROLE_SKILLS["deploy"]
    assert "Dockerfile" in skillpack.load_for_role("deploy") or len(skillpack.load_for_role("deploy")) > 500


def test_review_state_waits_for_human_acceptance(isolated_dirs):
    p = Project(name="rv", path=isolated_dirs / "projects" / "rv")
    p.save()
    walk_to(p, "review")
    out = pipeline.run_phase(p)
    assert out.waiting_human                      # acceptance gate, not orphan
    assert p.phase_completed is True
    # a second run keeps waiting (does not loop)
    out2 = pipeline.run_phase(p)
    assert out2.waiting_human


def test_qa_no_skips_orphan_anymore(isolated_dirs):
    # qa->deploy used to leave the project stuck; deploy is now actionable
    from devteam import daemon
    assert "deploy" in daemon.ACTIONABLE_STATES
    assert "review" in daemon.ACTIONABLE_STATES


def test_lessons_get_injected_into_pack(isolated_dirs, monkeypatch, tmp_path):
    # point skills dir at a temp copy so we don't pollute the real lessons
    import shutil
    tmp_skills = tmp_path / "skills"
    shutil.copytree(skillpack.SKILLS_DIR, tmp_skills)
    monkeypatch.setattr(skillpack, "SKILLS_DIR", tmp_skills)
    before = skillpack.load_for_role("backend")
    skillpack.append_lesson("backend", "do not forget the index on the notes FK")
    after = skillpack.load_for_role("backend")
    assert "LESSONS LEARNED" in after
    assert "index on the notes FK" in after
    assert len(after) > len(before)
