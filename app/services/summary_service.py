"""SummaryService — daily review (FR10) and weekly summary (FR11).

Daily summaries are assembled deterministically (no LLM call needed for
a same-day recap — 16.8 Cost Efficiency: "avoid repeated summarisation").
Weekly summaries use the WeeklySummaryAgent since they require genuine
synthesis across many logs.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.ai.summarisation import WeeklySummaryAgent
from app.repositories import DailyLogRepository, TaskRepository
from app.schemas.summary import DailySummary, WeeklySummary


class SummaryService:
    def __init__(
        self, task_repo: TaskRepository, log_repo: DailyLogRepository, weekly_agent: WeeklySummaryAgent
    ) -> None:
        self._tasks = task_repo
        self._logs = log_repo
        self._weekly_agent = weekly_agent

    async def today_summary(self, *, today: date | None = None) -> DailySummary:
        target = today or date.today()
        logs = await self._logs.get_by_date(target)
        tasks_by_id = {t.task_id: t for t in await self._tasks.get_all()}
        titles = [tasks_by_id[log.task_id].title if log.task_id in tasks_by_id else log.task_id for log in logs]
        return DailySummary(task_titles=titles, log_count=len(logs))

    async def weekly_summary(self, *, end: date | None = None) -> WeeklySummary:
        end_date = end or date.today()
        start_date = end_date - timedelta(days=6)
        logs = await self._logs.get_between(start_date, end_date)
        task_ids = {log.task_id for log in logs}
        all_tasks = await self._tasks.get_all()
        touched_tasks = [t for t in all_tasks if t.task_id in task_ids]
        text, _version = await self._weekly_agent.run(tasks=touched_tasks, logs=logs)
        return WeeklySummary(text=text, log_count=len(logs), tasks_touched=len(touched_tasks))
