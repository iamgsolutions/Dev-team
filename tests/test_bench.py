"""Benchmark harness tests (brains + gates mocked - no real agents)."""
from devteam import bench
from devteam.brains import BrainResult


def test_run_bench_compares_configs(tmp_path, monkeypatch):
    counter = {"n": 0}

    def fake_scratch():
        counter["n"] += 1
        p = tmp_path / f"s{counter['n']}"
        p.mkdir()
        return p

    def fake_get_invoker(brain):
        def _inv(prompt, cwd, timeout_s, model=None):
            return BrainResult("ok", "created calc.py + test", 0.0,
                               model or f"{brain}-default", 1.5)
        return _inv

    monkeypatch.setattr(bench, "_scratch_repo", fake_scratch)
    monkeypatch.setattr(bench, "get_invoker", fake_get_invoker)
    monkeypatch.setattr(bench, "run_gates", lambda d: type("G", (), {"passed": True})())

    results = bench.run_bench(configs=[("opencode", "m-free"), ("jcode", None)])
    assert len(results) == 2
    assert {r.brain for r in results} == {"opencode", "jcode"}
    assert all(r.status == "ok" and r.gate_passed for r in results)

    rep = bench.format_report(results)
    assert "BRAIN" in rep and "opencode" in rep and "jcode" in rep


def test_run_bench_handles_unknown_brain(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "_scratch_repo", lambda: tmp_path / "x")
    (tmp_path / "x").mkdir()
    # get_invoker raises KeyError for an unknown brain -> recorded, not crashed
    results = bench.run_bench(configs=[("nope", None)], gate=False)
    assert len(results) == 1
    assert results[0].status == "error" and "unknown brain" in results[0].note


def test_bench_does_not_run_gate_on_failure(tmp_path, monkeypatch):
    def fake_scratch():
        p = tmp_path / "y"
        p.mkdir(exist_ok=True)
        return p
    monkeypatch.setattr(bench, "_scratch_repo", fake_scratch)

    def fake_get_invoker(brain):
        return lambda prompt, cwd, timeout_s, model=None: BrainResult(
            "error", "boom", 0.0, model or "m", 0.3)

    monkeypatch.setattr(bench, "get_invoker", fake_get_invoker)
    called = {"gate": False}
    monkeypatch.setattr(bench, "run_gates",
                        lambda d: called.__setitem__("gate", True) or type("G", (), {"passed": True})())
    results = bench.run_bench(configs=[("opencode", "m")], gate=True)
    assert results[0].status == "error"
    assert results[0].gate_passed is None      # gate not run on a failed task
    assert called["gate"] is False
