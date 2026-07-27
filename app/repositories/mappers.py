"""Conversions between domain entities and Google Sheets rows.

Kept separate from the repositories themselves so the "row shape" concept
is easy to find and change in one place (03_IMPLEMENTATION.md §14, Row
Mapping: "the rest of the application should never know row indices").
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.domain.entities import DailyLog, Task
from app.domain.enums import ImpactLevel, Priority, TaskStatus
from app.utils.time import utcnow_naive

_TAG_SEP = ", "
_RESOURCE_SEP = " | "
_STAKEHOLDER_SEP = ", "

# Status was previously a 7-value set (Not Started/In Progress/Waiting
# Feedback/Waiting QA/Blocked/Ready for Deployment/Completed) before this
# user's fixed 3-value dropdown (In Progress/Completed/KIV). Rows already
# in the sheet with an old value must still load rather than crash.
_LEGACY_STATUS_MAP = {
    "Not Started": TaskStatus.KIV,
    "Waiting Feedback": TaskStatus.KIV,
    "Waiting QA": TaskStatus.KIV,
    "Blocked": TaskStatus.KIV,
    "Ready for Deployment": TaskStatus.KIV,
}


def _parse_status(value: str) -> TaskStatus:
    try:
        return TaskStatus(value)
    except ValueError:
        return _LEGACY_STATUS_MAP.get(value, TaskStatus.IN_PROGRESS)


def _parse_priority(value: Any) -> Priority | None:
    return Priority.parse(str(value)) if value else None


def _join(values: list[str], sep: str) -> str:
    return sep.join(v for v in values if v)


def _split(value: str, sep: str) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(sep) if v.strip()]


def task_to_row(task: Task) -> dict[str, Any]:
    return {
        "Task ID": task.task_id,
        "Task Name": task.title,
        "Stakeholder": _join(task.stakeholder, _STAKEHOLDER_SEP),
        "Status": task.status.value,
        "Tags": _join(task.tags, _TAG_SEP),
        "Resources": _join(task.resources, _RESOURCE_SEP),
        "Date Created": task.created_at.date().isoformat(),
        "Last Updated": task.updated_at.date().isoformat(),
        "Total Updates": task.total_updates,
        "Summary": task.summary,
        "Priority": task.priority.value if task.priority else "",
    }


def row_to_task(record: dict[str, Any]) -> Task:
    return Task(
        task_id=str(record["Task ID"]),
        title=str(record["Task Name"]),
        stakeholder=_split(str(record.get("Stakeholder", "")), _STAKEHOLDER_SEP),
        status=_parse_status(record.get("Status") or TaskStatus.IN_PROGRESS.value),
        summary=str(record.get("Summary", "")),
        tags=_split(str(record.get("Tags", "")), _TAG_SEP),
        resources=_split(str(record.get("Resources", "")), _RESOURCE_SEP),
        created_at=_parse_date(record.get("Date Created")),
        updated_at=_parse_date(record.get("Last Updated")),
        total_updates=int(record.get("Total Updates") or 0),
        priority=_parse_priority(record.get("Priority")),
    )


def daily_log_to_row(log: DailyLog) -> dict[str, Any]:
    return {
        "Log ID": log.log_id,
        "Date": log.date.isoformat(),
        "Task ID": log.task_id,
        "Original Message": log.original_message,
        "Stakeholder": _join(log.stakeholder, _STAKEHOLDER_SEP),
        "Status": log.status.value if log.status else "",
        "Next Steps": log.next_steps or "",
        "Resources": _join(log.resources, _RESOURCE_SEP),
        "Tags": _join(log.tags, _TAG_SEP),
        "Impact": log.impact.value,
        "Timestamp": log.timestamp.isoformat(),
    }


def row_to_daily_log(record: dict[str, Any]) -> DailyLog:
    status_value = record.get("Status")
    return DailyLog(
        log_id=str(record["Log ID"]),
        task_id=str(record["Task ID"]),
        date=_parse_date(record.get("Date")).date(),
        original_message=str(record["Original Message"]),
        stakeholder=_split(str(record.get("Stakeholder", "")), _STAKEHOLDER_SEP),
        status=_parse_status(status_value) if status_value else None,
        next_steps=str(record.get("Next Steps") or "") or None,
        resources=_split(str(record.get("Resources", "")), _RESOURCE_SEP),
        tags=_split(str(record.get("Tags", "")), _TAG_SEP),
        impact=ImpactLevel(record.get("Impact") or ImpactLevel.INFORMATIONAL.value),
        timestamp=_parse_datetime(record.get("Timestamp")),
    )


def _parse_date(value: Any) -> datetime:
    if not value:
        return utcnow_naive()
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    return datetime.fromisoformat(str(value))


def _parse_datetime(value: Any) -> datetime:
    if not value:
        return utcnow_naive()
    return datetime.fromisoformat(str(value))
