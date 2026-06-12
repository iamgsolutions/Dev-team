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
