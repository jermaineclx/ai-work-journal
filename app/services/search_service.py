"""SearchService (FR8) — natural language retrieval over Tasks and Daily Logs.

MVP scope: Tasks are matched semantically via stored embeddings (the
only entities embedded per 04_AI_DESIGN.MD §7). Daily Logs are matched
by keyword overlap — full semantic search over individual logs and
date-range natural-language parsing ("last week", "in March") are
listed as Phase 2 ("smarter search") in 01_PRD.md §19 and intentionally
not built here.
"""

from __future__ import annotations

import re

from app.ai.matching.similarity import top_k_similar
from app.ai.providers.base import EmbeddingProvider
from app.repositories import DailyLogRepository, MemoryRepository, TaskRepository
from app.schemas.search import SearchResponse, SearchResultLog, SearchResultTask

_MIN_TASK_SIMILARITY = 0.25
_MAX_RESULTS = 8


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}


class SearchService:
    def __init__(
        self,
        task_repo: TaskRepository,
        log_repo: DailyLogRepository,
        embeddings: EmbeddingProvider,
        memory: MemoryRepository,
    ) -> None:
        self._tasks = task_repo
        self._logs = log_repo
        self._embeddings = embeddings
        self._memory = memory

    async def search(self, query: str) -> SearchResponse:
        tasks = await self._tasks.get_all()
        logs = await self._logs.get_all()

        matched_tasks: list[SearchResultTask] = []
        stored_embeddings = await self._memory.get_all_embeddings()
        tasks_by_id = {t.task_id: t for t in tasks}
        available = {tid: vec for tid, vec in stored_embeddings.items() if tid in tasks_by_id}
        if available:
            query_vector = await self._embeddings.embed(query)
            for task_id, score in top_k_similar(query_vector, available, _MAX_RESULTS):
                if score < _MIN_TASK_SIMILARITY:
                    continue
                task = tasks_by_id[task_id]
                matched_tasks.append(
                    SearchResultTask(
                        task_id=task.task_id,
                        title=task.title,
                        stakeholder=task.stakeholder,
                        status=task.status,
                        summary=task.summary,
                        similarity=score,
                    )
                )

        query_tokens = _tokenize(query)
        scored_logs: list[tuple[int, SearchResultLog]] = []
        for log in logs:
            haystack = f"{log.original_message} {' '.join(log.stakeholder)} {' '.join(log.tags)}"
            overlap = len(query_tokens & _tokenize(haystack))
            if overlap == 0:
                continue
            task = tasks_by_id.get(log.task_id)
            scored_logs.append(
                (
                    overlap,
                    SearchResultLog(
                        log_id=log.log_id,
                        task_id=log.task_id,
                        task_title=task.title if task else log.task_id,
                        date=log.date,
                        original_message=log.original_message,
                        status=log.status,
                    ),
                )
            )
        scored_logs.sort(key=lambda pair: pair[0], reverse=True)
        matched_logs = [item for _, item in scored_logs[:_MAX_RESULTS]]

        highlights = [t.title for t in matched_tasks[:3]]

        return SearchResponse(query=query, tasks=matched_tasks, logs=matched_logs, highlights=highlights)
