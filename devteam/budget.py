"""Budget tracker (S5) - the system's primary brake (spec R3/R4/R6).

Hard rules:
- charge() raises BudgetExceeded when the cap would be crossed -> caller must
  pause the project and notify the human.
- alert_due() flips once when crossing the 80% ratio -> caller notifies human.
- Free models cost 0 but are still recorded (visibility into volume).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config
from .state import Project


class BudgetExceeded(Exception):
    def __init__(self, project: str, spent: float, cap: float, attempted: float):
        self.project, self.spent, self.cap, self.attempted = project, spent, cap, attempted
        super().__init__(
            f"{project}: budget cap reached (${spent:.2f} + ${attempted:.2f} > ${cap:.2f})"
        )


@dataclass
class ChargeResult:
    spent_usd: float
    cap_usd: float
    ratio: float
    alert_80: bool  # True the first time we cross the alert threshold


def estimate_cost_usd(model: str | None, tokens_in: int, tokens_out: int) -> float:
    """Best-effort cost estimate from the static pricing table."""
    pricing = config.MODEL_PRICING.get(model or "", config.FALLBACK_PRICING)
    return (tokens_in * pricing[0] + tokens_out * pricing[1]) / 1_000_000.0


def estimate_tokens_from_text(text: str) -> int:
    """Rough heuristic: ~4 chars per token."""
    return max(1, len(text) // 4)


def charge(project: Project, cost_usd: float, note: str = "") -> ChargeResult:
    """Record spend on a project. Raises BudgetExceeded if cap crossed."""
    if cost_usd < 0:
        raise ValueError("cost cannot be negative")
    cap = project.budget_cap_usd
    before_ratio = project.spent_usd / cap if cap > 0 else 1.0
    new_spent = project.spent_usd + cost_usd
    if new_spent > cap:
        # do NOT record the charge; the work that caused it must not proceed
        raise BudgetExceeded(project.name, project.spent_usd, cap, cost_usd)
    project.spent_usd = new_spent
    project.history.append({"event": "charge", "usd": round(cost_usd, 6), "note": note})
    project.save()
    after_ratio = new_spent / cap if cap > 0 else 1.0
    crossed_alert = before_ratio < config.BUDGET_ALERT_RATIO <= after_ratio
    return ChargeResult(new_spent, cap, after_ratio, crossed_alert)


def remaining(project: Project) -> float:
    return max(0.0, project.budget_cap_usd - project.spent_usd)
