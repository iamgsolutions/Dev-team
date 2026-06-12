"""Subscription guardian tests - the family-friendly ration system."""
from devteam import subscription
from devteam.router import BRAIN_DEFER, route


def test_daily_budget_exhausts(isolated_dirs):
    subscription.set_daily_budget("claude", 3)
    assert subscription.available("claude")
    for _ in range(3):
        subscription.record_call("claude")
    assert not subscription.available("claude")          # ration spent
    assert subscription.available("codex")               # independent ration


def test_rate_limit_cooldown_and_wake(isolated_dirs):
    assert subscription.available("codex")
    subscription.report_rate_limit("codex", cooldown_s=3600)
    assert not subscription.available("codex")
    subscription.clear_cooldown("codex")
    assert subscription.available("codex")


def test_status_reports_both_brains(isolated_dirs):
    subscription.set_daily_budget("claude", 5)
    subscription.record_call("claude")
    st = subscription.status()
    assert st["claude"]["calls_today"] == 1
    assert st["claude"]["daily_budget"] == 5
    assert st["claude"]["available"]
    assert "codex" in st


def test_rate_limit_marker_detection():
    assert subscription.looks_rate_limited("Error: usage limit reached for your plan")
    assert subscription.looks_rate_limited("HTTP 429 Too Many Requests")
    assert subscription.looks_rate_limited("You've hit your weekly limit")
    assert not subscription.looks_rate_limited("task completed successfully")


def test_opencode_is_never_guarded(isolated_dirs):
    assert subscription.available("opencode")
    subscription.record_call("opencode")  # no-op, must not crash
    assert subscription.available("opencode")


# --- router x availability ----------------------------------------------------

def test_critical_defers_when_both_premium_resting():
    r = route("backend", critical=True, claude_available=False, codex_available=False)
    assert r.brain == BRAIN_DEFER


def test_critical_falls_to_codex_when_claude_resting():
    r = route("architect", critical=True, claude_available=False, codex_available=True)
    assert r.brain == "codex"


def test_audit_degrades_to_cheap_when_codex_resting():
    r = route("review", author_brain="claude", codex_available=False)
    assert r.brain == "opencode"


def test_execution_unaffected_by_premium_availability():
    r = route("backend", claude_available=False, codex_available=False)
    assert r.brain == "opencode"
