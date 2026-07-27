"""DailyLog domain entity.

Daily Logs are immutable historical records: the original message and
submission timestamp must never be modified after creation. Corrections
are represented by mutating only the *extracted* fields, never the
original message.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import ImpactLevel
from app.utils.time import utcnow_naive


@dataclass
class DailyLog:
    log_id: str
    task_id: str
    date: date
    original_message: str
    stakeholder: list[str]
    next_steps: str | None
    resources: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    impact: ImpactLevel = ImpactLevel.INFORMATIONAL
    timestamp: datetime = field(default_factory=utcnow_naive)
    request_id: str = ""
    # AI-organized, coherent restatement of original_message — for easy
    # future reference. original_message itself is never touched; this is
    # a separate, editable field (see LogService.edit_log_summary).
    log_summary: str = ""

    def __post_init__(self) -> None:
        if not self.original_message.strip():
            raise ValueError("original_message must not be empty")
