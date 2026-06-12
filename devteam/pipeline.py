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

    # ERROR-CORRECTION CASCADE (human's mandate: "cuando haya errores que
    # primero traten de solucionarlos ellos, si no que suban a Hermes").
    # Attempt 1 runs the phase task; if gates/audit fail, the agent gets the
    # exact failure feedback and fixes its OWN work in the same worktree.
    # Only after MAX_TASK_RETRIES does the blocker escalate to Hermes/human.
    from pathlib import Path as _P
    from . import config as _cfg
    from . import reflective
    from .gates import run_gates
    from .audit import audit_worktree

    result: TaskResult | None = None
    failure_feedback = ""
    for attempt in range(1, _cfg.MAX_TASK_RETRIES + 1):
        task_text = spec.task if not failure_feedback else (
            spec.task
            + f"\n\nCORRECCIÓN (intento {attempt}): tu trabajo anterior en este mismo "
              f"worktree NO pasó el control de calidad. Arregla EXACTAMENTE esto y "
              f"no rompas lo que ya funciona:\n{failure_feedback[:1500]}"
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
                                "aplazada: cerebros premium descansando (ración/límite); se reintentará en la siguiente tanda")
        if result.status != "ok":
            failure_feedback = f"la ejecución falló ({result.status}): {result.output[:600]}"
            continue  # self-heal: retry (executor's fallback already tried other models)

        # QUALITY GATES before merge (spec R5: nada avanza sin pasar gates)
        if result.worktree:
            report = run_gates(_P(result.worktree))
            if not report.passed:
                reflective.record(result.model, result.brain, "gate_failed",
                                  note=f"{phase}: {report.summary()[:60]}")
                failing = "; ".join(f"{c.name}: {c.output[-400:]}" for c in report.checks
                                    if not c.passed and not c.skipped)
                failure_feedback = f"GATES fallidos — {report.summary()}. Detalle: {failing}"
                continue  # self-heal: agent fixes its own gate failures

            # MULTI-MODEL AUDIT for code phases (spec R5). PM/Architect output
            # is audited by the HUMAN checkpoint instead.
            if phase in ("backend", "frontend"):
                verdict = audit_worktree(_P(result.worktree), author_model=result.model,
                                         context=f"fase {phase} del proyecto {project.name}",
                                         critical=spec.critical)
                if not verdict.approved:
                    reflective.record(result.model, result.brain, "audit_rejected",
                                      note=f"{phase}")
                    failure_feedback = ("AUDITORÍA rechazada. Hallazgos de los auditores:\n"
                                        + verdict.details[:1200])
                    continue  # self-heal: agent fixes audited findings

        break  # ok + gates + audit -> done
    else:
        # cascade exhausted -> escalate to Hermes/human (Discord blocker)
        blocker(project.discord_channel,
                f"Proyecto {project.name} · fase {phase}: agotados {_cfg.MAX_TASK_RETRIES} "
                f"intentos de autocorrección. Último fallo: {failure_feedback[:400]} "
                f"Trabajo en rama {result.branch if result else '?'} sin mergear. Necesito dirección.")
        return PhaseOutcome(phase, result, None, None,
                            f"cascada agotada tras {_cfg.MAX_TASK_RETRIES} intentos: {failure_feedback[:300]}")

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
