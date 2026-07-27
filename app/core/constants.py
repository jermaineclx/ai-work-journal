"""Shared constants that are not user-configurable settings."""

from __future__ import annotations

TASKS_WORKSHEET_TITLE = "Tasks"
DAILY_LOGS_WORKSHEET_TITLE = "Daily Logs"

# These must exactly match row 1 of the live Google Sheet — order matters
# for writes (append_row/update_row_by_key build values positionally from
# this list) even though reads are name-keyed and therefore order-agnostic.
TASKS_HEADER = [
    "Task ID",
    "Priority",
    "Task Name",
    "Summary",
    "Stakeholder",
    "Status",
    "Tags",
    "Resources",
    "Date Created",
    "Last Updated",
    "Total Updates",
]

DAILY_LOGS_HEADER = [
    "Log ID",
    "Date",
    "Task ID",
    "Log Summary",
    "Stakeholder",
    "Next Steps",
    "Resources",
    "Tags",
    "Impact",
    "Timestamp",
    "Original Message",
]

TASK_ID_PREFIX = "T"
LOG_ID_PREFIX = "L"

MAX_SIMILARITY_CANDIDATES = 5
