"""Model/brain benchmark (roadmap H) - run the SAME task across several brains/
models in isolated scratch repos and compare success, cost and latency.

This is how we decide jcode vs OpenCode (ADR-017): `devteam bench` runs a fixed
coding task on each config, runs the quality gates on the result, and prints a
comparison. Each brain is invoked with its EXACT pinned model (no fallback), so
the numbers reflect that model, not the gateway's cascade.

It calls real agents (costs whatever those models cost) - run it when you have
the relevant logins. Scratch repos are created in a temp dir and removed after.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import config
from .brains import get_invoker
from .gates import run_gates

DEFAULT_TASK = (
    "Create a Python module `calc.py` with a function `add(a, b)` that returns "
    "a + b, plus a `tests/` folder with a pytest test `test_calc.py` asserting "
    "add(2, 3) == 5. Keep it minimal; it must pass `pytest -q`."
)

# The two configs we most want to compare (ADR-017 / roadmap H). jcode's model is
# its config default (pin a free OpenRouter slug there for a fair, free compare).
DEFAULT_CONFIGS: list[tuple[str, str | None]] = [
    (config.BRAIN_OPENCODE, config.OPENCODE_FREE_MODELS[0]),
    (config.BRAIN_JCODE, config.DEFAULT_MODELS.get(config.BRAIN_JCODE)),
]


@dataclass
class BenchResult:
    brain: str
    model: str
    status: str
    cost_usd: float
    duration_s: float
    gate_passed: bool | None      # None = gates not run (task did not produce ok)
    output_chars: int
    note: str = ""


def _scratch_repo() -> Path:
    """A throwaway git repo so the quality gates have something to run against."""
    d = Path(tempfile.mkdtemp(prefix="devteam-bench-"))
    for args in (["init", "-b", "main"], ["config", "user.email", "bench@local"],
                 ["config", "user.name", "bench"]):
        subprocess.run(["git", "-C", str(d), *args], capture_output=True)
    (d / "README.md").write_text("# bench scratch\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(d), "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", str(d), "commit", "-m", "seed"], capture_output=True)
    return d


def run_bench(task: str = DEFAULT_TASK,
              configs: list[tuple[str, str | None]] | None = None,
              timeout_s: int = 600, gate: bool = True) -> list[BenchResult]:
    """Run `task` on each (brain, model) config in its own scratch repo."""
    configs = configs or DEFAULT_CONFIGS
    results: list[BenchResult] = []
    for brain, model in configs:
        d = _scratch_repo()
        try:
            try:
                invoker = get_invoker(brain)
            except KeyError as e:
                results.append(BenchResult(brain, model or "default", "error",
                                           0.0, 0.0, None, 0, f"unknown brain: {e}"))
                continue
            res = invoker(task, d, timeout_s, model)
            gp: bool | None = None
            if gate and res.status == "ok":
                try:
                    gp = run_gates(d).passed
                except Exception:  # noqa: BLE001 - a gate crash must not kill the bench
                    gp = None
            results.append(BenchResult(brain, res.model or (model or "default"),
                                       res.status, res.cost_usd, res.duration_s,
                                       gp, len(res.output or "")))
        finally:
            shutil.rmtree(d, ignore_errors=True)
    return results


def format_report(results: list[BenchResult]) -> str:
    head = f"{'BRAIN':<10}{'MODEL':<40}{'STATUS':<10}{'GATE':<6}{'COST$':>9}{'SECS':>7}{'OUT':>7}"
    lines = [head]
    for r in results:
        gate = "-" if r.gate_passed is None else ("PASS" if r.gate_passed else "FAIL")
        lines.append(f"{r.brain:<10}{(r.model or 'default')[:39]:<40}{r.status:<10}"
                     f"{gate:<6}{r.cost_usd:>9.4f}{r.duration_s:>7.1f}{r.output_chars:>7}")
        if r.note:
            lines.append(f"  - {r.note}")
    return "\n".join(lines)
