from __future__ import annotations

from enum import Enum


class TaskStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    WAITING_FEEDBACK = "Waiting Feedback"
    WAITING_QA = "Waiting QA"
    BLOCKED = "Blocked"
    READY_FOR_DEPLOYMENT = "Ready for Deployment"
    COMPLETED = "Completed"


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
