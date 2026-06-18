"""Quality gates (S8) - hard gate before any merge (spec R5: strict quality).

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


# Secret patterns scanned on EVERY gate run (built-in, free, no external tool).
# Conservative: high-signal prefixes only, to avoid drowning in false positives.
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{20,}",          # OpenAI/Anthropic/OpenRouter style keys
    r"ghp_[A-Za-z0-9]{30,}",            # GitHub PAT
    r"github_pat_[A-Za-z0-9_]{30,}",    # GitHub fine-grained PAT
    r"xox[baprs]-[A-Za-z0-9\-]{10,}",   # Slack tokens
    r"AKIA[0-9A-Z]{16}",                # AWS access key id
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]
SECRET_SCAN_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
                    ".toml", ".md", ".env.example", ".cfg", ".ini", ".sql", ".sh", ".ps1",
                    ".txt", ".conf", ".tf", ".properties"}
# Extension-less files worth scanning (e.g. the deploy phase generates Dockerfiles).
SECRET_SCAN_NAMES = {"Dockerfile", "dockerfile", "Makefile", "Procfile"}


def scan_secrets(workdir: Path, max_files: int = 2000) -> list[str]:
    """Return findings like 'file:line: pattern'. Skips .git, .env, venvs."""
    import re as _re
    findings: list[str] = []
    compiled = [_re.compile(p) for p in SECRET_PATTERNS]
    count = 0
    for f in workdir.rglob("*"):
        if count >= max_files or len(findings) >= 20:
            break
        parts = {p.lower() for p in f.parts}
        if {".git", ".venv", "node_modules", "__pycache__"} & parts:
            continue
        if not f.is_file() or f.name == ".env":
            continue
        if f.suffix.lower() not in SECRET_SCAN_EXTS and f.name not in SECRET_SCAN_NAMES:
            continue
        count += 1
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat in compiled:
                if pat.search(line):
                    findings.append(f"{f.relative_to(workdir)}:{i}")
                    break
    return findings


def run_gates(workdir: Path, timeout_s: int = 900) -> GateReport:
    specs = _load_custom_gates(workdir)
    if specs is None:
        specs = _default_gates(workdir)

    checks: list[GateCheck] = []

    # Built-in security gate: ALWAYS runs (spec: basic hardening always).
    leaks = scan_secrets(workdir)
    checks.append(GateCheck(
        "secrets", passed=not leaks,
        output=("clean" if not leaks else "possible secrets in: " + ", ".join(leaks)),
    ))
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
