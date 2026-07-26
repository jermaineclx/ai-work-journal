"""Weekly Summary Agent (FR11 / 03_IMPLEMENTATION.md §24)."""

from __future__ import annotations

from app.ai.prompts import latest_version, load_prompt, render_prompt
from app.ai.providers.base import LLMProvider
from app.domain.entities import DailyLog, Task
from app.schemas.ai import SummaryResult

_PROMPT_PREFIX = "weekly_summary"


class WeeklySummaryAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(self, *, tasks: list[Task], logs: list[DailyLog]) -> tuple[str, str]:
        version = latest_version(_PROMPT_PREFIX)
        template = load_prompt(version)
        tasks_text = (
            "\n".join(f"- {t.title} ({t.status.value}, stakeholder: {t.stakeholder})" for t in tasks) or "(none)"
        )
        logs_text = (
            "\n".join(f"- {log.date.isoformat()} [{log.task_id}] {log.original_message}" for log in logs) or "(none)"
        )
        system_prompt = render_prompt(template, TASKS=tasks_text, LOGS=logs_text)
        result = await self._llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt="Write the weekly summary now.",
            response_model=SummaryResult,
            prompt_version=version,
        )
        return result.summary, version
