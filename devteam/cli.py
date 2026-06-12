"""devteam CLI - manual control surface (Hermes skills will call this too)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config
from .state import Project, registry_get, registry_load


def cmd_new_project(args) -> int:
    from .intake import new_project
    project, questions = new_project(
        Path(args.brief), name=args.name, cap=args.cap, discord_channel=args.discord or "",
    )
    print(f"project created: {project.name} at {project.path} [state={project.state}]")
    if questions:
        print("\nBRIEF INCOMPLETO - preguntas para el humano (enviar agrupadas al hilo):")
        for q in questions:
            print(f"  - {q}")
    return 0


def cmd_status(args) -> int:
    if args.name:
        p = registry_get(args.name)
        print(json.dumps({
            "name": p.name, "state": p.state, "paused": p.paused,
            "spent_usd": round(p.spent_usd, 4), "cap_usd": p.budget_cap_usd,
            "repo": p.repo, "path": str(p.path),
        }, indent=2, ensure_ascii=False))
    else:
        reg = registry_load()
        if not reg["projects"]:
            print("(no projects)")
        for name, path in reg["projects"].items():
            try:
                p = Project.load(Path(path))
                flag = " [PAUSED]" if p.paused else ""
                print(f"{name:<24} {p.state:<14} ${p.spent_usd:.2f}/${p.budget_cap_usd:.0f}{flag}")
            except Exception as e:  # noqa: BLE001
                print(f"{name:<24} (unreadable: {e})")
    return 0


def cmd_pause(args) -> int:
    p = registry_get(args.name)
    p.pause("pausado por el humano via CLI")
    print(f"{p.name} paused")
    return 0


def cmd_resume(args) -> int:
    p = registry_get(args.name)
    p.resume("reanudado por el humano via CLI")
    print(f"{p.name} resumed")
    return 0


def cmd_run_task(args) -> int:
    """Manual single-task execution (testing / Fase 1 acceptance)."""
    from .executor import execute_task
    p = registry_get(args.name)
    res = execute_task(
        project=p,
        role=args.role,
        task=args.task,
        acceptance_criteria=args.criteria or ["la tarea se completa según lo pedido"],
        critical=args.critical,
        timeout_s=args.timeout,
    )
    print(f"status={res.status} brain={res.brain} model={res.model} "
          f"cost=${res.cost_usd:.4f} branch={res.branch}")
    print(f"router: {res.justification}")
    print("--- output (first 2000 chars) ---")
    print(res.output[:2000])
    return 0 if res.status == "ok" else 1


def cmd_daemon(args) -> int:
    print("daemon: not implemented yet (M4 / Fase 2). See build/03-build-roadmap.md")
    return 2


def main(argv=None) -> int:
    config.ensure_dirs()
    ap = argparse.ArgumentParser(prog="devteam", description="MG 24/7 dev team engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new-project", help="create project from a markdown brief")
    p.add_argument("brief")
    p.add_argument("--name")
    p.add_argument("--cap", type=float)
    p.add_argument("--discord", help="discord target e.g. discord:123:thread456")
    p.set_defaults(fn=cmd_new_project)

    p = sub.add_parser("status", help="show project(s) status")
    p.add_argument("name", nargs="?")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("pause", help="pause a project")
    p.add_argument("name")
    p.set_defaults(fn=cmd_pause)

    p = sub.add_parser("resume", help="resume a project")
    p.add_argument("name")
    p.set_defaults(fn=cmd_resume)

    p = sub.add_parser("run-task", help="run a single task through the executor")
    p.add_argument("name")
    p.add_argument("--role", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--criteria", nargs="*")
    p.add_argument("--critical", action="store_true")
    p.add_argument("--timeout", type=int, default=1800)
    p.set_defaults(fn=cmd_run_task)

    p = sub.add_parser("daemon", help="24/7 loop (Fase 2)")
    p.set_defaults(fn=cmd_daemon)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
