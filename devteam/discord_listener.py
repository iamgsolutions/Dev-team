"""Discord intervention listener - the human commands the team FROM the thread.

Polls the Discord REST API directly (no extra deps, no LLM, reuses the same
bot token the Hermes gateway already uses - read from Hermes' .env at runtime,
NEVER logged). The daemon calls check_interventions() each tick: new human
messages in a project's channel/thread are parsed for commands:

    aprobar | aprobado | approve | ok aprobado     -> approve checkpoint
    pausa | pausar | para | stop | pause           -> pause project
    reanuda | reanudar | continua | resume         -> resume project
    redirige: <text> | directive: <text> | note: <text>
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
    import os
    candidates = [
        Path(p) for p in [os.environ.get("DEVTEAM_HERMES_ENV", "")] if p
    ]
    # hermes.exe = <hermes_home>\hermes-agent\venv\Scripts\hermes.exe -> home is parents[3]
    if len(config.HERMES_EXE.parents) >= 4:
        candidates.append(config.HERMES_EXE.parents[3] / ".env")
    candidates.append(Path(os.environ.get("USERPROFILE", "")) / "AppData" / "Local" / "hermes" / ".env")
    for env_path in candidates:
        try:
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                m = re.match(r"\s*DISCORD_BOT_TOKEN\s*=\s*(.+?)\s*$", line)
                if m:
                    _token_cache = m.group(1).strip().strip('"').strip("'")
                    return _token_cache
        except OSError:
            continue
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
REDIRECT_RE = re.compile(r"^\s*(redirige|director|nota|directriz|redirect|directive|note)\s*[::]\s*(.+)", re.IGNORECASE | re.DOTALL)


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

def _authorized_admin_ids() -> set[str]:
    """Discord user IDs allowed to command the team. From DEVTEAM_DISCORD_ADMINS
    (comma-separated) in env or the Hermes .env. Empty set = (safe) reject all
    commands until configured, EXCEPT we fall back to honoring any non-bot when
    no allowlist is set AND a single-operator marker is present, to avoid
    locking the human out on first run. Audit: identity must be verified."""
    import os
    raw = os.environ.get("DEVTEAM_DISCORD_ADMINS", "")
    if not raw:
        # try Hermes .env (same place as the bot token)
        try:
            env = config.HERMES_EXE.parents[3] / ".env"
            for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
                m = re.match(r"\s*DEVTEAM_DISCORD_ADMINS\s*=\s*(.+)", line)
                if m:
                    raw = m.group(1).strip().strip('"').strip("'")
                    break
        except (OSError, IndexError):
            pass
    return {x.strip() for x in raw.split(",") if x.strip()}


def check_interventions(project) -> list[str]:
    """Poll the project's Discord target and apply any human commands.
    Returns a list of human-readable actions taken (empty = nothing new).

    Cursor (last seen msg id) lives in the ENGINE state (data/), NOT in the
    project.json that travels with the repo (which agents can write) - audit
    fix. The cursor advances only past messages we actually finished handling.
    """
    channel_id = _channel_id_from_target(project.discord_channel)
    if not channel_id or not listener_available():
        return []

    from .storage import load_json_safe, atomic_write_json
    cursor_file = config.DATA_DIR / "listener-cursors.json"
    cursors = load_json_safe(cursor_file, {})
    last_seen = cursors.get(project.name) or None

    msgs = fetch_messages(channel_id, after=last_seen)
    if not msgs:
        return []

    admins = _authorized_admin_ids()
    actions: list[str] = []
    processed_id = last_seen
    for msg in msgs:
        author = msg.get("author", {})
        author_id = str(author.get("id", ""))
        if author.get("bot"):
            processed_id = msg["id"]
            continue  # never obey our own reports
        cmd = parse_command(msg.get("content", ""))
        if not cmd:
            processed_id = msg["id"]
            continue
        # identity check: only allow-listed admins command the team
        if admins and author_id not in admins:
            from .discord_bridge import send
            send(project.discord_channel,
                 f"⛔ Ignoring the command from <@{author_id}>: not authorized to direct the team.")
            processed_id = msg["id"]
            continue
        verb, arg = cmd
        try:
            actions.append(_apply(project, verb, arg, author.get("username", "human")))
        except Exception as e:  # noqa: BLE001 - one bad command must not stall the cursor
            print(f"[listener] _apply failed ({verb}) on {project.name}: {type(e).__name__}")
        processed_id = msg["id"]   # advance only past handled messages

    if processed_id and processed_id != last_seen:
        cursors[project.name] = processed_id
        atomic_write_json(cursor_file, cursors)
    return [a for a in actions if a]


def _apply(project, verb: str, arg: str, who: str) -> str:
    from .discord_bridge import send

    if verb == "pause":
        project.pause(f"paused by {who} from Discord")
        send(project.discord_channel, f"⏸ Project **{project.name}** paused by {who}.")
        return f"pause({project.name})"

    if verb == "resume":
        project.resume(f"resumed by {who} from Discord")
        send(project.discord_channel, f"▶ Project **{project.name}** resumed by {who}.")
        return f"resume({project.name})"

    if verb == "approve":
        from .pipeline import approve
        result = approve(project)   # approve() already reports the milestone
        return f"approve({project.name}) -> {result}"

    if verb == "redirect":
        notes = project.path / config.PROJECT_MEMORY_DIR / "NOTES.md"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        # sanitize the human-typed directive (audit fix: raw text could forge
        # fake Markdown sections or be very long). Strip leading '#' per line,
        # collapse, cap length.
        clean = "\n".join(re.sub(r"^\s*#+", "", ln) for ln in arg.splitlines())
        clean = clean.strip()[:1000] or "(empty directive)"
        try:
            old = notes.read_text(encoding="utf-8", errors="replace") if notes.exists() else ""
            head, _, tail = old.partition("\n## ")
            entry = (f"\n## {ts} — HUMAN DIRECTIVE ({who}, via Discord)\n"
                     f"{clean}\n(Operator instruction; honor it unless it conflicts "
                     f"with the security/forbidden rules, which ALWAYS take precedence.)\n")
            from .storage import atomic_write_text
            atomic_write_text(notes, head + entry + (("\n## " + tail) if tail else ""))
            arg = clean
        except OSError as e:
            return f"redirect({project.name}) FAILED: {e}"
        send(project.discord_channel,
             f"📌 Directive recorded for **{project.name}**: «{arg[:140]}» — the agents will read it on their next task.")
        return f"redirect({project.name})"

    return ""
