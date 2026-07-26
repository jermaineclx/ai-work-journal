"""Tests for the pure parsing helpers behind /all_tasks, /all_logs and
/edit — no Telegram objects involved, just string-in-value-out logic."""

from __future__ import annotations

from datetime import date, timedelta

from app.domain.enums import ImpactLevel, TaskStatus
from app.integrations.telegram.handlers import (
    _parse_impact,
    _parse_iso_date,
    _parse_list,
    _parse_relative_or_iso_date,
    _parse_status,
)


def test_parse_status_matches_case_insensitively_and_with_underscores():
    assert _parse_status("waiting qa") == TaskStatus.WAITING_QA
    assert _parse_status("waiting_qa") == TaskStatus.WAITING_QA
    assert _parse_status("Waiting QA") == TaskStatus.WAITING_QA
    assert _parse_status("In Progress") == TaskStatus.IN_PROGRESS


def test_parse_status_returns_none_for_unknown_value():
    assert _parse_status("not a real status") is None


def test_parse_impact_matches_case_insensitively():
    assert _parse_impact("high") == ImpactLevel.HIGH
    assert _parse_impact("Critical") == ImpactLevel.CRITICAL
    assert _parse_impact("nonsense") is None


def test_parse_list_splits_and_strips_commas():
    assert _parse_list("SQL, Finance,  Dashboard ") == ["SQL", "Finance", "Dashboard"]
    assert _parse_list("") == []
    assert _parse_list("  ,  ,") == []


def test_parse_iso_date_accepts_valid_iso_and_rejects_garbage():
    assert _parse_iso_date("2026-07-26") == date(2026, 7, 26)
    assert _parse_iso_date("26/07/2026") is None
    assert _parse_iso_date("not a date") is None


def test_parse_relative_or_iso_date_handles_keywords_and_iso():
    assert _parse_relative_or_iso_date("today") == date.today()
    assert _parse_relative_or_iso_date("Yesterday") == date.today() - timedelta(days=1)
    assert _parse_relative_or_iso_date("2026-01-01") == date(2026, 1, 1)
    assert _parse_relative_or_iso_date("garbage") is None
