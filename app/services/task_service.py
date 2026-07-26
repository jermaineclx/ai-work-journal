"""TaskService — direct Task CRUD/editing operations (FR9 — Editing).

Unlike LogService, these operations are user-initiated corrections with
no AI involved; they exist so a user can fix an AI mistake without
waiting for another Telegram message to happen to trigger a re-match.
"""

from __future__ import annotations

from app.ai.embeddings import EmbeddingRefresher
from app.domain.entities import Task
from app.domain.enums import TaskStatus
from app.repositories import TaskRepository


class TaskService:
    def __init__(self, task_repo: TaskRepository, embedding_refresher: EmbeddingRefresher) -> None:
        self._tasks = task_repo
        self._embeddings = embedding_refresher

    async def list_tasks(self, *, status: TaskStatus | None = None) -> list[Task]:
        tasks = await self._tasks.get_all()
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.updated_at, reverse=True)

    async def get_task(self, task_id: str) -> Task:
        return await self._tasks.require_by_id(task_id)

    async def edit_status(self, task_id: str, status: TaskStatus) -> Task:
        task = await self._tasks.require_by_id(task_id)
        task.status = status
        await self._tasks.update(task)
        return task

    async def edit_stakeholder(self, task_id: str, stakeholder: str) -> Task:
        task = await self._tasks.require_by_id(task_id)
        task.stakeholder = stakeholder
        await self._tasks.update(task)
        await self._embeddings.refresh(task)
        return task

    async def edit_tags(self, task_id: str, tags: list[str]) -> Task:
        task = await self._tasks.require_by_id(task_id)
        task.tags = tags
        await self._tasks.update(task)
        await self._embeddings.refresh(task)
        return task

    async def edit_title(self, task_id: str, title: str) -> Task:
        task = await self._tasks.require_by_id(task_id)
        task.title = title
        await self._tasks.update(task)
        await self._embeddings.refresh(task)
        return task

    async def edit_summary(self, task_id: str, summary: str) -> Task:
        """Manually override the rolling summary. The next confirmed log
        still regenerates it via the Summary Agent — but that agent always
        rewrites *from* the current summary, so a manual edit becomes the
        new baseline rather than being silently discarded."""
        task = await self._tasks.require_by_id(task_id)
        task.summary = summary
        await self._tasks.update(task)
        await self._embeddings.refresh(task)
        return task

    async def edit_resources(self, task_id: str, resources: list[str]) -> Task:
        task = await self._tasks.require_by_id(task_id)
        task.resources = resources
        await self._tasks.update(task)
        return task
