"""Search-related schemas (FR8 — natural language retrieval)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.domain.enums import TaskStatus


class SearchResultTask(BaseModel):
    task_id: str
    title: str
    stakeholder: list[str]
    status: TaskStatus
    summary: str
    similarity: float


class SearchResultLog(BaseModel):
    log_id: str
    task_id: str
    task_title: str
    date: date
    original_message: str
    status: TaskStatus | None


class SearchResponse(BaseModel):
    query: str
    tasks: list[SearchResultTask]
    logs: list[SearchResultLog]
    highlights: list[str]
