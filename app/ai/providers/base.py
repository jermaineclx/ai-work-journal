"""Provider-agnostic LLM interface.

Every AI agent depends on this abstraction, never on a vendor SDK
directly (02_ARCHITECTURE.md §5.6, ADR-004). Swapping Anthropic for
OpenAI or Gemini means writing one new class here — nothing else in the
application changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract chat/completion provider that always returns validated JSON."""

    name: str

    @abstractmethod
    async def complete_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
        prompt_version: str,
    ) -> ModelT:
        """Call the LLM and return output validated against ``response_model``.

        Implementations must never return free-form text — malformed or
        schema-violating responses should raise ``LLMProviderError``
        rather than being silently coerced, so the Decision Engine can
        fail safely (04_AI_DESIGN.MD §10).
        """
        raise NotImplementedError

    @abstractmethod
    async def complete_text(self, *, system_prompt: str, user_prompt: str, prompt_version: str) -> str:
        """Call the LLM and return raw text (used for free-form summaries)."""
        raise NotImplementedError


class EmbeddingProvider(ABC):
    """Abstract embedding provider used for semantic task matching."""

    name: str
    dimensions: int

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
