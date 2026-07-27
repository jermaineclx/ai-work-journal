"""Tests for the fixed Priority set (domain layer)."""

from __future__ import annotations

from app.domain.enums import Priority


def test_parse_matches_exact_value():
    assert Priority.parse("P0") == Priority.P0
    assert Priority.parse("P1") == Priority.P1
    assert Priority.parse("P2") == Priority.P2


def test_parse_is_case_insensitive():
    assert Priority.parse("p0") == Priority.P0
    assert Priority.parse("p2") == Priority.P2


def test_parse_returns_none_for_unknown_or_empty():
    assert Priority.parse("P3") is None
    assert Priority.parse("urgent") is None
    assert Priority.parse(None) is None
    assert Priority.parse("") is None


def test_priority_has_exactly_three_levels():
    assert [p.value for p in Priority] == ["P0", "P1", "P2"]
