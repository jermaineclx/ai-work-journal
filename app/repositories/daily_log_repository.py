"""Persistence abstraction for Daily Logs.

Daily Logs are immutable in one specific sense: the original message,
timestamp and log/task IDs can never change. `update_extracted_fields`
lets a user correct the AI-derived fields (stakeholder/status/next
steps/tags) on a past log — an explicit, user-initiated correction, not
automatic AI rewriting — per 01_PRD.md §11.2 ("Corrections should modify
extracted fields while preserving: original message, submission
timestamp, historical context"). `delete` is reserved for the narrower
"undo my last action" feature (FR9 / 01_PRD.md §13).
"""

from __future__ import annotations

from datetime import date

from app.core.constants import DAILY_LOGS_HEADER, DAILY_LOGS_WORKSHEET_TITLE, LOG_ID_PREFIX
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.domain.entities import DailyLog
from app.integrations.sheets.client import GoogleSheetsClient
from app.repositories.mappers import daily_log_to_row, row_to_daily_log

logger = get_logger(__name__)


class DailyLogRepository:
    def __init__(self, sheets: GoogleSheetsClient, spreadsheet_id: str) -> None:
        self._sheets = sheets
        self._spreadsheet_id = spreadsheet_id

    async def get_all(self) -> list[DailyLog]:
        """Mapper functions are already defensive about malformed cell
        values (04_AI_DESIGN.MD graceful-degradation pattern), but this is
        a last-resort backstop: one row we genuinely can't parse must never
        take down every other read (next_log_id, get_latest, etc. all funnel
        through here) — skip it and log instead of raising."""
        records = await self._sheets.get_all_records(self._spreadsheet_id, DAILY_LOGS_WORKSHEET_TITLE)
        logs = []
        for r in records:
            if not r.get("Log ID"):
                continue
            try:
                logs.append(row_to_daily_log(r))
            except Exception:  # noqa: BLE001
                logger.warning("skipping_unparseable_daily_log_row", extra={"log_id": r.get("Log ID")})
        return logs

    async def get_by_task(self, task_id: str) -> list[DailyLog]:
        return [log for log in await self.get_all() if log.task_id == task_id]

    async def get_by_date(self, target: date) -> list[DailyLog]:
        return [log for log in await self.get_all() if log.date == target]

    async def get_between(self, start: date, end: date) -> list[DailyLog]:
        return [log for log in await self.get_all() if start <= log.date <= end]

    async def next_log_id(self) -> str:
        logs = await self.get_all()
        max_n = 0
        for log in logs:
            suffix = log.log_id.removeprefix(LOG_ID_PREFIX)
            if suffix.isdigit():
                max_n = max(max_n, int(suffix))
        return f"{LOG_ID_PREFIX}{max_n + 1:04d}"

    async def append(self, log: DailyLog) -> DailyLog:
        await self._sheets.append_row(
            self._spreadsheet_id,
            DAILY_LOGS_WORKSHEET_TITLE,
            [daily_log_to_row(log)[col] for col in DAILY_LOGS_HEADER],
        )
        return log

    async def get_latest(self) -> DailyLog | None:
        logs = await self.get_all()
        if not logs:
            return None
        return max(logs, key=lambda log: log.timestamp)

    async def get_by_id(self, log_id: str) -> DailyLog | None:
        for log in await self.get_all():
            if log.log_id == log_id:
                return log
        return None

    async def require_by_id(self, log_id: str) -> DailyLog:
        log = await self.get_by_id(log_id)
        if log is None:
            raise NotFoundError(f"Daily Log '{log_id}' not found")
        return log

    async def update_extracted_fields(self, log: DailyLog) -> None:
        """Overwrite a log's extracted fields. `log.original_message`,
        `log.timestamp`, `log.log_id` and `log.task_id` must be unchanged
        from what's already stored — only the AI-derived fields should differ."""
        updated = await self._sheets.update_row_by_key(
            self._spreadsheet_id,
            DAILY_LOGS_WORKSHEET_TITLE,
            key_column="Log ID",
            key_value=log.log_id,
            header=DAILY_LOGS_HEADER,
            row_values=daily_log_to_row(log),
        )
        if not updated:
            raise NotFoundError(f"Daily Log '{log.log_id}' not found when updating")

    async def delete(self, log_id: str) -> bool:
        """Hard-delete one row. Reserved for the explicit "undo" action."""
        return await self._sheets.delete_row_by_key(
            self._spreadsheet_id, DAILY_LOGS_WORKSHEET_TITLE, key_column="Log ID", key_value=log_id
        )
