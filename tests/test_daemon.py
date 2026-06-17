"""Daemon robustness: singleton lock + safe_run_phase pauses on exception."""
import os

import pytest

from devteam import daemon
from devteam.state import Project


def test_singleton_lock_blocks_second_daemon(isolated_dirs):
    assert daemon._acquire_singleton() is True
    assert daemon._acquire_singleton() is False   # our own pid owns it
    daemon._release_singleton()
    assert daemon._acquire_singleton() is True
    daemon._release_singleton()


def test_stale_pidfile_is_taken_over(isolated_dirs):
    from devteam.storage import atomic_write_text
    daemon.config.ensure_dirs()
    atomic_write_text(daemon._pidfile(), "999999999")   # almost certainly dead pid
    assert daemon._acquire_singleton() is True          # took over the stale lock
    daemon._release_singleton()


def test_safe_run_phase_pauses_on_unexpected_exception(isolated_dirs, monkeypatch):
    p = Project(name="boom", path=isolated_dirs / "projects" / "boom")
    p.save()
    p.transition("pm")

    def explode(_p):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(daemon, "run_phase", explode)
    monkeypatch.setattr("devteam.discord_bridge.blocker", lambda *a, **k: True)
    out = daemon._safe_run_phase(p)
    assert out.note.startswith("exception")
    assert Project.load(p.path).paused is True   # paused, NOT left re-failing
