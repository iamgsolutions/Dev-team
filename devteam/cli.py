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
        print("\nINCOMPLETE BRIEF - questions for the human (send them grouped to the thread):")
        for q in questions:
            print(f"  - {q}")
    return 0


def cmd_adopt(args) -> int:
    from .adopt import adopt_project
    p = adopt_project(Path(args.path), name=args.name, cap=args.cap,
                      discord_channel=args.discord or "", initial_state=args.state)
    print(f"adopted: {p.name} at {p.path} [state={p.state}] cap=${p.budget_cap_usd:.0f}")
    print("suggested first mission: devteam run-phase", p.name, "(QA audits what exists)")
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
    p.pause("paused by the human via CLI")
    print(f"{p.name} paused")
    return 0


def cmd_resume(args) -> int:
    p = registry_get(args.name)
    p.resume("resumed by the human via CLI")
    print(f"{p.name} resumed")
    return 0


def cmd_run_task(args) -> int:
    """Manual single-task execution (testing / Phase 1 acceptance)."""
    from .executor import execute_task
    p = registry_get(args.name)
    res = execute_task(
        project=p,
        role=args.role,
        task=args.task,
        acceptance_criteria=args.criteria or ["the task is completed as requested"],
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


def cmd_learn(args) -> int:
    """Teach a role a lesson (learning loop: failure -> permanent craft)."""
    from .skillpack import append_lesson
    f = append_lesson(args.role, args.lesson)
    print(f"lesson added to role {args.role}: {f}")
    return 0


def cmd_skills(args) -> int:
    from .skillpack import available_skills, ROLE_SKILLS, load_for_role
    if args.role:
        print(load_for_role(args.role))
    else:
        print("available skills:", ", ".join(available_skills()))
        print("\nrole -> skills mapping:")
        for role, names in ROLE_SKILLS.items():
            print(f"  {role:<10} {', '.join(names)}")
    return 0


def cmd_catalog(args) -> int:
    from . import catalog
    if args.add:
        comp = catalog.register(
            name=args.add, summary=args.summary or "",
            capabilities=(args.caps or "").split(",") if args.caps else [],
            stack=args.stack or "", origin_project=args.origin or "")
        print(f"registered: {comp['name']}")
    elif args.use:
        catalog.mark_used(args.use, args.project or "")
        print(f"marked used: {args.use} in {args.project}")
    else:
        print(catalog.format_report(args.search))
    return 0


def cmd_log(args) -> int:
    from . import eventlog
    print(eventlog.format_tail(args.n, args.project))
    return 0


def cmd_presets(args) -> int:
    from . import presets
    if args.role:
        ps = presets.by_role(args.role)
        for p in ps:
            print(f"{p.name:<20}{p.brain:<10}{p.model or 'default':<42}{','.join(p.mcps)}")
        if not ps:
            print(f"(no presets for role {args.role})")
    else:
        print(presets.format_report())
    return 0


def cmd_panel(args) -> int:
    """One-screen control panel for the director/human."""
    from .state import Project, registry_load
    from .subscription import status as substatus
    from . import reflective

    print("=" * 64)
    print(" DEV TEAM CONTROL PANEL — MG Solutions")
    print("=" * 64)

    reg = registry_load()
    print("\nPROJECTS")
    if not reg["projects"]:
        print("  (none)")
    for name, path in reg["projects"].items():
        try:
            p = Project.load(Path(path))
            flag = " [PAUSED]" if p.paused else ""
            wait = " ⏳waiting-OK" if (p.phase_completed and p.requires_human_checkpoint()) else ""
            pct = (p.spent_usd / p.budget_cap_usd * 100) if p.budget_cap_usd else 0
            print(f"  {name:<20} {p.state:<13} {p.project_type:<7} "
                  f"${p.spent_usd:.2f}/${p.budget_cap_usd:.0f} ({pct:.0f}%){flag}{wait}")
        except Exception as e:  # noqa: BLE001
            print(f"  {name:<20} (unreadable: {e})")

    print("\nPREMIUM RATIONS (today)")
    for brain, v in substatus().items():
        rest = "" if v["available"] else (" COOLING-DOWN" if v["cooling_down"] else " RATION EXHAUSTED")
        print(f"  {brain:<8} {v['calls_today']}/{v['daily_budget']} calls{rest}")

    print("\nMODEL SCORECARD")
    print("  " + reflective.format_report().replace("\n", "\n  "))

    from . import catalog
    n_comp = len(catalog.all_components())
    print(f"\nREUSABLE CATALOG: {n_comp} component(s)  ·  recent EVENTS: `devteam log`")

    print("\nSYSTEM HEALTH")
    from .doctor import run_doctor
    checks = run_doctor()
    bad = [c for c in checks if not c.ok]
    print(f"  {len(checks)-len(bad)}/{len(checks)} OK" +
          ("" if not bad else "  ·  ISSUES: " + ", ".join(c.name for c in bad)))
    print("=" * 64)
    return 0


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

    p = sub.add_parser("learn", help="teach a role a lesson (learning loop)")
    p.add_argument("--role", required=True)
    p.add_argument("lesson")
    p.set_defaults(fn=cmd_learn)

    p = sub.add_parser("skills", help="list skills / show a role's pack")
    p.add_argument("--role")
    p.set_defaults(fn=cmd_skills)

    p = sub.add_parser("catalog", help="reusable component catalog (SAA / ADR-010)")
    p.add_argument("--search", help="find components by capability/name")
    p.add_argument("--add", help="register a component by name")
    p.add_argument("--summary"); p.add_argument("--caps", help="comma-separated capabilities")
    p.add_argument("--stack"); p.add_argument("--origin", help="origin project")
    p.add_argument("--use", help="mark a component used"); p.add_argument("--project")
    p.set_defaults(fn=cmd_catalog)

    p = sub.add_parser("log", help="engine event log (flight recorder)")
    p.add_argument("-n", type=int, default=40)
    p.add_argument("--project")
    p.set_defaults(fn=cmd_log)

    p = sub.add_parser("presets", help="ready-made agent presets (role+brain+model+skills+mcps)")
    p.add_argument("--role", help="filter by role")
    p.set_defaults(fn=cmd_presets)

    p = sub.add_parser("panel", help="one-screen control panel")
    p.set_defaults(fn=cmd_panel)

    p = sub.add_parser("tick", help="run one daemon step")
    p.set_defaults(fn=cmd_tick)

    p = sub.add_parser("daemon", help="24/7 loop")
    p.add_argument("--interval", type=int, default=60)
    p.set_defaults(fn=cmd_daemon)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
