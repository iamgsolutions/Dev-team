"""Atomic, crash-safe JSON/text persistence + secret redaction.

Audit fix (2026-06-12): all state files (project.json, registry.json,
scorecard.json, subscription.json) were written with a bare write_text that
truncates-then-writes; a crash mid-write left them empty/corrupt and could
paralyze the daemon. atomic_write_* writes to a temp file, fsyncs, then
os.replace (atomic on Windows and POSIX). load_json_safe never raises on
corrupt JSON.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)   # atomic
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(Path(path), json.dumps(payload, indent=2, ensure_ascii=False))


def load_json_safe(path: Path, default: Any) -> Any:
    """Load JSON; on missing/corrupt file return default (never raises).
    Keeps a .corrupt copy of unparseable files for forensics."""
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        try:
            p.replace(p.with_suffix(p.suffix + ".corrupt"))
        except OSError:
            pass
        return default


# --- secret redaction (outbound: Discord / stdout / prompts) -----------------
# Reused by gates.py for scanning AND by reporters for redaction. Conservative
# but broader than the original scanner (audit gap: missed Discord/Google/
# Stripe/AWS-secret/generic-assignment tokens).
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{20,}",                       # OpenAI/Anthropic/OpenRouter
    r"sk-(?:ant|or)-[A-Za-z0-9_\-]{20,}",
    r"sk_(?:live|test)_[A-Za-z0-9]{16,}",            # Stripe secret
    r"rk_(?:live|test)_[A-Za-z0-9]{16,}",            # Stripe restricted
    r"ghp_[A-Za-z0-9]{30,}",                         # GitHub PAT
    r"github_pat_[A-Za-z0-9_]{30,}",                 # GitHub fine-grained
    r"gho_[A-Za-z0-9]{30,}",                         # GitHub OAuth
    r"xox[baprs]-[A-Za-z0-9\-]{10,}",                # Slack
    r"AKIA[0-9A-Z]{16}",                             # AWS access key id
    r"aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+]{40}",  # AWS secret
    r"AIza[0-9A-Za-z_\-]{35}",                       # Google API key
    r"[MNO][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27,}",    # Discord bot token
    r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",  # JWT
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"(?i)(?:secret|password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
    r"\s*[=:]\s*['\"][^'\"\s]{8,}['\"]",             # generic assignment
]
_COMPILED = [re.compile(p) for p in SECRET_PATTERNS]


def redact(text: str) -> str:
    """Replace anything that looks like a secret with [REDACTED]."""
    if not text:
        return text
    out = text
    for pat in _COMPILED:
        out = pat.sub("[REDACTED]", out)
    return out
