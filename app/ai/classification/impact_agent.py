"""Impact Agent (01_PRD.md §12, "Impact Detection"). Advisory only — never
used to gate automation or the Decision Engine."""

from __future__ import annotations

from app.ai.prompts import latest_version, load_prompt, render_prompt
from app.ai.providers.base import LLMProvider
from app.domain.enums import TaskStatus
from app.schemas.ai import ExtractionResult, ImpactResult

_PROMPT_PREFIX = "estimate_impact"


class ImpactAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(self, *, message: str, extraction: ExtractionResult, status: TaskStatus) -> tuple[ImpactResult, str]:
        version = latest_version(_PROMPT_PREFIX)
        template = load_prompt(version)
        system_prompt = render_prompt(
            template,
            MESSAGE=message,
            EXTRACTED_ENTITIES=extraction.model_dump_json(),
            STATUS=status.value,
        )
        result = await self._llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt="Estimate impact now.",
            response_model=ImpactResult,
            prompt_version=version,
        )
        return result, version
