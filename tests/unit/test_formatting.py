"""Tests for the /all_tasks and /all_logs message-chunking behaviour —
Telegram messages have a hard 4096-char limit, so long lists must split."""

from __future__ import annotations

from datetime import date, datetime

from app.domain.entities import DailyLog, Task
from app.domain.enums import ImpactLevel, TaskStatus
from app.integrations.telegram.formatting import render_all_logs, render_all_tasks


def _task(task_id: str, summary: str = "") -> Task:
    return Task(
        task_id=task_id,
        title=f"Task {task_id}",
        stakeholder="Finance",
        status=TaskStatus.IN_PROGRESS,
        summary=summary,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )


def test_render_all_tasks_single_chunk_for_a_few_tasks():
    tasks = [_task(f"T{i:03d}") for i in range(3)]

    chunks = render_all_tasks(tasks)

    assert len(chunks) == 1
    assert "3 task(s)" in chunks[0]
    for t in tasks:
        assert t.task_id in chunks[0]


def test_render_all_tasks_splits_into_multiple_messages_when_long():
    long_summary = "x" * 1000
    tasks = [_task(f"T{i:03d}", summary=long_summary) for i in range(10)]

    chunks = render_all_tasks(tasks)

    assert len(chunks) > 1
    assert all(len(chunk) < 4096 for chunk in chunks)
    # Every task must appear exactly once across all chunks combined.
    combined = "\n\n".join(chunks)
    for t in tasks:
        assert combined.count(t.task_id) >= 1


def test_render_all_tasks_handles_empty_list():
    chunks = render_all_tasks([])
    assert chunks == ["0 task(s)"]


def test_render_all_logs_includes_task_title_when_known():
    task = _task("T001")
    log = DailyLog(
        log_id="L0001",
        task_id="T001",
        date=date(2026, 7, 26),
        original_message="Finance approved.",
        stakeholder="Finance",
        next_steps="QA tomorrow",
        impact=ImpactLevel.MEDIUM,
    )

    chunks = render_all_logs([log], {"T001": task})

    assert len(chunks) == 1
    assert task.title in chunks[0]
    assert "Finance approved." in chunks[0]


def test_render_all_logs_falls_back_to_task_id_when_task_unknown():
    log = DailyLog(
        log_id="L0002",
        task_id="T999",
        date=date(2026, 7, 26),
        original_message="Orphaned log.",
        stakeholder=None,
        next_steps=None,
    )

    chunks = render_all_logs([log], {})

    assert "T999" in chunks[0]
