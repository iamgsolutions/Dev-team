import json

from devteam.gates import run_gates


def write_gates(tmp_path, gates):
    d = tmp_path / ".project-memory"
    d.mkdir(parents=True, exist_ok=True)
    (d / "gates.json").write_text(json.dumps({"gates": gates}), encoding="utf-8")


def test_passing_gate(tmp_path):
    write_gates(tmp_path, [{"name": "ok", "cmd": ["cmd", "/c", "exit 0"]}])
    rep = run_gates(tmp_path)
    assert rep.passed
    assert rep.checks[0].passed


def test_failing_gate_blocks(tmp_path):
    write_gates(tmp_path, [
        {"name": "ok", "cmd": ["cmd", "/c", "exit 0"]},
        {"name": "bad", "cmd": ["cmd", "/c", "exit 1"]},
    ])
    rep = run_gates(tmp_path)
    assert not rep.passed
    assert "bad:FAIL" in rep.summary()


def test_missing_tool_is_skipped_not_failed(tmp_path):
    write_gates(tmp_path, [{"name": "ghost", "cmd": ["tool-that-does-not-exist-xyz"]}])
    rep = run_gates(tmp_path)
    assert rep.passed            # nothing actually ran -> no hard fail
    assert rep.checks[0].skipped
    assert "ghost:SKIP" in rep.summary()


def test_no_gates_passes_with_note(tmp_path):
    rep = run_gates(tmp_path)
    assert rep.passed
    assert "no gates" in rep.summary()


def test_python_defaults_detected(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    rep = run_gates(tmp_path)
    names = [c.name for c in rep.checks]
    assert "lint" in names and "tests" in names
