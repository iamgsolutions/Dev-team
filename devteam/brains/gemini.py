"""Gemini CLI invoker - 4th brain (Google AI Pro subscription).

Role in the team: diverse auditor for critical work (saves the codex ration)
and premium-lite fallback when claude/codex are resting. Huge context window
makes it ideal for whole-repo analysis.

Auth: interactive `gemini` login once (Login with Google, Pro account);
headless runs reuse the cached credential. Prompt goes via STDIN (multiline-
safe through npm .cmd wrappers); output is plain text on stdout.
"""
from __future__ import annotations

from pathlib import Path

from . import BrainResult, run_cli, estimate_fallback_cost


def invoke(prompt: str, cwd: Path, timeout_s: int = 1800, model: str | None = None) -> BrainResult:
    args = ["gemini"]
    if model:
        args += ["-m", model]
    rc, out, err, dur = run_cli(args, cwd, timeout_s, input_text=prompt)

    if rc == -1:
        return BrainResult("timeout", out or err, 0.0, model or "gemini-default", dur)

    text = (out or "").strip()
    if rc != 0 or not text:
        from ..subscription import looks_rate_limited
        blob = (out + " " + err)
        status = "rate_limited" if looks_rate_limited(blob) else "error"
        return BrainResult(status, blob.strip()[:2000] or f"exit {rc}",
                           0.0, model or "gemini-default", dur)

    cost = estimate_fallback_cost("gemini-default", prompt, text)
    return BrainResult("ok", text, cost, model or "gemini-default", dur)
