"""OpenAI embeddings implementation, used purely for semantic task matching.

This is intentionally the only place `openai` is imported outside of the
provider layer — the chat/completion LLM provider is Anthropic, but
embeddings are sourced from OpenAI's `text-embedding-3-large` per the
AI Design doc's stated tech choice. Nothing else in the app should know
which vendor generates embeddings.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.ai.providers.base import EmbeddingProvider
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)

_DIMENSIONS = {
    "text-embedding-3-large": 3072,
    "text-embedding-3-small": 1536,
}


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "text-embedding-3-large") -> None:
        if not api_key:
            raise LLMProviderError("OPENAI_API_KEY is not configured")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self.dimensions = _DIMENSIONS.get(model, 1536)

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = await self._client.embeddings.create(model=self._model, input=texts)
        except Exception as exc:  # noqa: BLE001
            logger.error("openai_embedding_failed", extra={"error": str(exc), "count": len(texts)})
            raise LLMProviderError(f"OpenAI embedding request failed: {exc}") from exc
        return [item.embedding for item in response.data]
