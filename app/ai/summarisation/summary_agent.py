"""Summary Agent (04_AI_DESIGN.MD §4.6) — rewrites, never appends."""

from __future__ import annotations

from app.ai.prompts import latest_version, load_prompt, render_prompt
from app.ai.providers.base import LLMProvider
from app.domain.enums import TaskStatus
from app.schemas.ai import SummaryResult

_PROMPT_PREFIX = "generate_summary"


class SummaryAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(
        self,
        *,
        task_title: str,
        current_summary: str,
        message: str,
        status: TaskStatus,
    ) -> tuple[SummaryResult, str]:
        version = latest_version(_PROMPT_PREFIX)
        template = load_prompt(version)
        system_prompt = render_prompt(
            template,
            TASK_TITLE=task_title,
            CURRENT_SUMMARY=current_summary or "(no summary yet — this is a new task)",
            MESSAGE=message,
            STATUS=status.value,
        )
        result = await self._llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt="Rewrite the summary now.",
            response_model=SummaryResult,
            prompt_version=version,
        )
        return result, version
