from __future__ import annotations

from pydantic import BaseModel


class DailySummary(BaseModel):
    task_titles: list[str]
    log_count: int


class WeeklySummary(BaseModel):
    text: str
    log_count: int
    tasks_touched: int
