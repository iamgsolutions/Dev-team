"""4-block instruction builder (S4a) - enforces ADR-015 memory handoff protocol.

Every instruction sent to ANY brain MUST contain the four blocks:
ORIENTACION (what to read first), TAREA (what to do + acceptance criteria),
RESTRICCIONES (model/budget/forbidden/gates), CIERRE (which memory to update).

build() raises MalformedInstruction if any block is missing/empty - making it
*impossible* for the engine to emit a malformed instruction.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class MalformedInstruction(Exception):
    pass


PREAMBLE = (
    "Eres un agente de código (rol: {role}) operando en el sistema MG.\n"
    "Eres STATELESS: todo lo que necesitas está en los archivos de memoria, y todo\n"
    "lo que hagas debe quedar escrito antes de cerrar. Cumples las reglas universales\n"
    "del equipo (mg-kb/build/05-agent-rules.md): no salirte del alcance, no exponer\n"
    "secretos, código/commits en inglés, honestidad si algo no funciona."
)


@dataclass
class Instruction:
    role: str
    # ORIENTACION
    read_first: list[str] = field(default_factory=list)   # ordered file paths
    current_state: str = ""
    # TAREA
    task: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    expected_output: str = ""
    # RESTRICCIONES
    model_info: str = ""
    budget_note: str = ""
    forbidden: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)
    # CIERRE
    memory_updates: list[str] = field(default_factory=list)  # "file: what to record"
    # CONOCIMIENTO (optional 5th block: role skill pack - senior craft injected)
    skills_pack: str = ""

    def build(self) -> str:
        missing = []
        if not self.read_first or not self.current_state:
            missing.append("ORIENTACION (read_first + current_state)")
        if not self.task or not self.acceptance_criteria:
            missing.append("TAREA (task + acceptance_criteria)")
        if not self.model_info or not self.budget_note:
            missing.append("RESTRICCIONES (model_info + budget_note)")
        if not self.memory_updates:
            missing.append("CIERRE (memory_updates)")
        if missing:
            raise MalformedInstruction(
                "instruction is missing mandatory blocks: " + "; ".join(missing)
            )

        lines: list[str] = [PREAMBLE.format(role=self.role), ""]

        lines += ["== ORIENTACIÓN ==", "Antes de hacer nada, lee en este orden:"]
        lines += [f"  {i+1}. {p}" for i, p in enumerate(self.read_first)]
        lines += [f"Estado actual: {self.current_state}", ""]

        lines += ["== TAREA ==", self.task, "Criterios de aceptación:"]
        lines += [f"  - {c}" for c in self.acceptance_criteria]
        if self.expected_output:
            lines.append(f"Output esperado: {self.expected_output}")
        lines.append("")

        lines += ["== RESTRICCIONES ==", f"Modelo/tier: {self.model_info}.", f"Presupuesto: {self.budget_note}."]
        if self.forbidden:
            lines.append("NO toques: " + "; ".join(self.forbidden) + ".")
        if self.gates:
            lines.append("Debe pasar: " + ", ".join(self.gates) + ".")
        lines.append("")

        if self.skills_pack:
            lines += ["== CONOCIMIENTO DEL ROL (aplícalo, es tu estándar de calidad) ==",
                      self.skills_pack, ""]

        lines += ["== CIERRE (OBLIGATORIO antes de terminar) ==", "Antes de cerrar, actualiza:"]
        lines += [f"  - {m}" for m in self.memory_updates]
        lines += [
            "Deja constancia de: qué hiciste, decisiones, pendientes, dudas.",
            "Si no actualizas la memoria, la tarea NO está completa.",
        ]
        return "\n".join(lines)
