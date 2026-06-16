"""Reusable component catalog (S15) - the foundation of the Solution Architect
Agent pattern (ADR-010): the team's library of reusable pieces so a new project
reuses proven work instead of rebuilding it.

Each component records what it does, how to use it, what it depends on, where
its code lives, and which projects already use it. The Architect consults this
BEFORE designing (search by capability) and registers new reusable pieces it
produces. Over time, building a project becomes "assemble known pieces + build
only the gap" - the human's original vision ("crear un puzzle con cosas que ya
tenemos").
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import config


def _path() -> Path:
    # The catalog is DURABLE team IP (not per-run state), so it can be pointed
    # at a versioned/synced location via DEVTEAM_CATALOG. Defaults to data/.
    import os
    override = os.environ.get("DEVTEAM_CATALOG")
    return Path(override) if override else (config.DATA_DIR / "catalog.json")


def _load() -> dict:
    from .storage import load_json_safe
    d = load_json_safe(_path(), {"components": {}})
    d.setdefault("components", {})
    return d


def _save(d: dict) -> None:
    from .storage import atomic_write_json
    config.ensure_dirs()
    atomic_write_json(_path(), d)


def register(name: str, summary: str, capabilities: list[str] | None = None,
             inputs: list[str] | None = None, dependencies: list[str] | None = None,
             files: list[str] | None = None, origin_project: str = "",
             stack: str = "") -> dict:
    """Add or update a reusable component. Idempotent by name."""
    d = _load()
    existing = d["components"].get(name, {})
    comp = {
        "name": name,
        "summary": summary or existing.get("summary", ""),
        "capabilities": sorted(set((capabilities or []) + existing.get("capabilities", []))),
        "inputs": inputs if inputs is not None else existing.get("inputs", []),
        "dependencies": dependencies if dependencies is not None else existing.get("dependencies", []),
        "files": files if files is not None else existing.get("files", []),
        "stack": stack or existing.get("stack", ""),
        "origin_project": origin_project or existing.get("origin_project", ""),
        "used_in": existing.get("used_in", []),
        "created": existing.get("created",
                                datetime.now(timezone.utc).strftime("%Y-%m-%d")),
    }
    d["components"][name] = comp
    _save(d)
    return comp


def search(query: str) -> list[dict]:
    """Find components by capability / name / summary (case-insensitive)."""
    q = (query or "").lower().strip()
    if not q:
        return list(_load()["components"].values())
    out = []
    for comp in _load()["components"].values():
        hay = " ".join([comp["name"], comp["summary"],
                        " ".join(comp.get("capabilities", [])),
                        comp.get("stack", "")]).lower()
        if q in hay or any(q in c.lower() for c in comp.get("capabilities", [])):
            out.append(comp)
    return out


def get(name: str) -> dict | None:
    return _load()["components"].get(name)


def mark_used(name: str, project: str) -> None:
    d = _load()
    comp = d["components"].get(name)
    if comp and project and project not in comp["used_in"]:
        comp["used_in"].append(project)
        _save(d)


def all_components() -> list[dict]:
    return list(_load()["components"].values())


def format_report(query: str | None = None) -> str:
    comps = search(query) if query else all_components()
    if not comps:
        return ("catálogo vacío" if not query
                else f"sin componentes para «{query}»")
    lines = [f"CATÁLOGO DE COMPONENTES REUTILIZABLES ({len(comps)})"]
    for c in sorted(comps, key=lambda x: x["name"]):
        caps = ", ".join(c.get("capabilities", [])) or "—"
        used = f" · usado en {len(c['used_in'])}" if c.get("used_in") else ""
        lines.append(f"\n• {c['name']}  [{c.get('stack') or 'cualquier stack'}]{used}")
        lines.append(f"    {c['summary']}")
        lines.append(f"    capacidades: {caps}")
        if c.get("dependencies"):
            lines.append(f"    depende de: {', '.join(c['dependencies'])}")
    return "\n".join(lines)
