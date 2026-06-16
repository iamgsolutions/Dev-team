"""Codex invoker: `codex exec <prompt> --json`.

stdout is a JSONL event stream; the final agent message is the last
`item.completed` with item.type == agent_message (schema may evolve - we parse
defensively and fall back to raw text). Known Windows quirk: may flash a
helper PowerShell window (upstream issue #20510) - cosmetic, not blocking.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import BrainResult, run_cli, estimate_fallback_cost


def invoke(prompt: str, cwd: Path, timeout_s: int = 1800, model: str | None = None) -> BrainResult:
    # Prompt via STDIN ("-" placeholder): cmd.exe wrappers mangle multiline args.
    # --skip-git-repo-check: the engine controls the cwd (always an isolated
    # worktree), so codex's own trusted-dir check is redundant here.
    args = ["codex", "exec", "--json", "--skip-git-repo-check"]
    if model:
        args += ["--model", model]
    args.append("-")
    rc, out, err, dur = run_cli(args, cwd, timeout_s, input_text=prompt)

    if rc == -1:
        return BrainResult("timeout", out or err, 0.0, model or "codex-default", dur)
    if rc != 0 and not out.strip():
        return BrainResult("error", err.strip() or f"exit {rc}", 0.0, model or "codex-default", dur)

    text, tokens_in, tokens_out = "", 0, 0
    events = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append(ev)
        # token usage events (defensive: several historical shapes + values)
        usage = ev.get("usage") or (ev.get("msg") or {}).get("usage") or {}
        try:
            tokens_in += int(float(usage.get("input_tokens", 0) or 0))
            tokens_out += int(float(usage.get("output_tokens", 0) or 0))
        except (ValueError, TypeError):
            pass   # malformed usage on one line must not crash the whole parse
        # final agent message (several historical shapes)
        item = ev.get("item") or {}
        if item.get("type") in ("agent_message", "assistant_message"):
            text = item.get("text") or item.get("content") or text
        if ev.get("type") in ("agent_message", "task_complete") and ev.get("message"):
            text = ev["message"]

    if not text:
        text = out  # fall back to the raw stream

    if tokens_in or tokens_out:
        from ..budget import estimate_cost_usd
        cost = estimate_cost_usd("codex-default", tokens_in, tokens_out)
    else:
        cost = estimate_fallback_cost("codex-default", prompt, text)

    status = "ok" if rc == 0 else "error"
    from ..subscription import looks_rate_limited
    if status != "ok" and looks_rate_limited(text + " " + err):
        status = "rate_limited"
    return BrainResult(status, text, cost, model or "codex-default", dur, {"events": len(events)})
