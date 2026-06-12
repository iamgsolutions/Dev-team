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


def cmd_adopt(args) -> int:
    from .adopt import adopt_project
    p = adopt_project(Path(args.path), name=args.name, cap=args.cap,
                      discord_channel=args.discord or "", initial_state=args.state)
    print(f"adopted: {p.name} at {p.path} [state={p.state}] cap=${p.budget_cap_usd:.0f}")
    print("primera misión sugerida: devteam run-phase", p.name, "(QA audita lo existente)")
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


def cmd_run_phase(args) -> int:
    """Execute the current phase's macro-task (M4 sequential pipeline)."""
    from .pipeline import run_phase
    p = registry_get(args.name)
    out = run_phase(p)
    print(f"phase={out.phase} advanced_to={out.advanced_to} "
          f"waiting_human={out.waiting_human!r} note={out.note!r}")
    if out.result:
        print(f"task: status={out.result.status} brain={out.result.brain} "
              f"model={out.result.model} cost=${out.result.cost_usd:.4f}")
    return 0 if (out.advanced_to or out.waiting_human) else 1


def cmd_approve(args) -> int:
    """Human approves the pending checkpoint (PRD / architecture / delivery)."""
    from .pipeline import approve
    p = registry_get(args.name)
    print(approve(p))
    return 0


def cmd_subs(args) -> int:
    """Subscription guardian status / tuning."""
    from . import subscription
    if args.set:
        brain, calls = args.set
        subscription.set_daily_budget(brain, int(calls))
        print(f"{brain}: daily budget set to {calls} calls")
    if args.wake:
        subscription.clear_cooldown(args.wake)
        print(f"{args.wake}: cooldown cleared")
    print(json.dumps(subscription.status(), indent=2))
    return 0


def cmd_scorecard(args) -> int:
    """Model accountability report (who works well, who fails)."""
    from .reflective import format_report, bench, unbench
    if args.bench:
        bench(args.bench); print(f"benched: {args.bench}")
    if args.unbench:
        unbench(args.unbench); print(f"unbenched: {args.unbench}")
    print(format_report())
    return 0


def cmd_doctor(args) -> int:
    """Full harness health check (no token spend)."""
    from .doctor import run_doctor, format_report
    checks = run_doctor()
    print(format_report(checks))
    return 0 if all(c.ok for c in checks) else 1


def cmd_tick(args) -> int:
    """Run a single daemon step (useful for cron/testing)."""
    from .daemon import tick
    r = tick()
    print(f"acted_on={r.acted_on} note={r.note!r}")
    return 0


def cmd_daemon(args) -> int:
    from .daemon import loop
    loop(interval_s=args.interval)
    return 0


def main(argv=None) -> int:
    # Windows consoles default to cp1252; tool outputs may carry unicode.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    config.ensure_dirs()
    ap = argparse.ArgumentParser(prog="devteam", description="MG 24/7 dev team engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new-project", help="create project from a markdown brief")
    p.add_argument("brief")
    p.add_argument("--name")
    p.add_argument("--cap", type=float)
    p.add_argument("--discord", help="discord target e.g. discord:123:thread456")
    p.set_defaults(fn=cmd_new_project)

    p = sub.add_parser("adopt", help="adopt an EXISTING repo into the system")
    p.add_argument("path")
    p.add_argument("--name")
    p.add_argument("--cap", type=float)
    p.add_argument("--discord")
    p.add_argument("--state", default="qa", help="initial state (default qa: audit first)")
    p.set_defaults(fn=cmd_adopt)

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

    p = sub.add_parser("run-phase", help="execute the current phase macro-task")
    p.add_argument("name")
    p.set_defaults(fn=cmd_run_phase)

    p = sub.add_parser("approve", help="approve pending human checkpoint")
    p.add_argument("name")
    p.set_defaults(fn=cmd_approve)

    p = sub.add_parser("subs", help="subscription guardian: show or tune premium rations")
    p.add_argument("--set", nargs=2, metavar=("BRAIN", "CALLS"),
                   help="set daily call budget, e.g. --set claude 10")
    p.add_argument("--wake", metavar="BRAIN", help="clear cooldown for a brain")
    p.set_defaults(fn=cmd_subs)

    p = sub.add_parser("scorecard", help="model accountability report")
    p.add_argument("--bench", help="send a model to the bench (excluded from fallback)")
    p.add_argument("--unbench", help="bring a model back from the bench")
    p.set_defaults(fn=cmd_scorecard)

    p = sub.add_parser("doctor", help="harness health check (no token spend)")
    p.set_defaults(fn=cmd_doctor)

    p = sub.add_parser("tick", help="run one daemon step")
    p.set_defaults(fn=cmd_tick)

    p = sub.add_parser("daemon", help="24/7 loop")
    p.add_argument("--interval", type=int, default=60)
    p.set_defaults(fn=cmd_daemon)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
