"""TaskService tests using in-memory fakes."""

from __future__ import annotations

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
async def test_edit_resources_updates_task_without_refreshing_embedding():
    """Resources aren't part of the embedding text (title/stakeholder/
    summary/tags only), so editing them shouldn't trigger a refresh."""
    service, repo, refresher = _make_service()
    await repo.create(Task(task_id="T001", title="Title", stakeholder="Finance", status=TaskStatus.IN_PROGRESS))

    task = await service.edit_resources("T001", ["DataSuite Dashboard", "https://example.com/query"])

    assert task.resources == ["DataSuite Dashboard", "https://example.com/query"]
    assert "T001" not in refresher.refreshed
