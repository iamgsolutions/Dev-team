"""Claude Code invoker: `claude -p <prompt> --output-format json`.

The JSON result includes `total_cost_usd` and `result` (final text). Post
June-15 billing, headless usage draws from the monthly automation credit -
the budget tracker records whatever the CLI reports.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import BrainResult, run_cli, estimate_fallback_cost


def invoke(prompt: str, cwd: Path, timeout_s: int = 1800, model: str | None = None) -> BrainResult:
    from .. import config

    # Default to the ration-friendly automation model (sonnet) unless the
    # caller explicitly escalates (e.g. opus for a hard architecture task).
    model = model or config.DEFAULT_MODELS[config.BRAIN_CLAUDE]
    # Prompt goes via STDIN: npm .cmd wrappers route args through cmd.exe,
    # which mangles multiline arguments (verified 2026-06-12). `claude -p`
    # reads the prompt from stdin when no positional prompt is given.
    #
    # --dangerously-skip-permissions: WITHOUT this, headless `claude -p` cannot
    # use file-writing tools (Write/Edit/Bash) - it just returns the deliverable
    # as TEXT and writes nothing to disk (estreno 2026-06-18: pm produced no PRD).
    # The agent runs in an ISOLATED git worktree (gates + audit + budget cap bound
    # the blast radius), so autonomous tool use is the intended mode - same as the
    # OpenCode/Codex workhorses, which are autonomous by default.
    args = ["claude", "-p", "--output-format", "json", "--dangerously-skip-permissions"]
    if model:
        args += ["--model", model]
    rc, out, err, dur = run_cli(args, cwd, timeout_s, input_text=prompt)

    if rc == -1:
        return BrainResult("timeout", out or err, 0.0, model or "claude-default", dur)
    if rc != 0 and not out.strip():
        return BrainResult("error", err.strip() or f"exit {rc}", 0.0, model or "claude-default", dur)

    text, cost, raw = out, None, None
    try:
        raw = json.loads(out)
        text = raw.get("result", out)
        cost = raw.get("total_cost_usd")
    except (json.JSONDecodeError, AttributeError):
        pass
    if cost is None:
        cost = estimate_fallback_cost("claude-default", prompt, text)
    status = "ok" if rc == 0 else "error"
    # Subscription guardian: surface provider limits so the executor can rest
    # this brain and defer the task to the next batch window.
    from ..subscription import looks_rate_limited
    if status != "ok" and looks_rate_limited(text + " " + err):
        status = "rate_limited"
    return BrainResult(status, text, float(cost), model or "claude-default", dur, raw)
