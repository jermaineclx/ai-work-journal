"""Storage/transport representation of a Decision Engine outcome.

The domain `Decision` dataclass (app.domain.rules.decision) stays a plain
dataclass with zero serialization concerns; this Pydantic mirror is what
gets persisted as a pending confirmation and rendered by the Telegram
layer.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import DecisionAction
from app.domain.rules.confidence import ConfidenceTier
from app.domain.rules.decision import Decision


class TaskMatchCandidateSchema(BaseModel):
    task_id: str
    title: str
    similarity: float


class DecisionSchema(BaseModel):
    action: DecisionAction
    confidence: float
    tier: ConfidenceTier
    matched_task_id: str | None
    candidates: list[TaskMatchCandidateSchema]
    reason: str


def decision_to_schema(decision: Decision) -> DecisionSchema:
    return DecisionSchema(
        action=decision.action,
        confidence=decision.confidence,
        tier=decision.tier,
        matched_task_id=decision.matched_task_id,
        candidates=[
            TaskMatchCandidateSchema(task_id=c.task_id, title=c.title, similarity=c.similarity)
            for c in decision.candidates
        ],
        reason=decision.reason,
    )
