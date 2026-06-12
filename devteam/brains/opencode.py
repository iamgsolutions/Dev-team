"""OpenCode invoker: `opencode run <prompt> --model <provider/model>`.

The workhorse (Tier 0/1). Free-first policy lives in the router; this invoker
detects rate-limit errors so the caller can walk the fallback chain.
"""
from __future__ import annotations

from pathlib import Path

from . import BrainResult, run_cli, estimate_fallback_cost
from .. import config

RATE_LIMIT_MARKERS = ("rate limit", "rate-limit", "429", "too many requests", "quota")


def invoke(prompt: str, cwd: Path, timeout_s: int = 1800, model: str | None = None) -> BrainResult:
    model = model or config.DEFAULT_MODELS[config.BRAIN_OPENCODE]
    args = ["opencode", "run", prompt, "--model", model]
    rc, out, err, dur = run_cli(args, cwd, timeout_s)

    if rc == -1:
        return BrainResult("timeout", out or err, 0.0, model, dur)

    blob = (out + "\n" + err).lower()
    if rc != 0 or not out.strip():
        status = "rate_limited" if any(m in blob for m in RATE_LIMIT_MARKERS) else "error"
        return BrainResult(status, (out or err).strip() or f"exit {rc}", 0.0, model, dur)

    cost = estimate_fallback_cost(model, prompt, out)
    return BrainResult("ok", out.strip(), cost, model, dur)


def invoke_with_fallback(prompt: str, cwd: Path, timeout_s: int = 1800,
                         model: str | None = None) -> BrainResult:
    """Try the requested model, then walk the free->cheap fallback chain on
    rate limits / errors (spec: 'respeta rate limits, escala cuando toque')."""
    from ..router import fallback_chain

    first = invoke(prompt, cwd, timeout_s, model)
    if first.status == "ok":
        return first
    last = first
    for fb in fallback_chain(model):
        res = invoke(prompt, cwd, timeout_s, fb)
        if res.status == "ok":
            return res
        last = res
    return last
