"""24/7 daemon (S13-driven loop) - SKELETON for Fase 2 / M4.

Loop: pick active project -> honor paused flag -> check Discord thread for
human interventions (pause/redirect) -> execute next pipeline step -> report
milestones/blockers -> repeat. Designed to survive restarts (all state is on
disk via state.py).

TODO(M4): intervention listener (read Discord thread via hermes CLI or
gateway state), scheduling, crash-safe loop, Windows service registration.
"""
from __future__ import annotations
