"""Status Classification Agent (04_AI_DESIGN.MD §4.3)."""

from __future__ import annotations

from app.ai.prompts import latest_version, load_prompt, render_prompt
from app.ai.providers.base import LLMProvider
from app.domain.enums import TaskStatus
from app.schemas.ai import StatusResult

_PROMPT_PREFIX = "classify_status"


class StatusAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(
        self,
        *,
        message: str,
        status_hint: str | None,
        prior_status: TaskStatus | None,
    ) -> tuple[StatusResult, str]:
        version = latest_version(_PROMPT_PREFIX)
        template = load_prompt(version)
        system_prompt = render_prompt(
            template,
            PRIOR_STATUS=prior_status.value if prior_status else "(new task, no prior status)",
            STATUS_HINT=status_hint or "(none extracted)",
            MESSAGE=message,
        )
        result = await self._llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt="Classify the status now.",
            response_model=StatusResult,
            prompt_version=version,
        )
        return result, version
