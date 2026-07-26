"""Builds the configured LLM/embedding providers from application settings.

This is the single place that knows how to translate `llm_provider` /
`embedding_provider` settings into concrete classes. Everything else
depends only on the `LLMProvider` / `EmbeddingProvider` interfaces.
"""

from __future__ import annotations

from functools import lru_cache

from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.core.config import Settings, get_settings
from app.core.exceptions import LLMProviderError


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "anthropic":
        from app.ai.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
    raise LLMProviderError(f"Unsupported llm_provider: {settings.llm_provider}")


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        from app.ai.providers.openai_embeddings import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(api_key=settings.openai_api_key, model=settings.embedding_model)
    raise LLMProviderError(f"Unsupported embedding_provider: {settings.embedding_provider}")


@lru_cache
def get_llm_provider() -> LLMProvider:
    return build_llm_provider(get_settings())


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return build_embedding_provider(get_settings())
