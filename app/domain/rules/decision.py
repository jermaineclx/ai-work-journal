"""The deterministic Decision Engine.

Given AI outputs (confidence + candidate matches), decides what the
application should actually do. This module contains zero LLM calls and
zero I/O — it is pure business logic and should be exhaustively unit
tested (see 02_ARCHITECTURE.md §5.5, §9 Service Responsibilities).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import DecisionAction
from app.domain.rules.confidence import ConfidenceTier, classify_confidence


@dataclass
class TaskMatchCandidate:
    task_id: str
    title: str
    similarity: float


@dataclass
class Decision:
    action: DecisionAction
    confidence: float
    tier: ConfidenceTier
    matched_task_id: str | None
    candidates: list[TaskMatchCandidate]
    reason: str


def decide(
    *,
    confidence: float,
    best_match: TaskMatchCandidate | None,
    candidates: list[TaskMatchCandidate],
    auto_apply_threshold: float,
    confirm_threshold: float,
) -> Decision:
    """Decide the next action for a processed Daily Log.

    Rules:
      * No candidate at all -> always require confirmation to create a
        new Task, regardless of extraction confidence, since creating a
        new persistent workstream is a higher-stakes action than
        appending to an existing one.
      * A best match exists -> the confidence tier determines whether the
        match is auto-applied, needs confirmation, or is too weak to
        trust (fall through to clarification/new-task suggestion).
    """
    tier = classify_confidence(
        confidence,
        auto_apply_threshold=auto_apply_threshold,
        confirm_threshold=confirm_threshold,
    )

    if best_match is None:
        if tier == ConfidenceTier.CLARIFY:
            return Decision(
                action=DecisionAction.ASK_CLARIFICATION,
                confidence=confidence,
                tier=tier,
                matched_task_id=None,
                candidates=candidates,
                reason="No matching task found and extraction confidence is low.",
            )
        return Decision(
            action=DecisionAction.CONFIRM_NEW_TASK,
            confidence=confidence,
            tier=tier,
            matched_task_id=None,
            candidates=candidates,
            reason="No existing task matched; proposing a new task for user confirmation.",
        )

    if tier == ConfidenceTier.AUTO_APPLY:
        return Decision(
            action=DecisionAction.AUTO_SAVE_EXISTING_TASK,
            confidence=confidence,
            tier=tier,
            matched_task_id=best_match.task_id,
            candidates=candidates,
            reason=f"High confidence match ({confidence:.0%}) to '{best_match.title}'.",
        )

    if tier == ConfidenceTier.CONFIRM:
        return Decision(
            action=DecisionAction.CONFIRM_EXISTING_TASK,
            confidence=confidence,
            tier=tier,
            matched_task_id=best_match.task_id,
            candidates=candidates,
            reason=f"Medium confidence match ({confidence:.0%}) to '{best_match.title}'.",
        )

    return Decision(
        action=DecisionAction.ASK_CLARIFICATION,
        confidence=confidence,
        tier=tier,
        matched_task_id=None,
        candidates=candidates,
        reason="Match confidence too low to trust; presenting candidates to the user.",
    )
