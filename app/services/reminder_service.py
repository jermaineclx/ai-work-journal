"""ReminderService (FR12) — decides whether a reminder is warranted.

Sending the actual Telegram message is the bot layer's job; this
service only answers the deterministic question "has anything been
logged today?".
"""

from __future__ import annotations

from datetime import date

from app.repositories import DailyLogRepository


class ReminderService:
    def __init__(self, log_repo: DailyLogRepository) -> None:
        self._logs = log_repo

    async def should_remind(self, *, today: date | None = None) -> bool:
        target = today or date.today()
        logs = await self._logs.get_by_date(target)
        return len(logs) == 0
