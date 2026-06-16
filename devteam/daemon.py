"""24/7 daemon (M4b) - durable loop over the project registry.

Honors (spec R4/R7): one project at a time, paused flag, human checkpoints
(does not re-run a completed phase while waiting approval), clarification
waits, budget pauses. All state is on disk - the daemon can die and resume.

Not yet wired (M4c/M5+): reading human orders from the Discord thread
(today pause/approve arrive via CLI or Hermes skill), deploy phase (M6).
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from . import config
from .pipeline import run_phase
from .state import Project, registry_load

ACTIONABLE_STATES = {"pm", "architect", "backend", "frontend", "qa", "deploy", "review"}
AUTO_BENCH_EVERY = 20   # ticks between auto-bench sweeps of the scorecard


@dataclass
class TickResult:
    acted_on: str | None      # project name we ran a phase for
    note: str


def _candidates() -> list[Project]:
    reg = registry_load()
    out: list[Project] = []
    for name, path in reg["projects"].items():
        try:
            out.append(Project.load(Path(path)))
        except Exception as e:  # noqa: BLE001 - a corrupt project must not kill the loop
            print(f"[daemon] skipping unreadable project {name}: {e}")
    return out


def _actionable(p: Project) -> bool:
    if p.paused or p.state not in ACTIONABLE_STATES:
        return False
    if p.phase_completed and p.requires_human_checkpoint():
        return False  # waiting for human approval
    return True


def tick() -> TickResult:
    """One daemon step: (1) apply human interventions from Discord threads for
    ALL projects (even paused ones - that's how they get resumed), then
    (2) run ONE phase step for the first actionable project."""
    from .discord_listener import check_interventions, listener_available

    candidates = _candidates()

    if listener_available():
        for p in candidates:
            try:
                for action in check_interventions(p):
                    print(f"[daemon] intervention: {action}")
            except Exception as e:  # noqa: BLE001 - listener must not kill the loop
                print(f"[daemon] listener error on {p.name}: {e}")

    for p in candidates:
        # reload: an intervention may have just paused/approved/resumed it
        try:
            p = Project.load(p.path)
        except Exception:  # noqa: BLE001
            continue
        if not _actionable(p):
            continue
        out = _safe_run_phase(p)
        return TickResult(p.name, f"{out.phase} -> {out.advanced_to or out.waiting_human or out.note}")
    return TickResult(None, "nothing actionable (all waiting/paused/done)")


def _safe_run_phase(p: Project):
    """Run a phase, but ANY unexpected exception PAUSES the project and notifies
    instead of leaving it actionable to re-fail every tick (audit philosophy:
    on unrecoverable failure, pause + alert, never silent re-fail loop)."""
    from .pipeline import PhaseOutcome
    try:
        return run_phase(p)
    except Exception as e:  # noqa: BLE001
        try:
            p.pause(f"excepción inesperada en fase {p.state}: {type(e).__name__}: {e}")
            from .discord_bridge import blocker
            blocker(p.discord_channel,
                    f"Proyecto {p.name} · fase {p.state}: error inesperado del sistema "
                    f"({type(e).__name__}) → PAUSADO. Necesito que lo revises antes de reanudar.")
        except Exception:  # noqa: BLE001 - notification/pause must never re-raise
            pass
        return PhaseOutcome(p.state, None, None, None, f"excepción: {type(e).__name__}")


def _pidfile() -> Path:
    return config.DATA_DIR / "daemon.pid"


def _acquire_singleton() -> bool:
    """Refuse to start a 2nd daemon (two would trample shared state).
    Returns True if we got the lock."""
    config.ensure_dirs()
    pf = _pidfile()
    if pf.exists():
        try:
            old = int(pf.read_text(encoding="utf-8").strip())
            # is the old pid still alive?
            os.kill(old, 0)
            return False        # alive -> another daemon owns the lock
        except (ValueError, OSError):
            pass                # stale pidfile -> take over
    from .storage import atomic_write_text
    atomic_write_text(pf, str(os.getpid()))
    return True


def _release_singleton() -> None:
    try:
        _pidfile().unlink()
    except OSError:
        pass


def loop(interval_s: int = 60) -> None:
    """Blocking 24/7 loop. Ctrl+C to stop. State survives restarts.
    Single-instance: a second daemon refuses to start (audit fix)."""
    if not _acquire_singleton():
        print(f"[daemon] another daemon is already running (see {_pidfile()}). Refusing to start.")
        return
    print(f"[daemon] started (pid {os.getpid()}), interval={interval_s}s. Ctrl+C to stop.")
    ticks = 0
    try:
        while True:
            try:
                r = tick()
                if r.acted_on:
                    print(f"[daemon] {r.acted_on}: {r.note}")
                ticks += 1
                if ticks % AUTO_BENCH_EVERY == 0:
                    from .reflective import auto_bench
                    for benched in auto_bench():
                        print(f"[daemon] auto-bench: {benched}")
            except KeyboardInterrupt:
                print("[daemon] stopped by user")
                return
            except Exception as e:  # noqa: BLE001 - the loop must survive anything
                print(f"[daemon] tick error (loop continues): {e}")
            time.sleep(interval_s)
    finally:
        _release_singleton()
