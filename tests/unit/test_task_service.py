"""TaskService tests using in-memory fakes."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.entities import Task
from app.domain.enums import TaskStatus
from app.services.task_service import TaskService


class FakeTaskRepository:
    def __init__(self):
        self.tasks: dict[str, Task] = {}

    async def get_all(self) -> list[Task]:
        return list(self.tasks.values())

    async def require_by_id(self, task_id: str) -> Task:
        return self.tasks[task_id]

    async def create(self, task: Task) -> Task:
        self.tasks[task.task_id] = task
        return task

    async def update(self, task: Task) -> None:
        self.tasks[task.task_id] = task


class FakeEmbeddingRefresher:
    def __init__(self):
        self.refreshed: list[str] = []

    async def refresh(self, task: Task) -> None:
        self.refreshed.append(task.task_id)


def _make_service():
    repo = FakeTaskRepository()
    refresher = FakeEmbeddingRefresher()
    return TaskService(repo, refresher), repo, refresher


@pytest.mark.asyncio
async def test_edit_title_updates_task_and_refreshes_embedding():
    service, repo, refresher = _make_service()
    await repo.create(Task(task_id="T001", title="Old Title", stakeholder="Finance", status=TaskStatus.IN_PROGRESS))

    task = await service.edit_title("T001", "New Title")

    assert task.title == "New Title"
    assert repo.tasks["T001"].title == "New Title"
    assert "T001" in refresher.refreshed


@pytest.mark.asyncio
async def test_edit_summary_updates_task_and_refreshes_embedding():
    service, repo, refresher = _make_service()
    await repo.create(Task(task_id="T001", title="Title", stakeholder="Finance", status=TaskStatus.IN_PROGRESS))

    task = await service.edit_summary("T001", "New rolling summary text.")

    assert task.summary == "New rolling summary text."
    assert "T001" in refresher.refreshed


@pytest.mark.asyncio
async def test_list_known_stakeholders_dedupes_and_orders_by_recency():
    service, repo, _ = _make_service()
    await repo.create(
        Task(
            task_id="T001",
            title="A",
            stakeholder="Priya Shah",
            status=TaskStatus.IN_PROGRESS,
            updated_at=_dt(2026, 1, 1),
        )
    )
    await repo.create(
        Task(
            task_id="T002", title="B", stakeholder="John Tan", status=TaskStatus.IN_PROGRESS, updated_at=_dt(2026, 1, 3)
        )
    )
    await repo.create(
        Task(
            task_id="T003",
            title="C",
            stakeholder="Priya Shah",
            status=TaskStatus.IN_PROGRESS,
            updated_at=_dt(2026, 1, 2),
        )
    )

    stakeholders = await service.list_known_stakeholders()

    assert stakeholders == ["John Tan", "Priya Shah"]


@pytest.mark.asyncio
async def test_list_known_stakeholders_respects_limit():
    service, repo, _ = _make_service()
    for i in range(10):
        await repo.create(
            Task(task_id=f"T{i:03d}", title=f"Task {i}", stakeholder=f"Person {i}", status=TaskStatus.IN_PROGRESS)
        )

    stakeholders = await service.list_known_stakeholders(limit=3)

    assert len(stakeholders) == 3


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day)
