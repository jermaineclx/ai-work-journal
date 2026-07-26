"""Extraction Agent — converts natural language into structured entities.

Owns exactly one responsibility (04_AI_DESIGN.MD §4.1): entity
extraction. It never matches tasks, classifies status beyond a raw hint,
or writes to storage.
"""

from __future__ import annotations

from app.ai.prompts import latest_version, load_prompt, render_prompt
from app.ai.providers.base import LLMProvider
from app.schemas.ai import ExtractionResult

_PROMPT_PREFIX = "extract_entities"


class ExtractionAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(
        self,
        *,
        message: str,
        known_stakeholders: list[str],
        known_tasks: list[str],
        known_aliases: dict[str, str],
    ) -> tuple[ExtractionResult, str]:
        version = latest_version(_PROMPT_PREFIX)
        template = load_prompt(version)
        system_prompt = render_prompt(
            template,
            KNOWN_STAKEHOLDERS=", ".join(known_stakeholders) or "(none yet)",
            KNOWN_TASKS=", ".join(known_tasks) or "(none yet)",
            KNOWN_ALIASES=", ".join(f"{k} -> {v}" for k, v in known_aliases.items()) or "(none yet)",
            MESSAGE=message,
        )
        result = await self._llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt="Extract the structured entities now.",
            response_model=ExtractionResult,
            prompt_version=version,
        )
        return result, version
