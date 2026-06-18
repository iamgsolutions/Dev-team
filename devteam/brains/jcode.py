"""jcode invoker - a fast, low-RAM Rust coding-agent harness as a brain.

Why it's here (evaluated 2026-06): jcode (github.com/1jehuang/jcode, MIT) is a
multi-provider coding agent that claims ~6x less RAM and far faster startup than
Claude Code, with a built-in semantic memory system. It is multi-provider
(OpenRouter, Claude, Codex, Gemini, Ollama, ...), so it can run our free
OpenRouter models with much less overhead - ideal for many PARALLEL workers
(roadmap A) and aligned with the semantic-memory goal (roadmap G).

Status: integrated and callable, but NOT routed to by default yet - it must be
benchmarked against OpenCode on real tasks (roadmap H) before becoming a default
workhorse. Use via the `jcode-free` preset or by pinning brain="jcode".

Headless: `jcode run --json --quiet --no-update -p <provider> -C <cwd> <message>`.
Native .exe (not an npm wrapper), so multiline argv is safe. Telemetry disabled
via JCODE_NO_TELEMETRY=1.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import BrainResult, run_cli, estimate_fallback_cost
from .. import config


def _jcode_exe() -> str:
    override = os.environ.get("DEVTEAM_JCODE")
    if override and Path(override).exists():
        return override
    cand = Path.home() / "dev" / "tools" / "jcode.exe"
    if cand.exists():
        return str(cand)
    return config.resolve_cli("jcode")


def invoke(prompt: str, cwd: Path, timeout_s: int = 1800, model: str | None = None) -> BrainResult:
    os.environ.setdefault("JCODE_NO_TELEMETRY", "1")
    model = model or config.DEFAULT_MODELS.get(config.BRAIN_JCODE)
    # provider defaults to openrouter (our free/cheap tier); model is the openrouter id.
    args = [_jcode_exe(), "run", "--json", "--quiet", "--no-update", "-p", "openrouter", "-C", str(cwd)]
    if model:
        args += ["-m", model]
    args.append(prompt)
    rc, out, err, dur = run_cli(args, cwd, timeout_s)

    if rc == -1:
        return BrainResult("timeout", out or err, 0.0, model or "jcode", dur)

    blob = (out + " " + err).lower()
    if rc != 0 and not out.strip():
        from ..subscription import looks_rate_limited
        status = "rate_limited" if looks_rate_limited(blob) else "error"
        return BrainResult(status, (out or err).strip()[:2000] or f"exit {rc}", 0.0, model or "jcode", dur)

    text, cost = out, None
    try:
        data = json.loads(out)
        text = data.get("result") or data.get("text") or data.get("message") or out
        # explicit None check: a reported cost of 0.0 (free model) must NOT be
        # discarded by an `or` chain and replaced with an estimate.
        cost = data.get("cost_usd")
        if cost is None:
            cost = data.get("total_cost_usd")
    except (json.JSONDecodeError, AttributeError):
        pass
    if cost is None:
        cost = estimate_fallback_cost(model or "", prompt, text)
    return BrainResult("ok", text.strip() if isinstance(text, str) else str(text),
                       float(cost), model or "jcode", dur)
