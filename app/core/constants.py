"""Shared constants that are not user-configurable settings."""

from __future__ import annotations

TASKS_WORKSHEET_TITLE = "Tasks"
DAILY_LOGS_WORKSHEET_TITLE = "Daily Logs"

TASKS_HEADER = [
    "Task ID",
    "Task Name",
    "Stakeholder",
    "Status",
    "Tags",
    "Resources",
    "Date Created",
    "Last Updated",
    "Total Updates",
    "Summary",
    # Appended (not inserted) — a live sheet already has data in the columns
    # above; adding a new column must go at the end so existing rows' cells
    # keep mapping to the same header they always did.
    "Priority",
]

DAILY_LOGS_HEADER = [
    "Log ID",
    "Date",
    "Task ID",
    "Original Message",
    "Stakeholder",
    "Status",
    "Next Steps",
    "Resources",
    "Tags",
    "Impact",
    "Timestamp",
]

TASK_ID_PREFIX = "T"
LOG_ID_PREFIX = "L"

MAX_SIMILARITY_CANDIDATES = 5
