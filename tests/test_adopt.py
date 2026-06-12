import subprocess

import pytest

from devteam.adopt import adopt_project
from devteam.state import registry_get


def make_existing_repo(tmp_path):
    repo = tmp_path / "legacyapp"
    repo.mkdir()
    (repo / "ROADMAP.md").write_text("# Roadmap\n- [x] login\n- [ ] payments\n", encoding="utf-8")
    (repo / "main.py").write_text("print('legacy')\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "init"], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "legacy"], capture_output=True)
    return repo


def test_adopt_existing_repo(isolated_dirs, tmp_path):
    repo = make_existing_repo(tmp_path)
    p = adopt_project(repo)
    assert p.name == "legacyapp"
    assert p.state == "qa"                       # audit-first rule
    state = (repo / ".project-memory" / "STATE.md").read_text(encoding="utf-8")
    assert "ADOPTADO" in state and "payments" in state   # seeded from ROADMAP
    assert (repo / "AGENTS.md").exists()
    assert (repo / "docs" / "STANDARDS.md").exists()
    assert (repo / "main.py").read_text(encoding="utf-8") == "print('legacy')\n"  # untouched
    assert registry_get("legacyapp").name == "legacyapp"


def test_adopt_requires_git_repo(isolated_dirs, tmp_path):
    plain = tmp_path / "notarepo"; plain.mkdir()
    with pytest.raises(ValueError):
        adopt_project(plain)


def test_adopt_twice_fails(isolated_dirs, tmp_path):
    repo = make_existing_repo(tmp_path)
    adopt_project(repo)
    with pytest.raises(FileExistsError):
        adopt_project(repo)


def test_adopt_respects_existing_agents_md(isolated_dirs, tmp_path):
    repo = make_existing_repo(tmp_path)
    (repo / "AGENTS.md").write_text("# custom rules\n", encoding="utf-8")
    adopt_project(repo)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == "# custom rules\n"
