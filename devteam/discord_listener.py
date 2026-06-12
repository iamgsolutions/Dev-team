"""Discord intervention listener - the human commands the team FROM the thread.

Polls the Discord REST API directly (no extra deps, no LLM, reuses the same
bot token the Hermes gateway already uses - read from Hermes' .env at runtime,
NEVER logged). The daemon calls check_interventions() each tick: new human
messages in a project's channel/thread are parsed for commands:

    aprobar | aprobado | approve | ok aprobado     -> approve checkpoint
    pausa | pausar | para | stop | pause           -> pause project
    reanuda | reanudar | continua | resume         -> resume project
    redirige: <texto> | director: <texto> | nota: <texto>
                                                   -> directive into NOTES.md

Design notes:
- Thread targets: in Discord's API a thread IS a channel id, so for
  "discord:chan:thread" we poll the thread id directly.
- Only non-bot authors are honored (the team's own reports are ignored).
- last seen message id is persisted per project -> no double-processing.
- Failures are soft: Discord being unreachable must never crash the daemon.
"""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from . import config

API = "https://discord.com/api/v10"
_token_cache: str | None = None


def _load_bot_token() -> str | None:
    """Read DISCORD_BOT_TOKEN from Hermes' .env (runtime only, never logged)."""
    global _token_cache
    if _token_cache:
        return _token_cache
    env_path = config.HERMES_EXE.parents[2] / ".env"   # ...\hermes\.env
    try:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"\s*DISCORD_BOT_TOKEN\s*=\s*(.+?)\s*$", line)
            if m:
                _token_cache = m.group(1).strip().strip('"').strip("'")
                return _token_cache
    except OSError:
        pass
    return None


def listener_available() -> bool:
    return _load_bot_token() is not None


def _channel_id_from_target(target: str) -> str | None:
    """'discord:123' -> '123' ; 'discord:123:456' -> '456' (thread IS a channel)."""
    if not target or not target.startswith("discord"):
        return None
    parts = target.split(":")
    if len(parts) >= 3 and parts[2]:
        return parts[2]
    if len(parts) >= 2 and parts[1] and not parts[1].startswith("#"):
        return parts[1]
    return None


def fetch_messages(channel_id: str, after: str | None = None, limit: int = 25) -> list[dict]:
    """GET recent messages. Returns oldest-first list of raw message dicts."""
    token = _load_bot_token()
    if not token:
        return []
    url = f"{API}/channels/{channel_id}/messages?limit={limit}"
    if after:
        url += f"&after={after}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {token}",
        "User-Agent": "mg-devteam-listener/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return list(reversed(data))  # API returns newest-first
    except Exception as e:  # noqa: BLE001 - listener must never crash the daemon
        print(f"[listener] fetch failed for {channel_id}: {type(e).__name__}")
        return []


# --- command parsing (pure, tested) ------------------------------------------

APPROVE_RE = re.compile(r"^\s*(aprobar|aprobado|aprueba|approve|ok,?\s*aprobado)\b", re.IGNORECASE)
PAUSE_RE = re.compile(r"^\s*(pausa(r)?|para|stop|pause|detén|deten)\b", re.IGNORECASE)
RESUME_RE = re.compile(r"^\s*(reanuda(r)?|contin[uú]a|resume|sigue)\b", re.IGNORECASE)
REDIRECT_RE = re.compile(r"^\s*(redirige|director|nota|directriz)\s*[::]\s*(.+)", re.IGNORECASE | re.DOTALL)


def parse_command(text: str) -> tuple[str, str] | None:
    """Return (command, arg) or None. Commands: approve|pause|resume|redirect."""
    if not text:
        return None
    if APPROVE_RE.match(text):
        return ("approve", "")
    if PAUSE_RE.match(text):
        return ("pause", "")
    if RESUME_RE.match(text):
        return ("resume", "")
    m = REDIRECT_RE.match(text)
    if m:
        return ("redirect", m.group(2).strip())
    return None


# --- intervention application ------------------------------------------------

def check_interventions(project) -> list[str]:
    """Poll the project's Discord target and apply any human commands.
    Returns a list of human-readable actions taken (empty = nothing new)."""
    channel_id = _channel_id_from_target(project.discord_channel)
    if not channel_id or not listener_available():
        return []

    msgs = fetch_messages(channel_id, after=getattr(project, "last_discord_msg_id", "") or None)
    if not msgs:
        return []

    actions: list[str] = []
    newest_id = msgs[-1]["id"]
    for msg in msgs:
        author = msg.get("author", {})
        if author.get("bot"):
            continue  # never obey our own reports
        cmd = parse_command(msg.get("content", ""))
        if not cmd:
            continue
        verb, arg = cmd
        actions.append(_apply(project, verb, arg, author.get("username", "humano")))

    project.last_discord_msg_id = newest_id
    project.save()
    return [a for a in actions if a]


def _apply(project, verb: str, arg: str, who: str) -> str:
    from .discord_bridge import send

    if verb == "pause":
        project.pause(f"pausado por {who} desde Discord")
        send(project.discord_channel, f"⏸ Proyecto **{project.name}** pausado por {who}.")
        return f"pause({project.name})"

    if verb == "resume":
        project.resume(f"reanudado por {who} desde Discord")
        send(project.discord_channel, f"▶ Proyecto **{project.name}** reanudado por {who}.")
        return f"resume({project.name})"

    if verb == "approve":
        from .pipeline import approve
        result = approve(project)   # approve() already reports the milestone
        return f"approve({project.name}) -> {result}"

    if verb == "redirect":
        notes = project.path / config.PROJECT_MEMORY_DIR / "NOTES.md"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        try:
            old = notes.read_text(encoding="utf-8") if notes.exists() else ""
            head, _, tail = old.partition("\n## ")
            entry = (f"\n## {ts} — DIRECTRIZ DEL HUMANO ({who}, via Discord)\n"
                     f"{arg}\n(Obligatoria para los siguientes agentes de este proyecto.)\n")
            notes.write_text(head + entry + (("\n## " + tail) if tail else ""), encoding="utf-8")
        except OSError as e:
            return f"redirect({project.name}) FAILED: {e}"
        send(project.discord_channel,
             f"📌 Directriz registrada para **{project.name}**: «{arg[:140]}» — los agentes la leerán en su próxima tarea.")
        return f"redirect({project.name})"

    return ""
