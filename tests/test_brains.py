import json

import pytest

from devteam import config
from devteam.brains import BrainResult, get_invoker, jcode


def test_jcode_registered_in_get_invoker():
    assert get_invoker(config.BRAIN_JCODE) is jcode.invoke


def test_get_invoker_unknown_raises():
    with pytest.raises(KeyError):
        get_invoker("nope")


def test_jcode_invokes_via_openrouter_and_parses_json(monkeypatch, tmp_path):
    captured = {}

    def fake_run_cli(args, cwd, timeout_s, input_text=None):
        captured["args"] = args
        blob = json.dumps({"result": "done: created file", "cost_usd": 0.0})
        return 0, blob, "", 1.23

    monkeypatch.setattr(jcode, "run_cli", fake_run_cli)
    res = jcode.invoke("make a thing", tmp_path)

    assert isinstance(res, BrainResult)
    assert res.status == "ok"
    assert res.output == "done: created file"
    assert res.cost_usd == 0.0
    # headless contract: run, machine-readable, no self-update, openrouter provider
    a = captured["args"]
    assert "run" in a and "--json" in a and "--no-update" in a
    assert "-p" in a and "openrouter" in a


def test_jcode_rate_limit_is_detected(monkeypatch, tmp_path):
    monkeypatch.setattr(jcode, "run_cli",
                        lambda *a, **k: (1, "", "HTTP 429 rate limit", 0.5))
    res = jcode.invoke("x", tmp_path)
    assert res.status == "rate_limited"


def test_jcode_timeout(monkeypatch, tmp_path):
    monkeypatch.setattr(jcode, "run_cli", lambda *a, **k: (-1, "", "", 9.9))
    res = jcode.invoke("x", tmp_path)
    assert res.status == "timeout"


def test_jcode_exe_env_override(monkeypatch, tmp_path):
    fake = tmp_path / "jcode.exe"
    fake.write_text("")
    monkeypatch.setenv("DEVTEAM_JCODE", str(fake))
    assert jcode._jcode_exe() == str(fake)
