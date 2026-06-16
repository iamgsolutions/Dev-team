"""Project state machine (S2).

State lives in <project>/.project-memory/project.json so it travels with the
project repo (memory handoff protocol). Transitions are validated against
config.TRANSITIONS; "paused" is an orthogonal flag the daemon must honor.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import config


class InvalidTransition(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Project:
    name: str
    path: Path
    state: str = "new"
    paused: bool = False
    phase_completed: bool = False   # current phase's task done, awaiting checkpoint
    budget_cap_usd: float = config.DEFAULT_BUDGET_CAP_USD
    spent_usd: float = 0.0
    discord_channel: str = ""   # e.g. "discord:123456" or "discord:123:thread456"
    last_discord_msg_id: str = ""   # listener cursor (no double-processing)
    repo: str = ""              # e.g. "iamgsolutions/notes"
    created: str = field(default_factory=_now)
    history: list[dict] = field(default_factory=list)

    # --- persistence ---------------------------------------------------------

    @property
    def memory_dir(self) -> Path:
        return self.path / config.PROJECT_MEMORY_DIR

    @property
    def json_path(self) -> Path:
        return self.memory_dir / "project.json"

    def save(self) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "name": self.name,
            "path": str(self.path),
            "state": self.state,
            "paused": self.paused,
            "phase_completed": self.phase_completed,
            "budget_cap_usd": self.budget_cap_usd,
            "spent_usd": round(self.spent_usd, 6),
            "discord_channel": self.discord_channel,
            "last_discord_msg_id": self.last_discord_msg_id,
            "repo": self.repo,
            "created": self.created,
            "history": self.history,
        }
        from .storage import atomic_write_json
        atomic_write_json(self.json_path, payload)

    @classmethod
    def load(cls, path: Path) -> "Project":
        data = json.loads((path / config.PROJECT_MEMORY_DIR / "project.json").read_text(encoding="utf-8"))
        return cls(
            name=data["name"],
            path=Path(data["path"]),
            state=data["state"],
            paused=data.get("paused", False),
            phase_completed=data.get("phase_completed", False),
            budget_cap_usd=data.get("budget_cap_usd", config.DEFAULT_BUDGET_CAP_USD),
            spent_usd=data.get("spent_usd", 0.0),
            discord_channel=data.get("discord_channel", ""),
            last_discord_msg_id=data.get("last_discord_msg_id", ""),
            repo=data.get("repo", ""),
            created=data.get("created", _now()),
            history=data.get("history", []),
        )

    # --- transitions ---------------------------------------------------------

    def transition(self, to_state: str, note: str = "") -> None:
        allowed = config.TRANSITIONS.get(self.state, [])
        if to_state not in allowed:
            raise InvalidTransition(
                f"{self.name}: cannot go {self.state!r} -> {to_state!r} (allowed: {allowed})"
            )
        self.history.append({"ts": _now(), "from": self.state, "to": to_state, "note": note})
        self.state = to_state
        self.phase_completed = False   # entering a fresh phase
        self.save()

    def pause(self, note: str = "") -> None:
        self.paused = True
        self.history.append({"ts": _now(), "event": "paused", "note": note})
        self.save()

    def resume(self, note: str = "") -> None:
        self.paused = False
        self.history.append({"ts": _now(), "event": "resumed", "note": note})
        self.save()

    def requires_human_checkpoint(self) -> str | None:
        """Return the approval description if current state needs human OK to leave."""
        return config.HUMAN_CHECKPOINTS.get(self.state)


# --- registry of all projects (engine-level index) ---------------------------

def registry_path() -> Path:
    return config.DATA_DIR / "registry.json"


def registry_load() -> dict:
    # safe load: a corrupt registry.json must NOT raise (it would paralyze the
    # whole daemon). load_json_safe quarantines the bad file and returns empty.
    from .storage import load_json_safe
    reg = load_json_safe(registry_path(), {"projects": {}})
    if not isinstance(reg, dict) or "projects" not in reg:
        return {"projects": {}}
    return reg


def registry_save(reg: dict) -> None:
    from .storage import atomic_write_json
    config.ensure_dirs()
    atomic_write_json(registry_path(), reg)


def registry_add(project: Project) -> None:
    reg = registry_load()
    reg["projects"][project.name] = str(project.path)
    registry_save(reg)


def registry_get(name: str) -> Project:
    reg = registry_load()
    if name not in reg["projects"]:
        raise KeyError(f"project {name!r} not in registry ({list(reg['projects'])})")
    return Project.load(Path(reg["projects"][name]))
