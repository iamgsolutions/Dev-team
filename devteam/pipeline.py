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
        return PhaseOutcome(project.state, None, None, None, "proyecto pausado")

    phase = project.state
    if project.phase_completed and project.requires_human_checkpoint():
        return PhaseOutcome(phase, None, None, project.requires_human_checkpoint(),
                            "fase ya completada; esperando aprobación humana")
    if phase == "clarification":
        return PhaseOutcome(phase, None, None,
                            "responder a las preguntas de clarificación en el hilo",
                            "esperando respuestas del humano al brief")
    if phase not in PHASE_TASKS:
        return PhaseOutcome(phase, None, None, None,
                            f"fase {phase!r} no ejecutable por el pipeline (deploy/review/done: M6)")

    spec = PHASE_TASKS[phase](project)
    result = execute_task(
        project=project,
        role=spec.role,
        task=spec.task,
        acceptance_criteria=spec.acceptance_criteria,
        critical=spec.critical,
        forbidden=spec.forbidden,
        gates=spec.gates,
        expected_output=spec.expected_output,
    )

    if result.status == "deferred":
        # Premium brains resting (subscription guardian) - NOT an error.
        # The daemon retries on a later batch; no human action needed.
        return PhaseOutcome(phase, result, None, None,
                            "aplazada: cerebros premium descansando (ración/límite); se reintentará en la siguiente tanda")

    if result.status != "ok":
        blocker(project.discord_channel,
                f"Proyecto {project.name} · fase {phase}: tarea fallida ({result.status}). "
                f"Cerebro {result.brain}/{result.model}.")
        return PhaseOutcome(phase, result, None, None, f"tarea fallida: {result.status}")

    # QUALITY GATES before merge (spec R5: nada avanza sin pasar gates)
    if result.worktree:
        from .gates import run_gates
        from pathlib import Path as _P
        report = run_gates(_P(result.worktree))
        if not report.passed:
            blocker(project.discord_channel,
                    f"Proyecto {project.name} · fase {phase}: GATES fallidos — {report.summary()}. "
                    f"El trabajo queda en la rama {result.branch} sin mergear.")
            return PhaseOutcome(phase, result, None, None, f"gates fallidos: {report.summary()}")

    # merge the phase branch into main (gates passed)
    if result.branch:
        try:
            worktree.merge_branch(project.path, result.branch,
                                  f"merge({phase}): {result.branch}")
        except worktree.GitError as e:
            return PhaseOutcome(phase, result, None, None, f"merge falló: {e}")

    checkpoint = project.requires_human_checkpoint()
    if checkpoint:
        project.phase_completed = True
        project.save()
        milestone(project.discord_channel,
                  f"Proyecto {project.name}: fase **{phase}** completada. "
                  f"CHECKPOINT: {checkpoint}. Usa `devteam approve {project.name}` (o di 'aprobado' en el hilo).")
        return PhaseOutcome(phase, result, None, checkpoint)

    nxt = _next_state(project)
    project.transition(nxt, f"fase {phase} completada (auto)")
    milestone(project.discord_channel,
              f"Proyecto {project.name}: fase **{phase}** completada → **{nxt}**. "
              f"Gasto: ${project.spent_usd:.2f}/${project.budget_cap_usd:.0f}.")
    return PhaseOutcome(phase, result, nxt, None)


def approve(project: Project) -> str:
    """Human approves the pending checkpoint -> advance to next phase."""
    checkpoint = project.requires_human_checkpoint()
    if not checkpoint:
        return f"{project.name}: no hay checkpoint pendiente en fase {project.state}"
    if project.state == "review":
        project.transition("done", "entrega aceptada por el humano")
        milestone(project.discord_channel, f"Proyecto {project.name}: ACEPTADO y terminado. ✔")
        return f"{project.name}: done"
    nxt = _next_state(project)
    project.transition(nxt, f"checkpoint aprobado por el humano: {checkpoint}")
    milestone(project.discord_channel,
              f"Proyecto {project.name}: checkpoint aprobado → fase **{nxt}**.")
    return f"{project.name}: {nxt}"


def _next_state(project: Project) -> str:
    from . import config
    allowed = config.TRANSITIONS[project.state]
    # sequential default: first allowed forward state
    return allowed[0]
