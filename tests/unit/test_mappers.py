from datetime import date, datetime

from app.domain.entities import DailyLog, Task
from app.domain.enums import ImpactLevel, Priority, TaskStatus
from app.repositories.mappers import (
    daily_log_to_row,
    row_to_daily_log,
    row_to_task,
    task_to_row,
)


def test_task_round_trips_through_row_mapping():
    task = Task(
        task_id="T001",
        title="Settlement Reconciliation",
        stakeholder=["Finance"],
        status=TaskStatus.KIV,
        summary="Built SQL solution. Finance approved. Awaiting QA.",
        tags=["SQL", "Finance"],
        resources=["DataSuite Dashboard", "https://example.com/query"],
        created_at=datetime(2026, 7, 1),
        updated_at=datetime(2026, 7, 26),
        total_updates=4,
        priority=Priority.P1,
    )
    row = task_to_row(task)
    restored = row_to_task(row)

    assert restored.task_id == task.task_id
    assert restored.title == task.title
    assert restored.stakeholder == task.stakeholder
    assert restored.status == task.status
    assert restored.tags == task.tags
    assert restored.resources == task.resources
    assert restored.total_updates == task.total_updates
    assert restored.priority == Priority.P1


def test_daily_log_round_trips_through_row_mapping():
    log = DailyLog(
        log_id="L0001",
        task_id="T001",
        date=date(2026, 7, 26),
        original_message="Finance approved the SQL fix. QA tomorrow.",
        stakeholder=["Finance"],
        status=TaskStatus.KIV,
        next_steps="QA tomorrow",
        resources=["Settlement SQL"],
        tags=["SQL", "Finance"],
        impact=ImpactLevel.MEDIUM,
        timestamp=datetime(2026, 7, 26, 18, 42, 15),
        log_summary="Finance approved the settlement fix; QA scheduled for tomorrow.",
    )
    row = daily_log_to_row(log)
    restored = row_to_daily_log(row)

    assert restored.log_id == log.log_id
    assert restored.task_id == log.task_id
    assert restored.date == log.date
    assert restored.original_message == log.original_message
    assert restored.stakeholder == log.stakeholder
    assert restored.status == log.status
    assert restored.next_steps == log.next_steps
    assert restored.resources == log.resources
    assert restored.tags == log.tags
    assert restored.impact == log.impact
    assert restored.log_summary == log.log_summary


def test_daily_log_row_mapping_handles_missing_optional_fields():
    row = {
        "Log ID": "L0002",
        "Date": "2026-07-27",
        "Task ID": "T002",
        "Original Message": "Quick check-in with Product.",
        "Stakeholder": "",
        "Status": "",
        "Next Steps": "",
        "Resources": "",
        "Tags": "",
        "Impact": "",
        "Timestamp": "2026-07-27T09:00:00",
    }
    log = row_to_daily_log(row)
    assert log.stakeholder == []
    assert log.status is None
    assert log.next_steps is None
    assert log.resources == []
    assert log.tags == []
    assert log.impact == ImpactLevel.INFORMATIONAL
    assert log.log_summary == ""


def test_row_to_task_maps_legacy_status_values_instead_of_crashing():
    """Rows saved before the status set shrank to In Progress/Completed/KIV
    (e.g. old 'Waiting QA' rows already sitting in a live sheet) must still
    load rather than raise ValueError on an unrecognised enum value."""
    row = {
        "Task ID": "T001",
        "Task Name": "Settlement Reconciliation",
        "Stakeholder": "Liyuan",
        "Status": "Waiting QA",
        "Summary": "",
        "Tags": "",
        "Resources": "",
        "Date Created": "2026-07-01",
        "Last Updated": "2026-07-26",
        "Total Updates": 1,
    }

    task = row_to_task(row)

    assert task.status == TaskStatus.KIV
    # This row predates the Priority column entirely (no key in the dict
    # at all, not just an empty cell) — must default to None, not crash.
    assert task.priority is None


def test_row_to_daily_log_maps_legacy_status_values_instead_of_crashing():
    row = {
        "Log ID": "L0001",
        "Date": "2026-07-26",
        "Task ID": "T001",
        "Original Message": "Waiting on QA.",
        "Stakeholder": "Liyuan",
        "Status": "Ready for Deployment",
        "Next Steps": "",
        "Resources": "",
        "Tags": "",
        "Impact": "",
        "Timestamp": "2026-07-26T18:00:00",
    }

    log = row_to_daily_log(row)

    assert log.status == TaskStatus.KIV
    # This row predates the Log Summary column entirely — must default to
    # an empty string, not crash.
    assert log.log_summary == ""
