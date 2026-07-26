"""Unified outcome of processing one Telegram message.

A single discriminated shape keeps the Telegram layer's branching logic
simple: check `status`, then read only the fields relevant to that case.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.domain.enums import TaskStatus
from app.schemas.decision import DecisionSchema, TaskMatchCandidateSchema


class LogOutcome(BaseModel):
    status: Literal["committed", "pending_confirmation", "duplicate"]
    request_id: str

    # Populated when status == "committed"
    task_id: str | None = None
    task_title: str | None = None
    task_status: TaskStatus | None = None
    stakeholder: list[str] = []
    is_new_task: bool = False
    auto_applied: bool = False
    summary: str | None = None
    tags: list[str] = []
    log_id: str | None = None

    # Populated when status == "pending_confirmation"
    decision: DecisionSchema | None = None
    proposed_task_title: str | None = None
    proposed_stakeholder: list[str] = []
    proposed_status: TaskStatus | None = None
    candidates: list[TaskMatchCandidateSchema] = []
    confidence: float | None = None
