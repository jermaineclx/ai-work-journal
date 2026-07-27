"""Tests for the fixed Stakeholder roster (domain layer)."""

from __future__ import annotations

from app.domain.enums import Stakeholder


def test_parse_matches_exact_value():
    assert Stakeholder.parse("Liyuan") == Stakeholder.LIYUAN
    assert Stakeholder.parse("Nicole Ong") == Stakeholder.NICOLE_ONG


def test_parse_is_case_insensitive_and_strips_whitespace():
    assert Stakeholder.parse("liyuan") == Stakeholder.LIYUAN
    assert Stakeholder.parse("LIYUAN") == Stakeholder.LIYUAN
    assert Stakeholder.parse("  Ee Xuen  ") == Stakeholder.EE_XUEN


def test_parse_returns_none_for_unknown_or_empty():
    assert Stakeholder.parse("Finance") is None
    assert Stakeholder.parse("Someone Not On The List") is None
    assert Stakeholder.parse(None) is None
    assert Stakeholder.parse("") is None


def test_roster_has_exactly_the_expected_eleven_names():
    assert {s.value for s in Stakeholder} == {
        "Liyuan",
        "Ammir",
        "Ziyue",
        "Rosey",
        "Joshua",
        "Jeremy",
        "Nicole Ong",
        "Ee Xuen",
        "Karleng",
        "Eugene",
        "Yan Ting",
    }
