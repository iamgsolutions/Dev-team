"""Subscription guardian - rations the premium brains (claude / codex).

Human's policy (2026-06-12, his words distilled):
- NEVER drain the subscriptions: weekly limits die in 3-4 days if you zero
  the session caps daily. The human AND his mother use both AIs interactively.
- Premium only for what truly needs it; bulk work goes to free/cheap models.
- Rate-limited mid-task? Fine - work continues in batches ("varias tandas"):
  the task defers and the daemon retries when the window reopens.

Mechanics (we cannot read the real subscription meters, so we combine):
1. A conservative DAILY CALL BUDGET per premium brain (configurable in
   data/subscription.json). When spent, the brain is "resting" until tomorrow.
2. Rate-limit detection from CLI output -> cooldown for N seconds.
3. router/executor consult available() before routing premium work.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import config

# Conservative defaults: leave clear headroom for the humans' interactive use.
# GEMINI IS DISABLED (0) by human decision 2026-06-12: he saw the engine's
# internal cost ESTIMATE ($0.00003) and prefers not to risk any billing until
# confirmed that CLI usage under his AI Pro subscription is not metered.
# NOTE: that figure was our own bookkeeping estimate, NOT a Google charge -
# OAuth "Login with Google" under AI Pro is subscription-covered (no per-call
# billing; only API keys bill per call). Re-enable: devteam subs --set gemini 25
DEFAULT_DAILY_CALLS = {"claude": 15, "codex": 20, "gemini": 0}
GUARDED_BRAINS = ("claude", "codex", "gemini")  # subscription-backed brains
DEFAULT_COOLDOWN_S = 3600  # 1h pause when the provider reports a limit
ERROR_COOLDOWN_S = 180     # short rest after a HARD error so the self-heal cascade
                           # advances to the NEXT premium brain (not the same one)

RATE_LIMIT_MARKERS = (
    "rate limit", "rate-limit", "usage limit", "limit reached", "quota",
    "too many requests", "429", "overloaded", "capacity", "try again later",
    "weekly limit", "session limit",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _state_path() -> Path:
    return config.DATA_DIR / "subscription.json"


def _load() -> dict:
    from .storage import load_json_safe
    d = load_json_safe(_state_path(), {})
    return d if isinstance(d, dict) else {}


def _save(state: dict) -> None:
    from .storage import atomic_write_json
    config.ensure_dirs()
    atomic_write_json(_state_path(), state)


def _brain_state(state: dict, brain: str) -> dict:
    today = date.today().isoformat()
    b = state.setdefault(brain, {})
    if b.get("date") != today:           # daily reset
        b["date"] = today
        b["calls"] = 0
    b.setdefault("cooldown_until", None)
    b.setdefault("daily_budget", DEFAULT_DAILY_CALLS.get(brain, 999999))
    return b


def looks_rate_limited(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in RATE_LIMIT_MARKERS)


def available(brain: str) -> bool:
    """Can the engine use this premium brain right now?"""
    if brain not in GUARDED_BRAINS:
        return True  # opencode etc. are not subscription-guarded
    state = _load()
    b = _brain_state(state, brain)
    _save(state)
    if b["cooldown_until"]:
        try:
            until = datetime.fromisoformat(b["cooldown_until"])
            if _now() < until:
                return False
        except (ValueError, TypeError):
            b["cooldown_until"] = None   # corrupt value -> treat as no cooldown
    return b["calls"] < b["daily_budget"]


def record_call(brain: str) -> None:
    if brain not in GUARDED_BRAINS:
        return
    state = _load()
    b = _brain_state(state, brain)
    b["calls"] += 1
    _save(state)


def report_rate_limit(brain: str, cooldown_s: int = DEFAULT_COOLDOWN_S) -> None:
    """Provider said 'limit' -> rest this brain for a while (work in batches)."""
    state = _load()
    b = _brain_state(state, brain)
    b["cooldown_until"] = (_now() + timedelta(seconds=cooldown_s)).isoformat()
    _save(state)


def report_error(brain: str, cooldown_s: int = ERROR_COOLDOWN_S) -> None:
    """A premium brain returned a HARD error/timeout (not a rate-limit). Rest it
    BRIEFLY so the self-heal cascade re-routes to the next premium brain instead
    of retrying the same failing one. Much shorter than a rate-limit cooldown."""
    if brain not in GUARDED_BRAINS:
        return
    report_rate_limit(brain, cooldown_s)


def clear_cooldown(brain: str) -> None:
    state = _load()
    b = _brain_state(state, brain)
    b["cooldown_until"] = None
    _save(state)


def status() -> dict:
    """For reporting: calls used / budget / cooldown per premium brain."""
    state = _load()
    out = {}
    for brain in GUARDED_BRAINS:
        b = _brain_state(state, brain)
        cooling = False
        if b["cooldown_until"]:
            try:
                cooling = _now() < datetime.fromisoformat(b["cooldown_until"])
            except (ValueError, TypeError):
                cooling = False
        out[brain] = {
            "calls_today": b["calls"],
            "daily_budget": b["daily_budget"],
            "cooling_down": cooling,
            "available": (not cooling) and b["calls"] < b["daily_budget"],
        }
    _save(state)
    return out


def set_daily_budget(brain: str, calls: int) -> None:
    """Tune the ration (e.g. weekend with heavy human use -> lower it)."""
    state = _load()
    b = _brain_state(state, brain)
    b["daily_budget"] = int(calls)
    _save(state)
