"""Task domain entity.

Deliberately a plain dataclass (no Pydantic, no ORM) so the domain layer
stays independent of any framework. Google Sheets is just where a Task
happens to be persisted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import TaskStatus
from app.utils.time import utcnow_naive


@dataclass
class Task:
    task_id: str
    title: str
    stakeholder: str
    status: TaskStatus
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow_naive)
    updated_at: datetime = field(default_factory=utcnow_naive)
    total_updates: int = 0

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Task title must not be empty")
        if not isinstance(self.status, TaskStatus):
            self.status = TaskStatus(self.status)

    def apply_update(self, *, status: TaskStatus | None, new_tags: list[str], new_resources: list[str]) -> None:
        """Merge in the effects of a new confirmed Daily Log."""
        if status is not None:
            self.status = status
        for tag in new_tags:
            if tag not in self.tags:
                self.tags.append(tag)
        for resource in new_resources:
            if resource not in self.resources:
                self.resources.append(resource)
        self.total_updates += 1
        self.updated_at = utcnow_naive()
