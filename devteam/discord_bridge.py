"""Discord bridge (S12a) - report via `hermes send` (no LLM, reuses gateway creds).

Target format (verified against hermes send --help):
  discord                      -> home channel
  discord:<chat_id>            -> channel
  discord:<chat_id>:<thread>   -> thread inside channel
  discord:#channel-name        -> by name
"""
from __future__ import annotations

import subprocess

from . import config


def send(target: str, message: str, subject: str | None = None, timeout_s: int = 60) -> bool:
    """Send a message. Returns True on success; never raises (reporting must
    not crash the pipeline - failures are logged to stdout instead)."""
    args = [str(config.HERMES_EXE), "send", "--to", target, "--quiet"]
    if subject:
        args += ["--subject", subject]
    args.append(message)
    try:
        proc = subprocess.run(args, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout_s)
        if proc.returncode != 0:
            print(f"[discord_bridge] send failed rc={proc.returncode}: {proc.stderr.strip()[:300]}")
            return False
        return True
    except Exception as e:  # noqa: BLE001 - reporting is best-effort by design
        print(f"[discord_bridge] send exception: {e}")
        return False


def milestone(project_discord: str, text: str) -> bool:
    """Hito → Discord (spec R12: solo hitos y bloqueos)."""
    return send(project_discord or "discord", text, subject="[hito]")


def blocker(project_discord: str, text: str) -> bool:
    return send(project_discord or "discord", text, subject="[BLOQUEO]")
