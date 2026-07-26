from __future__ import annotations

from enum import Enum


class TaskStatus(str, Enum):
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    KIV = "KIV"  # "Keep In View" — on hold / revisit later, this user's catch-all for anything not actively moving


class Stakeholder(str, Enum):
    """The fixed roster of coworkers this user logs work against.

    Deliberately a closed set (not free text) — matches the fixed
    dropdown-chip UI this user actually uses day to day. AI-extracted
    stakeholder mentions are validated against this roster (see
    `Stakeholder.parse`); anything that doesn't match is treated as
    unknown rather than silently accepting a hallucinated/typo'd name.
    """

    LIYUAN = "Liyuan"
    AMMIR = "Ammir"
    ZIYUE = "Ziyue"
    ROSEY = "Rosey"
    JOSHUA = "Joshua"
    JEREMY = "Jeremy"
    NICOLE_ONG = "Nicole Ong"
    EE_XUEN = "Ee Xuen"

    @classmethod
    def parse(cls, value: str | None) -> Stakeholder | None:
        """Case-insensitive match against the roster; None if no match."""
        if not value:
            return None
        normalized = value.strip().lower()
        return next((member for member in cls if member.value.lower() == normalized), None)


class ImpactLevel(str, Enum):
    INFORMATIONAL = "Informational"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class DecisionAction(str, Enum):
    """What the Decision Engine tells the Application Layer to do next."""

    AUTO_SAVE_EXISTING_TASK = "auto_save_existing_task"
    AUTO_SAVE_NEW_TASK = "auto_save_new_task"
    CONFIRM_EXISTING_TASK = "confirm_existing_task"
    CONFIRM_NEW_TASK = "confirm_new_task"
    ASK_CLARIFICATION = "ask_clarification"
