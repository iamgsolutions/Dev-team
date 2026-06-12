"""Shared fixtures: isolate DATA/PROJECTS dirs into tmp_path for every test."""
import pytest

from devteam import config


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "PROJECTS_ROOT", tmp_path / "projects")
    config.ensure_dirs()
    yield tmp_path
