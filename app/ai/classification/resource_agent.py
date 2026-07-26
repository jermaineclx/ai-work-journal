"""Resource Agent (04_AI_DESIGN.MD §4.5)."""

from __future__ import annotations

from app.ai.prompts import latest_version, load_prompt, render_prompt
from app.ai.providers.base import LLMProvider
from app.schemas.ai import ResourceResult

_PROMPT_PREFIX = "detect_resources"


class ResourceAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(self, *, message: str) -> tuple[ResourceResult, str]:
        version = latest_version(_PROMPT_PREFIX)
        template = load_prompt(version)
        system_prompt = render_prompt(template, MESSAGE=message)
        result = await self._llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt="Detect resources now.",
            response_model=ResourceResult,
            prompt_version=version,
        )
        return result, version
