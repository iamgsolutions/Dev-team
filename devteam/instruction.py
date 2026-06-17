"""4-block instruction builder (S4a) - enforces ADR-015 memory handoff protocol.

Every instruction sent to ANY brain MUST contain the four blocks:
ORIENTATION (what to read first), TASK (what to do + acceptance criteria),
CONSTRAINTS (model/budget/forbidden/gates), CLOSE-OUT (which memory to update).

build() raises MalformedInstruction if any block is missing/empty - making it
*impossible* for the engine to emit a malformed instruction.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class MalformedInstruction(Exception):
    pass


PREAMBLE = (
    "You are a coding agent (role: {role}) operating in the MG system.\n"
    "You are STATELESS: everything you need is in the memory files, and everything\n"
    "you do must be written down before finishing. You follow the team's universal\n"
    "rules (mg-kb/build/05-agent-rules.md): do not go out of scope, do not expose\n"
    "secrets, code/commits in English, honesty if something does not work."
)


@dataclass
class Instruction:
    role: str
    # ORIENTATION
    read_first: list[str] = field(default_factory=list)   # ordered file paths
    current_state: str = ""
    # TASK
    task: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    expected_output: str = ""
    # CONSTRAINTS
    model_info: str = ""
    budget_note: str = ""
    forbidden: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)
    # CLOSE-OUT
    memory_updates: list[str] = field(default_factory=list)  # "file: what to record"
    # ROLE KNOWLEDGE (optional 5th block: role skill pack - senior craft injected)
    skills_pack: str = ""

    def build(self) -> str:
        missing = []
        if not self.read_first or not self.current_state:
            missing.append("ORIENTATION (read_first + current_state)")
        if not self.task or not self.acceptance_criteria:
            missing.append("TASK (task + acceptance_criteria)")
        if not self.model_info or not self.budget_note:
            missing.append("CONSTRAINTS (model_info + budget_note)")
        if not self.memory_updates:
            missing.append("CLOSE-OUT (memory_updates)")
        if missing:
            raise MalformedInstruction(
                "instruction is missing mandatory blocks: " + "; ".join(missing)
            )

        lines: list[str] = [PREAMBLE.format(role=self.role), ""]

        lines += ["== ORIENTATION ==", "Before doing anything, read in this order:"]
        lines += [f"  {i+1}. {p}" for i, p in enumerate(self.read_first)]
        lines += [f"Current state: {self.current_state}", ""]

        lines += ["== TASK ==", self.task, "Acceptance criteria:"]
        lines += [f"  - {c}" for c in self.acceptance_criteria]
        if self.expected_output:
            lines.append(f"Expected output: {self.expected_output}")
        lines.append("")

        lines += ["== CONSTRAINTS ==", f"Model/tier: {self.model_info}.", f"Budget: {self.budget_note}."]
        if self.forbidden:
            lines.append("Do NOT touch: " + "; ".join(self.forbidden) + ".")
        if self.gates:
            lines.append("Must pass: " + ", ".join(self.gates) + ".")
        lines.append("")

        if self.skills_pack:
            lines += ["== ROLE KNOWLEDGE (apply it, it is your quality standard) ==",
                      self.skills_pack, ""]

        lines += ["== CLOSE-OUT (MANDATORY before finishing) ==", "Before finishing, update:"]
        lines += [f"  - {m}" for m in self.memory_updates]
        lines += [
            "Leave a record of: what you did, decisions, pending items, doubts.",
            "If you do not update the memory, the task is NOT complete.",
        ]
        return "\n".join(lines)
