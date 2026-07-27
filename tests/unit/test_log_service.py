"""LogService tests using in-memory fakes — no network, no real LLM/Sheets calls.

Exercises the auto-apply, confirm, and undo flows end-to-end at the
service layer, which is where the Decision Engine's output actually
turns into persisted state.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.domain.entities import DailyLog, Task
from app.domain.enums import ImpactLevel, TaskStatus
from app.schemas.ai import (
    AIPipelineOutput,
    ExtractionResult,
    ImpactResult,
    MatchResult,
    ResourceResult,
    StatusResult,
    SummaryResult,
    TagResult,
)
from app.services.log_service import LogService


class FakeTaskRepository:
    def __init__(self):
        self.tasks: dict[str, Task] = {}

    async def get_all(self) -> list[Task]:
        return list(self.tasks.values())

    async def get_by_id(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    async def require_by_id(self, task_id: str) -> Task:
        return self.tasks[task_id]

    async def next_task_id(self) -> str:
        return f"T{len(self.tasks) + 1:03d}"

    async def create(self, task: Task) -> Task:
        self.tasks[task.task_id] = task
        return task

    async def update(self, task: Task) -> None:
        self.tasks[task.task_id] = task


class FakeDailyLogRepository:
    def __init__(self):
        self.logs: list[DailyLog] = []

    async def next_log_id(self) -> str:
        return f"L{len(self.logs) + 1:04d}"

    async def append(self, log: DailyLog) -> DailyLog:
        self.logs.append(log)
        return log

    async def get_latest(self) -> DailyLog | None:
        return max(self.logs, key=lambda log: log.timestamp) if self.logs else None

    async def get_all(self) -> list[DailyLog]:
        return list(self.logs)

    async def get_by_task(self, task_id: str) -> list[DailyLog]:
        return [log for log in self.logs if log.task_id == task_id]

    async def get_by_id(self, log_id: str) -> DailyLog | None:
        return next((log for log in self.logs if log.log_id == log_id), None)

    async def require_by_id(self, log_id: str) -> DailyLog:
        log = await self.get_by_id(log_id)
        if log is None:
            raise NotFoundError(f"Daily Log '{log_id}' not found")
        return log

    async def update_extracted_fields(self, log: DailyLog) -> None:
        for i, existing in enumerate(self.logs):
            if existing.log_id == log.log_id:
                self.logs[i] = log
                return
        raise NotFoundError(f"Daily Log '{log.log_id}' not found when updating")

    async def delete(self, log_id: str) -> bool:
        before = len(self.logs)
        self.logs = [log for log in self.logs if log.log_id != log_id]
        return len(self.logs) != before


class FakeMemoryRepository:
    def __init__(self):
        self.processed: dict[str, str] = {}
        self.pending: dict[str, str] = {}
        self.aliases: dict[str, str] = {}
        self.confidence_records: list[dict] = []

    async def get_processed_request(self, request_id: str) -> str | None:
        return self.processed.get(request_id)

    async def mark_request_processed(self, request_id: str, result_json: str) -> None:
        self.processed[request_id] = result_json

    async def save_pending_confirmation(self, request_id: str, user_id: str, payload_json: str) -> None:
        self.pending[request_id] = payload_json

    async def get_pending_confirmation(self, request_id: str) -> str | None:
        return self.pending.get(request_id)

    async def delete_pending_confirmation(self, request_id: str) -> None:
        self.pending.pop(request_id, None)

    async def record_confidence_outcome(self, **kwargs) -> None:
        self.confidence_records.append(kwargs)

    async def learn_alias(self, alias: str, canonical: str, alias_type: str) -> None:
        self.aliases[f"{alias_type}:{alias.lower()}"] = canonical


class FakeOrchestrator:
    def __init__(self, output: AIPipelineOutput):
        self.output = output

    async def run(self, *, message: str, tasks: list[Task]) -> AIPipelineOutput:
        return self.output


class FakeSummaryAgent:
    async def run(self, *, task_title, current_summary, message, status):
        return SummaryResult(summary=f"Summary after: {message}"), "generate_summary_v1"


class FakeEmbeddingRefresher:
    def __init__(self):
        self.refreshed: list[str] = []

    async def refresh(self, task: Task) -> None:
        self.refreshed.append(task.task_id)


def _build_ai_output(
    *, matched_task_id: str | None, confidence: float, task_title: str = "Settlement Reconciliation"
) -> AIPipelineOutput:
    return AIPipelineOutput(
        extraction=ExtractionResult(task_title=task_title, stakeholder=["Finance"], extraction_confidence=confidence),
        match=MatchResult(
            matched_task_id=matched_task_id,
            matched_task_title=task_title if matched_task_id else None,
            confidence=confidence,
        ),
        status=StatusResult(status=TaskStatus.KIV, confidence=confidence),
        tags=TagResult(tags=["SQL", "Finance"]),
        resources=ResourceResult(resources=[]),
        impact=ImpactResult(impact=ImpactLevel.MEDIUM),
        overall_confidence=confidence,
    )


def _make_service(ai_output: AIPipelineOutput, *, task_repo=None):
    task_repo = task_repo or FakeTaskRepository()
    return (
        LogService(
            orchestrator=FakeOrchestrator(ai_output),
            summary_agent=FakeSummaryAgent(),
            embedding_refresher=FakeEmbeddingRefresher(),
            task_repo=task_repo,
            log_repo=FakeDailyLogRepository(),
            memory=FakeMemoryRepository(),
            settings=Settings(confidence_auto_apply=0.95, confidence_confirm_lower_bound=0.80),
        ),
        task_repo,
    )


@pytest.mark.asyncio
async def test_high_confidence_new_task_still_requires_confirmation():
    ai_output = _build_ai_output(matched_task_id=None, confidence=0.99)
    service, _ = _make_service(ai_output)

    outcome = await service.process_message(request_id="req-1", user_id="u1", message="Built the churn dashboard.")

    assert outcome.status == "pending_confirmation"
    assert outcome.proposed_task_title == "Settlement Reconciliation"


@pytest.mark.asyncio
async def test_high_confidence_existing_match_auto_commits():
    task_repo = FakeTaskRepository()
    existing = Task(
        task_id="T001", title="Settlement Reconciliation", stakeholder=["Finance"], status=TaskStatus.IN_PROGRESS
    )
    await task_repo.create(existing)

    ai_output = _build_ai_output(matched_task_id="T001", confidence=0.97)
    service, task_repo = _make_service(ai_output, task_repo=task_repo)

    outcome = await service.process_message(request_id="req-2", user_id="u1", message="Finance approved. QA tomorrow.")

    assert outcome.status == "committed"
    assert outcome.auto_applied is True
    assert outcome.task_id == "T001"
    assert task_repo.tasks["T001"].status == TaskStatus.KIV
    assert task_repo.tasks["T001"].total_updates == 1


@pytest.mark.asyncio
async def test_confirm_new_task_creates_task_and_log():
    ai_output = _build_ai_output(matched_task_id=None, confidence=0.5)
    service, task_repo = _make_service(ai_output)

    pending = await service.process_message(request_id="req-3", user_id="u1", message="Started churn dashboard work.")
    assert pending.status == "pending_confirmation"

    outcome = await service.confirm(request_id="req-3", chosen_task_id=None, create_new=True)

    assert outcome.status == "committed"
    assert outcome.is_new_task is True
    assert outcome.auto_applied is False
    assert len(task_repo.tasks) == 1


@pytest.mark.asyncio
async def test_duplicate_request_id_replays_cached_result():
    ai_output = _build_ai_output(matched_task_id=None, confidence=0.99)
    service, task_repo = _make_service(ai_output)

    first = await service.process_message(request_id="req-4", user_id="u1", message="dup test")
    second = await service.process_message(request_id="req-4", user_id="u1", message="dup test")

    assert first == second


@pytest.mark.asyncio
async def test_undo_last_removes_log_and_decrements_task_counter():
    task_repo = FakeTaskRepository()
    existing = Task(
        task_id="T001",
        title="Settlement Reconciliation",
        stakeholder=["Finance"],
        status=TaskStatus.IN_PROGRESS,
        total_updates=1,
    )
    await task_repo.create(existing)
    ai_output = _build_ai_output(matched_task_id="T001", confidence=0.97)
    service, task_repo = _make_service(ai_output, task_repo=task_repo)

    await service.process_message(request_id="req-5", user_id="u1", message="Finance approved.")
    assert task_repo.tasks["T001"].total_updates == 2

    undone = await service.undo_last()

    assert undone is not None
    assert task_repo.tasks["T001"].total_updates == 1


@pytest.mark.asyncio
async def test_create_task_explicitly_uses_overridden_stakeholder():
    """Mirrors the /new_task flow: extraction derives the title, but the
    stakeholder is whatever the user explicitly supplied, not AI-guessed."""
    ai_output = _build_ai_output(matched_task_id=None, confidence=0.4, task_title="Budget Projection")
    overridden = ai_output.model_copy(
        update={"extraction": ai_output.extraction.model_copy(update={"stakeholder": ["Priya Shah"]})}
    )
    service, task_repo = _make_service(ai_output)

    outcome = await service.create_task_explicitly(
        request_id="req-new-task-1", message="Worked on the budget projection.", ai_output=overridden
    )

    assert outcome.status == "committed"
    assert outcome.is_new_task is True
    assert outcome.stakeholder == ["Priya Shah"]
    assert len(task_repo.tasks) == 1


@pytest.mark.asyncio
async def test_create_task_explicitly_is_idempotent_on_request_id():
    ai_output = _build_ai_output(matched_task_id=None, confidence=0.4)
    service, task_repo = _make_service(ai_output)

    first = await service.create_task_explicitly(request_id="req-new-task-2", message="msg", ai_output=ai_output)
    second = await service.create_task_explicitly(request_id="req-new-task-2", message="msg", ai_output=ai_output)

    assert first == second
    assert len(task_repo.tasks) == 1


@pytest.mark.asyncio
async def test_edit_log_fields_update_the_stored_log():
    task_repo = FakeTaskRepository()
    await task_repo.create(
        Task(task_id="T001", title="Settlement Reconciliation", stakeholder=["Finance"], status=TaskStatus.IN_PROGRESS)
    )
    ai_output = _build_ai_output(matched_task_id="T001", confidence=0.97)
    service, task_repo = _make_service(ai_output, task_repo=task_repo)

    committed = await service.process_message(request_id="req-6", user_id="u1", message="Finance approved.")
    log_id = committed.log_id

    updated = await service.edit_log_stakeholder(log_id, ["Priya Shah"])
    assert updated.stakeholder == ["Priya Shah"]

    updated = await service.edit_log_status(log_id, TaskStatus.COMPLETED)
    assert updated.status == TaskStatus.COMPLETED

    updated = await service.edit_log_next_steps(log_id, "Ship next week")
    assert updated.next_steps == "Ship next week"

    updated = await service.edit_log_tags(log_id, ["SQL", "Reporting"])
    assert updated.tags == ["SQL", "Reporting"]

    fetched = await service.get_log(log_id)
    assert fetched.stakeholder == ["Priya Shah"]
    assert fetched.tags == ["SQL", "Reporting"]


@pytest.mark.asyncio
async def test_edit_log_field_raises_for_unknown_log():
    ai_output = _build_ai_output(matched_task_id=None, confidence=0.4)
    service, _ = _make_service(ai_output)

    with pytest.raises(NotFoundError):
        await service.edit_log_stakeholder("L9999", ["Nobody"])


@pytest.mark.asyncio
async def test_list_logs_for_task_returns_most_recent_first():
    task_repo = FakeTaskRepository()
    await task_repo.create(
        Task(task_id="T001", title="Settlement Reconciliation", stakeholder=["Finance"], status=TaskStatus.IN_PROGRESS)
    )
    ai_output = _build_ai_output(matched_task_id="T001", confidence=0.97)
    service, _ = _make_service(ai_output, task_repo=task_repo)

    await service.process_message(request_id="req-7a", user_id="u1", message="First update")
    await service.process_message(request_id="req-7b", user_id="u1", message="Second update")
    # Pin timestamps explicitly so ordering doesn't depend on how fast the
    # two awaited calls above actually ran.
    service._logs.logs[0].timestamp = datetime(2026, 1, 1, 10, 0, 0)
    service._logs.logs[1].timestamp = datetime(2026, 1, 1, 11, 0, 0)

    logs = await service.list_logs_for_task("T001")

    assert [log.original_message for log in logs] == ["Second update", "First update"]


@pytest.mark.asyncio
async def test_edit_log_resources_impact_and_date():
    task_repo = FakeTaskRepository()
    await task_repo.create(
        Task(task_id="T001", title="Settlement Reconciliation", stakeholder=["Finance"], status=TaskStatus.IN_PROGRESS)
    )
    ai_output = _build_ai_output(matched_task_id="T001", confidence=0.97)
    service, _ = _make_service(ai_output, task_repo=task_repo)

    committed = await service.process_message(request_id="req-8", user_id="u1", message="Finance approved.")
    log_id = committed.log_id

    updated = await service.edit_log_resources(log_id, ["Settlement SQL script"])
    assert updated.resources == ["Settlement SQL script"]

    # Appends rather than overwrites, deduping against what's already there.
    updated = await service.edit_log_resources(log_id, ["Settlement SQL script", "New Doc"])
    assert updated.resources == ["Settlement SQL script", "New Doc"]

    updated = await service.edit_log_impact(log_id, ImpactLevel.HIGH)
    assert updated.impact == ImpactLevel.HIGH

    new_date = date(2026, 1, 15)
    updated = await service.edit_log_date(log_id, new_date)
    assert updated.date == new_date
    # Editing the logged date must never touch when it was actually submitted.
    assert updated.timestamp == committed_log_timestamp(service, log_id)


def committed_log_timestamp(service: LogService, log_id: str):
    return next(log.timestamp for log in service._logs.logs if log.log_id == log_id)


@pytest.mark.asyncio
async def test_search_logs_filters_by_task_and_date():
    task_repo = FakeTaskRepository()
    await task_repo.create(
        Task(task_id="T001", title="Settlement Reconciliation", stakeholder=["Finance"], status=TaskStatus.IN_PROGRESS)
    )
    await task_repo.create(
        Task(task_id="T002", title="Budget Projection", stakeholder=["Priya"], status=TaskStatus.IN_PROGRESS)
    )
    ai_output_t1 = _build_ai_output(matched_task_id="T001", confidence=0.97)
    service, _ = _make_service(ai_output_t1, task_repo=task_repo)

    await service.process_message(request_id="req-9a", user_id="u1", message="Task 1 update")

    ai_output_t2 = _build_ai_output(matched_task_id="T002", confidence=0.97, task_title="Budget Projection")
    service._orchestrator.output = ai_output_t2
    await service.process_message(request_id="req-9b", user_id="u1", message="Task 2 update")

    only_t1 = await service.search_logs(task_id="T001")
    assert [log.original_message for log in only_t1] == ["Task 1 update"]

    all_logs = await service.search_logs()
    assert len(all_logs) == 2

    none_for_bad_date = await service.search_logs(on_date=date(2000, 1, 1))
    assert none_for_bad_date == []
