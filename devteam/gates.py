"""Quality gates (S8) - hard gate before any merge (spec R5: calidad estricta).

v1 design: each project can define its gate commands in
.project-memory/gates.json (written by the Architect phase):
    { "gates": [ {"name": "lint", "cmd": ["ruff", "check", "."]},
                 {"name": "tests", "cmd": ["pytest", "-q"]} ] }
If the file is absent, sensible defaults are inferred from the stack
(pyproject.toml -> ruff/pytest; package.json -> npm scripts when present).

Hard rule: a gate that RUNS and fails -> the work does not merge. A tool that
is not available counts as "skipped" (recorded, not silently ignored).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import config

GATES_FILE = "gates.json"


@dataclass
class GateCheck:
    name: str
    passed: bool
    skipped: bool = False
    output: str = ""


@dataclass
class GateReport:
    passed: bool
    checks: list[GateCheck] = field(default_factory=list)

    def summary(self) -> str:
        parts = []
        for c in self.checks:
            mark = "SKIP" if c.skipped else ("PASS" if c.passed else "FAIL")
            parts.append(f"{c.name}:{mark}")
        return f"{'PASS' if self.passed else 'FAIL'} ({', '.join(parts) or 'no gates'})"


def _load_custom_gates(workdir: Path) -> list[dict] | None:
    f = workdir / config.PROJECT_MEMORY_DIR / GATES_FILE
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("gates", [])
    except (json.JSONDecodeError, OSError):
        return None


def _default_gates(workdir: Path) -> list[dict]:
    gates: list[dict] = []
    if (workdir / "pyproject.toml").exists() or list(workdir.glob("*.py")):
        gates.append({"name": "lint", "cmd": ["ruff", "check", "."]})
        if (workdir / "tests").exists():
            gates.append({"name": "tests", "cmd": ["pytest", "-q"]})
    if (workdir / "package.json").exists():
        try:
            pkg = json.loads((workdir / "package.json").read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})
            for script, gate_name in (("lint", "lint"), ("test", "tests"), ("build", "build")):
                if script in scripts:
                    gates.append({"name": gate_name, "cmd": ["npm", "run", script]})
        except (json.JSONDecodeError, OSError):
            pass
    return gates


def run_gates(workdir: Path, timeout_s: int = 900) -> GateReport:
    specs = _load_custom_gates(workdir)
    if specs is None:
        specs = _default_gates(workdir)

    checks: list[GateCheck] = []
    for spec in specs:
        name, cmd = spec.get("name", "gate"), spec.get("cmd", [])
        if not cmd:
            continue
        exe = config.resolve_cli(cmd[0])
        if shutil.which(exe) is None and not Path(exe).exists():
            checks.append(GateCheck(name, passed=False, skipped=True,
                                    output=f"tool not available: {cmd[0]}"))
            continue
        try:
            proc = subprocess.run(
                [exe, *cmd[1:]], cwd=str(workdir), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout_s,
                stdin=subprocess.DEVNULL,
            )
            checks.append(GateCheck(name, passed=proc.returncode == 0,
                                    output=(proc.stdout + proc.stderr)[-3000:]))
        except subprocess.TimeoutExpired:
            checks.append(GateCheck(name, passed=False, output=f"timeout after {timeout_s}s"))

    ran = [c for c in checks if not c.skipped]
    passed = all(c.passed for c in ran) if ran else True
    return GateReport(passed=passed, checks=checks)
