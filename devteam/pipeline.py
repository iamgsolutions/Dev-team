"""Pipeline runner (S6) - strict sequential phases with human checkpoints.

M4 v1: run_phase() executes the current phase's macro-task and advances the
state machine. Human checkpoints (after pm / architect / review) block
advancement until approve() is called (CLI now; Discord approval when the
daemon lands). Merging task branches happens after gates+audit (M5) - for now
work stays on its task branch and is merged manually or by approve.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import worktree
from .discord_bridge import blocker, milestone
from .executor import TaskResult, execute_task
from .roles import PHASE_TASKS
from .state import Project
from .storage import redact
from . import eventlog

NEXT_AFTER_QA_OK = "deploy"


@dataclass
class PhaseOutcome:
    phase: str
    result: TaskResult | None
    advanced_to: str | None
    waiting_human: str | None   # checkpoint description if blocked on approval
    note: str = ""


def run_phase(project: Project) -> PhaseOutcome:
    """Execute the macro-task of the CURRENT phase. Does not skip checkpoints."""
    if project.paused:
        return PhaseOutcome(project.state, None, None, None, "project paused")

    phase = project.state
    if project.phase_completed and project.requires_human_checkpoint():
        return PhaseOutcome(phase, None, None, project.requires_human_checkpoint(),
                            "phase already completed; waiting for human approval")
    if phase == "clarification":
        return PhaseOutcome(phase, None, None,
                            "answer the clarification questions in the thread",
                            "waiting for the human's answers to the brief")
    # 'review' = human acceptance gate (no agent task): present it once and wait
    if phase == "review":
        project.phase_completed = True
        project.save()
        milestone(project.discord_channel,
                  f"Project {project.name}: READY for your acceptance. Review the delivery "
                  f"(demo + report) and type `approved` in the thread to close it, or "
                  f"`directive:` with changes.")
        return PhaseOutcome(phase, None, None, "Delivery accepted by the human",
                            "waiting for final human acceptance")
    if phase not in PHASE_TASKS:
        return PhaseOutcome(phase, None, None, None,
                            f"phase {phase!r} not executable by the pipeline")

    spec = PHASE_TASKS[phase](project)

    # ERROR-CORRECTION CASCADE (human's mandate: when errors happen, the agents
    # should first try to fix them themselves, and only escalate to Hermes if
    # they can't). Attempt 1 runs the phase task; if gates/audit fail, the agent
    # gets the exact failure feedback and fixes its OWN work in the same
    # worktree. Only after MAX_TASK_RETRIES does the blocker escalate to
    # Hermes/human.
    from pathlib import Path as _P
    from . import config as _cfg
    from . import reflective
    from .gates import run_gates
    from .audit import audit_worktree

    result: TaskResult | None = None
    failure_feedback = ""
    max_attempts = max(1, _cfg.MAX_TASK_RETRIES)   # never silently disable execution
    for attempt in range(1, max_attempts + 1):
        task_text = spec.task if not failure_feedback else (
            spec.task
            + f"\n\nCORRECTION (attempt {attempt}): your previous work in this same "
              f"worktree did NOT pass quality control. Fix EXACTLY this and do not "
              f"break what already works:\n{failure_feedback[:1500]}"
        )
        result = execute_task(
            project=project,
            role=spec.role,
            task=task_text,
            acceptance_criteria=spec.acceptance_criteria,
            critical=spec.critical,
            forbidden=spec.forbidden,
            gates=spec.gates,
            expected_output=spec.expected_output,
        )

        if result.status == "deferred":
            return PhaseOutcome(phase, result, None, None,
                                "deferred: premium brains resting (ration/limit); will retry on the next batch")
        if result.status != "ok":
            failure_feedback = f"execution failed ({result.status}): {result.output[:600]}"
            continue  # self-heal: retry (executor's fallback already tried other models)

        # OUTPUT VERIFICATION (estreno 2026-06-18): a brain can return "ok" yet
        # write NOTHING - an empty worktree would otherwise pass the gates (nothing
        # to lint/test) and an empty-diff audit (nothing to review), advancing the
        # project with no deliverable. Verify the phase actually produced its files.
        if result.worktree:
            wt = _P(result.worktree)
            missing = [f for f in (spec.expected_files or []) if not (wt / f).exists()]
            no_changes = phase in ("backend", "frontend") and not worktree.has_changes_vs_base(wt)
            if missing or no_changes:
                problem = (f"missing required file(s): {', '.join(missing)}" if missing
                           else "you produced no changes at all")
                reflective.record(result.model, result.brain, "output_missing",
                                  note=f"{phase}: {problem[:60]}")
                eventlog.record("output_check", project.name, phase=phase, problem=problem[:120])
                failure_feedback = (f"you returned success but {problem}. Actually WRITE the "
                                    "deliverable(s) to disk with real content this time - do not "
                                    "just describe them in your reply.")
                continue  # self-heal: the agent writes the files this time

        # QUALITY GATES before merge (spec R5: nothing advances without passing gates)
        if result.worktree:
            report = run_gates(_P(result.worktree))
            eventlog.record("gate", project.name, phase=phase,
                            passed=report.passed, summary=report.summary()[:120])
            if not report.passed:
                reflective.record(result.model, result.brain, "gate_failed",
                                  note=f"{phase}: {report.summary()[:60]}")
                failing = "; ".join(f"{c.name}: {c.output[-400:]}" for c in report.checks
                                    if not c.passed and not c.skipped)
                failure_feedback = f"GATES failed — {report.summary()}. Detail: {failing}"
                continue  # self-heal: agent fixes its own gate failures

            # MULTI-MODEL AUDIT for code phases (spec R5). PM/Architect output
            # is audited by the HUMAN checkpoint instead.
            if phase in ("backend", "frontend"):
                verdict = audit_worktree(_P(result.worktree), author_model=result.model,
                                         context=f"phase {phase} of project {project.name}",
                                         critical=spec.critical)
                eventlog.record("audit", project.name, phase=phase,
                                approved=verdict.approved, voters=len(verdict.votes))
                if not verdict.approved:
                    reflective.record(result.model, result.brain, "audit_rejected",
                                      note=f"{phase}")
                    failure_feedback = ("AUDIT rejected. Findings from the auditors:\n"
                                        + verdict.details[:1200])
                    continue  # self-heal: agent fixes audited findings

        break  # ok + gates + audit -> done
    else:
        # cascade exhausted -> PAUSE the project and escalate (audit fix: not
        # pausing left the project actionable, so the daemon re-ran the failing
        # phase every tick forever, draining budget and premium rations).
        project.pause(f"cascade exhausted in phase {phase} after {_cfg.MAX_TASK_RETRIES} attempts")
        eventlog.record("escalate", project.name, phase=phase, reason="cascade_exhausted")
        blocker(project.discord_channel,
                f"Project {project.name} · phase {phase}: exhausted {_cfg.MAX_TASK_RETRIES} "
                f"self-correction attempts → project PAUSED. Last failure: "
                f"{redact(failure_feedback[:400])} Work on branch "
                f"{result.branch if result else '?'} not merged. Resume with `resume` "
                f"or give a `directive:` in the thread when you redirect it.")
        return PhaseOutcome(phase, result, None, None,
                            f"cascade exhausted after {_cfg.MAX_TASK_RETRIES} attempts (project paused): "
                            f"{failure_feedback[:300]}")

    # merge the phase branch into main (gates passed), then REMOVE the worktree
    # (audit fix: worktrees were never cleaned -> a QA bounce-back reused a stale
    # already-merged worktree, and they piled up on disk). After removal, a
    # re-run of the same phase gets a fresh worktree off current main.
    if result.branch:
        try:
            worktree.merge_branch(project.path, result.branch,
                                  f"merge({phase}): {result.branch}")
        except worktree.GitError as e:
            return PhaseOutcome(phase, result, None, None, f"merge failed: {e}")
        if result.worktree:
            try:
                worktree.remove(project.path, _P(result.worktree), force=True)
            except worktree.GitError:
                pass   # cleanup is best-effort; never block on it
        worktree.delete_branch(project.path, result.branch)  # allow same-name re-run

    checkpoint = project.requires_human_checkpoint()
    if checkpoint:
        project.phase_completed = True
        project.save()
        milestone(project.discord_channel,
                  f"Project {project.name}: phase **{phase}** completed. "
                  f"CHECKPOINT: {checkpoint}. Use `devteam approve {project.name}` (or say 'approved' in the thread).")
        return PhaseOutcome(phase, result, None, checkpoint)

    nxt = _next_state(project)
    project.transition(nxt, f"phase {phase} completed (auto)")
    eventlog.record("phase", project.name, **{"from": phase, "to": nxt,
                    "spent": round(project.spent_usd, 2)})
    milestone(project.discord_channel,
              f"Project {project.name}: phase **{phase}** completed → **{nxt}**. "
              f"Spend: ${project.spent_usd:.2f}/${project.budget_cap_usd:.0f}.")
    return PhaseOutcome(phase, result, nxt, None)


def approve(project: Project) -> str:
    """Human approves the pending checkpoint -> advance to next phase."""
    checkpoint = project.requires_human_checkpoint()
    if not checkpoint:
        return f"{project.name}: no pending checkpoint in phase {project.state}"
    if project.state == "review":
        project.transition("done", "delivery accepted by the human")
        milestone(project.discord_channel, f"Project {project.name}: ACCEPTED and finished. ✔")
        return f"{project.name}: done"
    nxt = _next_state(project)
    project.transition(nxt, f"checkpoint approved by the human: {checkpoint}")
    milestone(project.discord_channel,
              f"Project {project.name}: checkpoint approved → phase **{nxt}**.")
    return f"{project.name}: {nxt}"


def _next_state(project: Project) -> str:
    from . import config
    allowed = config.TRANSITIONS[project.state]
    # sequential default: first allowed forward state
    return allowed[0]
