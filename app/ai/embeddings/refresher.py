"""Embedding lifecycle management for Tasks (04_AI_DESIGN.MD §7).

A Task's embedding should be regenerated whenever its summary, title or
tags change meaningfully. This module owns *when/how* to refresh; the
raw embedding call itself lives behind the `EmbeddingProvider` interface.
"""

from __future__ import annotations

from app.ai.matching.agent import build_task_embedding_text
from app.ai.providers.base import EmbeddingProvider
from app.domain.entities import Task
from app.repositories.memory_repository import MemoryRepository


class EmbeddingRefresher:
    def __init__(self, embeddings: EmbeddingProvider, memory: MemoryRepository) -> None:
        self._embeddings = embeddings
        self._memory = memory

    async def refresh(self, task: Task) -> None:
        source_text = build_task_embedding_text(task)
        vector = await self._embeddings.embed(source_text)
        await self._memory.save_embedding(task.task_id, vector, self._embeddings.name, source_text)

    async def refresh_all(self, tasks: list[Task]) -> None:
        if not tasks:
            return
        texts = [build_task_embedding_text(t) for t in tasks]
        vectors = await self._embeddings.embed_batch(texts)
        for task, text, vector in zip(tasks, texts, vectors, strict=True):
            await self._memory.save_embedding(task.task_id, vector, self._embeddings.name, text)
