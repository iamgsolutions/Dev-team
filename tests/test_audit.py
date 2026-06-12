"""Audit panel + secrets gate tests (brains mocked - no real API calls)."""
import subprocess

import pytest

from devteam import audit
from devteam.brains import BrainResult
from devteam.gates import run_gates, scan_secrets


def make_repo_with_diff(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    def git(*a):
        subprocess.run(["git", "-C", str(repo), *a], capture_output=True, check=True)
    git("init", "-b", "main")
    (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
    git("add", "-A"); git("commit", "-m", "init")
    git("checkout", "-b", "task/t")
    (repo / "a.py").write_text("x = 2\npassword_input = validate(user_input)\n", encoding="utf-8")
    git("add", "-A"); git("commit", "-m", "change")
    return repo


def fake_invoke(verdict_text):
    def _inv(prompt, cwd, timeout_s=600, model=None):
        return BrainResult("ok", verdict_text, 0.0, model or "fake", 0.1)
    return _inv


def test_audit_approves_on_majority(tmp_path, monkeypatch):
    repo = make_repo_with_diff(tmp_path)
    monkeypatch.setattr(audit.oc_brain, "invoke", fake_invoke("VEREDICTO: APROBADO\nHALLAZGOS:\n- ninguno"))
    rep = audit.audit_worktree(repo, author_model="opencode/deepseek-v4-flash-free")
    assert rep.approved
    assert len(rep.votes) == 1                      # normal -> 1 free auditor
    assert rep.votes[0][0] != "opencode/deepseek-v4-flash-free"  # diversity


def test_audit_rejects_on_critical_findings(tmp_path, monkeypatch):
    repo = make_repo_with_diff(tmp_path)
    monkeypatch.setattr(audit.oc_brain, "invoke",
                        fake_invoke("VEREDICTO: RECHAZADO\nHALLAZGOS:\n- crítico: SQL injection"))
    monkeypatch.setattr(audit.codex_brain, "invoke",
                        fake_invoke("VEREDICTO: RECHAZADO\nHALLAZGOS:\n- crítico: confirmo"))
    monkeypatch.setattr(audit.gemini_brain, "invoke",
                        fake_invoke("VEREDICTO: RECHAZADO\nHALLAZGOS:\n- crítico: confirmo"))
    rep = audit.audit_worktree(repo, author_model=None, critical=True)
    assert not rep.approved
    assert len(rep.votes) >= 2                      # critical -> panel


def test_audit_garbled_verdict_is_not_approval(tmp_path, monkeypatch):
    repo = make_repo_with_diff(tmp_path)
    monkeypatch.setattr(audit.oc_brain, "invoke", fake_invoke("I think it looks fine?"))
    rep = audit.audit_worktree(repo, author_model=None)
    assert not rep.approved


def test_empty_diff_auto_approves(tmp_path):
    repo = tmp_path / "clean"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], capture_output=True)
    rep = audit.audit_worktree(repo, author_model=None)
    assert rep.approved


# --- secrets gate -------------------------------------------------------------

def test_secrets_gate_catches_leaked_key(tmp_path):
    (tmp_path / "config.py").write_text(
        'API_KEY = "sk-or-v1-abcdefghij1234567890abcdefghij"\n', encoding="utf-8")
    findings = scan_secrets(tmp_path)
    assert findings and "config.py" in findings[0]
    rep = run_gates(tmp_path)
    assert not rep.passed
    assert "secrets:FAIL" in rep.summary()


def test_secrets_gate_clean_project_passes(tmp_path):
    (tmp_path / "app.py").write_text('import os\nKEY = os.environ["API_KEY"]\n', encoding="utf-8")
    assert scan_secrets(tmp_path) == []
    assert run_gates(tmp_path).passed
