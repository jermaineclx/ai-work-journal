"""Anthropic Claude implementation of the LLMProvider interface.

Structured output is obtained via forced tool-use: we register a single
synthetic tool whose input schema is the caller's Pydantic model, force
``tool_choice`` to that tool, and validate the tool call's input against
the model. This is more reliable than asking Claude to "return only
JSON" in prose.
"""

from __future__ import annotations

from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel, ValidationError

from app.ai.providers.base import LLMProvider
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)

_TOOL_NAME = "emit_structured_result"


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, max_tokens: int = 1024) -> None:
        if not api_key:
            raise LLMProviderError("ANTHROPIC_API_KEY is not configured")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def complete_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
        prompt_version: str,
    ) -> ModelT:
        schema = response_model.model_json_schema()
        schema.pop("title", None)
        tool = {
            "name": _TOOL_NAME,
            "description": f"Emit the structured result for {response_model.__name__}.",
            "input_schema": schema,
        }
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system_prompt,
                tools=[tool],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as exc:  # noqa: BLE001 - normalise every provider failure
            logger.error("anthropic_request_failed", extra={"prompt_version": prompt_version, "error": str(exc)})
            raise LLMProviderError(f"Anthropic request failed: {exc}") from exc

        tool_use_block = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_use_block is None:
            raise LLMProviderError("Anthropic response did not contain a tool_use block")

        try:
            return response_model.model_validate(tool_use_block.input)
        except ValidationError as exc:
            logger.error(
                "anthropic_schema_validation_failed",
                extra={"prompt_version": prompt_version, "error": str(exc)},
            )
            raise LLMProviderError(f"Anthropic output failed schema validation: {exc}") from exc

    async def complete_text(self, *, system_prompt: str, user_prompt: str, prompt_version: str) -> str:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("anthropic_request_failed", extra={"prompt_version": prompt_version, "error": str(exc)})
            raise LLMProviderError(f"Anthropic request failed: {exc}") from exc

        text_block = next((b for b in response.content if b.type == "text"), None)
        if text_block is None:
            raise LLMProviderError("Anthropic response did not contain a text block")
        return text_block.text.strip()
