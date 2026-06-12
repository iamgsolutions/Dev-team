"""Brain invokers - common interface over the coding-agent CLIs.

Every invoker runs a headless CLI inside a working directory (usually a git
worktree) and returns a normalized BrainResult. Cost: parsed from the CLI
output when available (claude reports total_cost_usd; codex reports token
usage), otherwise estimated from text length and the static pricing table.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic

from .. import config
from ..budget import estimate_cost_usd, estimate_tokens_from_text


@dataclass
class BrainResult:
    status: str                 # ok | error | timeout
    output: str
    cost_usd: float
    model: str
    duration_s: float
    raw: dict | None = field(default=None, repr=False)


def run_cli(
    args: list[str],
    cwd: Path,
    timeout_s: int,
    input_text: str | None = None,
) -> tuple[int, str, str, float]:
    """Run a CLI; return (returncode, stdout, stderr, duration). -1 rc on timeout."""
    t0 = monotonic()
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            shell=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or "", monotonic() - t0
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return -1, out, err, monotonic() - t0
    except FileNotFoundError as e:
        return -2, "", f"CLI not found: {e}", monotonic() - t0


def estimate_fallback_cost(model_key: str, prompt: str, output: str) -> float:
    tin = estimate_tokens_from_text(prompt)
    tout = estimate_tokens_from_text(output)
    return estimate_cost_usd(model_key, tin, tout)


def get_invoker(brain: str):
    """Return the invoke() callable for a brain name."""
    from . import claude, codex, opencode

    table = {
        config.BRAIN_CLAUDE: claude.invoke,
        config.BRAIN_CODEX: codex.invoke,
        config.BRAIN_OPENCODE: opencode.invoke,
    }
    if brain not in table:
        raise KeyError(f"unknown brain {brain!r}")
    return table[brain]
