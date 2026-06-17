"""Task executor - the spine that ties everything together (S3+S4+S5+ADR-015).

execute_task() is the ONLY path through which a brain touches a project:
  1. route the task to a brain/model (budget-aware)
  2. build the 4-block instruction (raises if malformed)
  3. create an isolated worktree for the task branch
  4. snapshot memory mtimes, invoke the brain
  5. verify the memory handoff (retry with explicit warning if violated)
  6. charge the budget (BudgetExceeded pauses the project upstream)
  7. commit worktree work; merge is the pipeline's job after gates/audit
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import budget, config, worktree
from .brains import BrainResult, get_invoker
from .brains.opencode import invoke_with_fallback
from .instruction import Instruction
from .memory import (memory_paths_for_instruction, memory_update_spec,
                     read_state, snapshot_mtimes, verify_handoff)
from .router import Route, route
from .state import Project


@dataclass
class TaskResult:
    status: str            # ok | error | timeout | deferred | handoff_violated | budget_paused
    brain: str
    model: str
    cost_usd: float
    output: str
    branch: str | None
    justification: str
    worktree: str | None = None   # path of the task worktree (for gates/audit)


def execute_task(
    project: Project,
    role: str,
    task: str,
    acceptance_criteria: list[str],
    critical: bool = False,
    forbidden: list[str] | None = None,
    gates: list[str] | None = None,
    author_brain: str | None = None,
    timeout_s: int = 1800,
    expected_output: str = "",
) -> TaskResult:
    if project.paused:
        return TaskResult("budget_paused", "", "", 0.0, "project is paused", None, "paused")

    from . import subscription

    rt: Route = route(
        role=role,
        critical=critical,
        budget_remaining_usd=budget.remaining(project),
        author_brain=author_brain,
        claude_available=subscription.available(config.BRAIN_CLAUDE),
        codex_available=subscription.available(config.BRAIN_CODEX),
        gemini_available=subscription.available(config.BRAIN_GEMINI),
    )
    if rt.brain == "defer":
        # Premium ration spent / cooling down -> task waits for the next batch
        # window (human's policy: better batched than degraded or drained).
        return TaskResult("deferred", "", "", 0.0,
                          "premium brains resting; task will retry on a later batch",
                          None, rt.justification)

    state_summary = read_state(project.path)
    # STATE.md uses the English header "## Current state" (new projects); legacy
    # adopted projects may still carry the Spanish "## Estado actual" - accept both.
    _state_section = re.split(r"##\s*(?:Current state|Estado actual)", state_summary, maxsplit=1)[-1]
    current_state = (_state_section.split("##", 1)[0].strip()
                     or f"phase {project.state}")[:600]

    instr = Instruction(
        role=role,
        read_first=memory_paths_for_instruction(project.path) + ["./BRIEF.md"],
        current_state=current_state,
        task=task,
        acceptance_criteria=acceptance_criteria,
        expected_output=expected_output,
        model_info=f"{rt.brain} / {rt.model or 'default'} ({rt.justification})",
        budget_note=(f"restante ${budget.remaining(project):.2f} de "
                     f"${project.budget_cap_usd:.2f}; no lo superes"),
        forbidden=forbidden or ["la configuración del sistema", "otros proyectos",
                                "credenciales y secretos"],
        gates=gates or ["el código debe ejecutar sin errores"],
        memory_updates=memory_update_spec(),
    )
    # pre-installed role knowledge (skill pack) - senior craft for every agent,
    # tailored to the project type (web/api/mobile)
    from .skillpack import load_for_role
    instr.skills_pack = load_for_role(role, getattr(project, "project_type", None))
    prompt = instr.build()  # raises MalformedInstruction if blocks missing

    wt_path, branch = worktree.create(project.path, f"{role}-{task[:30]}")
    try:
        # snapshot the WORKTREE memory BEFORE invoking - the agent works in the
        # worktree, not the main checkout. (audit fix: was snapshotted after
        # _invoke, forcing a redundant retry on every successful task.)
        wt_before = snapshot_mtimes(wt_path)
        result = _invoke(rt, prompt, wt_path, timeout_s)
        if rt.brain in subscription.GUARDED_BRAINS:
            subscription.record_call(rt.brain)
            if result.status == "rate_limited":
                # Rest the brain and defer - the daemon retries in a later batch.
                subscription.report_rate_limit(rt.brain)
                return TaskResult("deferred", rt.brain, result.model, 0.0,
                                  "provider reported a usage limit; brain resting, task deferred",
                                  branch, rt.justification)

        # memory handoff enforcement (one retry with explicit warning)
        handoff_ok = verify_handoff(wt_path, wt_before)
        if result.status == "ok" and not handoff_ok:
            warn = (prompt + "\n\nWARNING: in your previous run you did NOT update the memory "
                    "files (.project-memory/STATE.md and NOTES.md). Do it NOW: record what "
                    "you did, decisions and pending items. Without this the task is INCOMPLETE.")
            retry = _invoke(rt, warn, wt_path, timeout_s // 2)
            result.cost_usd += retry.cost_usd
            handoff_ok = verify_handoff(wt_path, wt_before)
            if not handoff_ok:
                result = BrainResult("handoff_violated", result.output, result.cost_usd,
                                     result.model, result.duration_s)

        try:
            chg = budget.charge(project, result.cost_usd,
                                note=f"{role}: {task[:60]} [{result.model}]")
            if chg.alert_80:
                from .discord_bridge import blocker
                blocker(project.discord_channel,
                        f"Proyecto {project.name}: presupuesto al "
                        f"{chg.ratio*100:.0f}% (${chg.spent_usd:.2f}/${chg.cap_usd:.2f}).")
        except budget.BudgetExceeded as e:
            project.pause(str(e))
            from .discord_bridge import blocker
            blocker(project.discord_channel,
                    f"Proyecto {project.name} PAUSADO por presupuesto: {e}")
            return TaskResult("budget_paused", rt.brain, result.model, 0.0,
                              result.output, branch, rt.justification)

        if result.status == "ok":
            worktree.commit_all(wt_path, f"feat({role}): {worktree.slugify(task)[:40]}",
                                model=result.model, role=role)

        # model accountability: every outcome feeds the scorecard (S14)
        from . import reflective
        reflective.record(result.model, rt.brain, result.status, note=f"{role}: {task[:50]}")

        from . import eventlog
        eventlog.record("task", project.name, role=role, brain=rt.brain,
                        model=result.model, status=result.status,
                        cost=round(result.cost_usd, 4))

        return TaskResult(result.status, rt.brain, result.model, result.cost_usd,
                          result.output, branch, rt.justification, str(wt_path))
    finally:
        # worktree stays for inspection/merge; pipeline removes it after merge
        pass


def _invoke(rt: Route, prompt: str, cwd, timeout_s: int) -> BrainResult:
    if rt.brain == config.BRAIN_OPENCODE:
        return invoke_with_fallback(prompt, cwd, timeout_s, rt.model)
    return get_invoker(rt.brain)(prompt, cwd, timeout_s, rt.model)
