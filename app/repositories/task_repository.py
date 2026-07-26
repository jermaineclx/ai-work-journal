"""Persistence abstraction for Tasks (03_IMPLEMENTATION.md §13).

Application Services never call gspread directly — they call this
repository, which happens to be backed by Google Sheets today and could
be backed by PostgreSQL tomorrow without changing any caller.
"""

from __future__ import annotations

from app.core.constants import TASK_ID_PREFIX, TASKS_HEADER, TASKS_WORKSHEET_TITLE
from app.core.exceptions import NotFoundError
from app.domain.entities import Task
from app.integrations.sheets.client import GoogleSheetsClient
from app.repositories.mappers import row_to_task, task_to_row


class TaskRepository:
    def __init__(self, sheets: GoogleSheetsClient, spreadsheet_id: str) -> None:
        self._sheets = sheets
        self._spreadsheet_id = spreadsheet_id

    async def get_all(self) -> list[Task]:
        records = await self._sheets.get_all_records(self._spreadsheet_id, TASKS_WORKSHEET_TITLE)
        return [row_to_task(r) for r in records if r.get("Task ID")]

    async def get_by_id(self, task_id: str) -> Task | None:
        for task in await self.get_all():
            if task.task_id == task_id:
                return task
        return None

    async def require_by_id(self, task_id: str) -> Task:
        task = await self.get_by_id(task_id)
        if task is None:
            raise NotFoundError(f"Task '{task_id}' not found")
        return task

    async def next_task_id(self) -> str:
        tasks = await self.get_all()
        max_n = 0
        for task in tasks:
            suffix = task.task_id.removeprefix(TASK_ID_PREFIX)
            if suffix.isdigit():
                max_n = max(max_n, int(suffix))
        return f"{TASK_ID_PREFIX}{max_n + 1:03d}"

    async def create(self, task: Task) -> Task:
        await self._sheets.append_row(
            self._spreadsheet_id,
            TASKS_WORKSHEET_TITLE,
            [task_to_row(task)[col] for col in TASKS_HEADER],
        )
        return task

    async def update(self, task: Task) -> None:
        updated = await self._sheets.update_row_by_key(
            self._spreadsheet_id,
            TASKS_WORKSHEET_TITLE,
            key_column="Task ID",
            key_value=task.task_id,
            header=TASKS_HEADER,
            row_values=task_to_row(task),
        )
        if not updated:
            raise NotFoundError(f"Task '{task.task_id}' not found when updating")
