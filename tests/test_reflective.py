from devteam import config, reflective
from devteam.router import fallback_chain


def test_scorecard_records_and_rates(isolated_dirs):
    reflective.record("model-a", "opencode", "ok")
    reflective.record("model-a", "opencode", "ok")
    reflective.record("model-a", "opencode", "gate_failed")
    assert reflective.success_rate("model-a") == 2 / 3
    assert "model-a" in reflective.format_report()


def test_bench_excludes_model_from_fallback(isolated_dirs):
    victim = config.OPENCODE_FREE_MODELS[1]
    assert victim in fallback_chain(None)
    reflective.bench(victim)
    assert victim not in fallback_chain(None)
    reflective.unbench(victim)
    assert victim in fallback_chain(None)


def test_unknown_model_rate_is_none(isolated_dirs):
    assert reflective.success_rate("never-seen") is None


def test_auto_bench_benches_sustained_loser(isolated_dirs):
    for _ in range(2):
        reflective.record("weak/model", "opencode", "ok")
    for _ in range(8):
        reflective.record("weak/model", "opencode", "error")   # 2/10 = 20% < 40%
    newly = reflective.auto_bench()
    assert "weak/model" in newly
    assert reflective.is_benched("weak/model")


def test_auto_bench_needs_enough_evidence(isolated_dirs):
    reflective.record("new/model", "opencode", "error")   # only 1 task
    assert reflective.auto_bench() == []
    assert not reflective.is_benched("new/model")


def test_auto_bench_protects_premium_brains(isolated_dirs):
    for _ in range(10):
        reflective.record("claude-default", "claude", "rate_limited")   # all "fail"
    assert reflective.auto_bench() == []           # premium never auto-benched
    assert not reflective.is_benched("claude-default")
