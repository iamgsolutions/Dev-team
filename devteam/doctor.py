"""System doctor - end-to-end health check of the harness (no token spend).

Verifies every connection the team depends on BEFORE work starts, so system
failures surface as a clear report instead of mid-task crashes (human's
mandate: "que el harness y las conexiones sean seguras, que no haya fallos
de sistema"). All checks are passive/cheap: no LLM calls.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import config


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def _run(args: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except FileNotFoundError as e:
        return -2, str(e)


def run_doctor() -> list[Check]:
    checks: list[Check] = []
    home = Path(os.environ.get("USERPROFILE", r"C:\Users\Administrator"))

    # 1. CLIs resolvable (the four brains + git)
    for cli in ("claude", "codex", "opencode", "gemini", "git"):
        path = config.resolve_cli(cli)
        ok = shutil.which(path) is not None or Path(path).exists()
        checks.append(Check(f"cli:{cli}", ok, path if ok else "NOT FOUND"))

    # 2. Cached credentials present (passive - no API calls)
    cred_files = {
        "auth:claude": home / ".claude" / ".credentials.json",
        "auth:codex": home / ".codex" / "auth.json",
        "auth:opencode": home / ".local" / "share" / "opencode" / "auth.json",
        "auth:gemini": home / ".gemini" / "oauth_creds.json",
    }
    for name, f in cred_files.items():
        checks.append(Check(name, f.exists(), str(f) if f.exists() else f"missing {f.name}"))

    # 3. Git remote reachability over SSH (cheap: ls-remote HEAD only)
    rc, out = _run(["git", "ls-remote", "--heads",
                    "git@github.com:iamgsolutions/Dev-team.git", "main"], timeout=25)
    checks.append(Check("github:ssh", rc == 0, out[:120]))

    # 4. Hermes gateway alive + hermes send available
    rc, out = _run([str(config.HERMES_EXE), "gateway", "status"], timeout=30)
    checks.append(Check("hermes:gateway", rc == 0 and "running" in out.lower(), out[:120]))

    # 5. Engine state integrity
    try:
        from .state import registry_load
        reg = registry_load()
        n = len(reg.get("projects", {}))
        checks.append(Check("engine:registry", True, f"{n} project(s)"))
    except (json.JSONDecodeError, OSError) as e:
        checks.append(Check("engine:registry", False, str(e)[:120]))

    # 6. Subscriptions / rations snapshot
    try:
        from .subscription import status as substatus
        s = substatus()
        parts = [f"{b}:{v['calls_today']}/{v['daily_budget']}" for b, v in s.items()]
        checks.append(Check("subs:rations", True, " ".join(parts)))
    except Exception as e:  # noqa: BLE001
        checks.append(Check("subs:rations", False, str(e)[:120]))

    # 7. Disk space (>10 GB free)
    try:
        free_gb = shutil.disk_usage("C:\\").free / 1e9
        checks.append(Check("disk:c", free_gb > 10, f"{free_gb:.0f} GB free"))
    except OSError as e:
        checks.append(Check("disk:c", False, str(e)))

    return checks


def format_report(checks: list[Check]) -> str:
    lines = []
    for c in checks:
        mark = "OK " if c.ok else "FAIL"
        lines.append(f"[{mark}] {c.name:<18} {c.detail}")
    bad = sum(1 for c in checks if not c.ok)
    lines.append("")
    lines.append("SISTEMA SANO - todo conectado" if bad == 0
                 else f"{bad} problema(s) - revisar antes de trabajar")
    return "\n".join(lines)
