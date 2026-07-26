"""Confidence-based automation rules.

This is the deterministic bridge between probabilistic AI output and
application behaviour described in 02_ARCHITECTURE.md §5.5 and
03_IMPLEMENTATION.md §20. Thresholds are parameters (never hardcoded
inside prompts) so they can be tuned via configuration without touching
AI code.
"""

from __future__ import annotations

from enum import Enum


class ConfidenceTier(str, Enum):
    AUTO_APPLY = "auto_apply"
    CONFIRM = "confirm"
    CLARIFY = "clarify"


def classify_confidence(
    confidence: float,
    *,
    auto_apply_threshold: float,
    confirm_threshold: float,
) -> ConfidenceTier:
    """Map a raw confidence score to a behavioural tier.

    ``confidence`` must be in [0, 1]. ``auto_apply_threshold`` must be
    greater than ``confirm_threshold``.
    """
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence must be within [0, 1], got {confidence}")
    if auto_apply_threshold <= confirm_threshold:
        raise ValueError("auto_apply_threshold must be greater than confirm_threshold")

    if confidence >= auto_apply_threshold:
        return ConfidenceTier.AUTO_APPLY
    if confidence >= confirm_threshold:
        return ConfidenceTier.CONFIRM
    return ConfidenceTier.CLARIFY
