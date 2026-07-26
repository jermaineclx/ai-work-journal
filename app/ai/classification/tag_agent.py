"""Tag Agent (04_AI_DESIGN.MD §4.4)."""

from __future__ import annotations

from app.ai.prompts import latest_version, load_prompt, render_prompt
from app.ai.providers.base import LLMProvider
from app.schemas.ai import ExtractionResult, TagResult

_PROMPT_PREFIX = "generate_tags"


class TagAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(self, *, message: str, extraction: ExtractionResult, known_tags: list[str]) -> tuple[TagResult, str]:
        version = latest_version(_PROMPT_PREFIX)
        template = load_prompt(version)
        system_prompt = render_prompt(
            template,
            KNOWN_TAGS=", ".join(known_tags) or "(none yet)",
            MESSAGE=message,
            EXTRACTED_ENTITIES=extraction.model_dump_json(),
        )
        result = await self._llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt="Generate tags now.",
            response_model=TagResult,
            prompt_version=version,
        )
        return result, version
