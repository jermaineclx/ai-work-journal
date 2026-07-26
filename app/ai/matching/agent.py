"""Task Matching Agent (04_AI_DESIGN.MD §4.2).

Hybrid retrieval: embeddings narrow the field to a handful of plausible
candidates, then the LLM re-ranks with full context. Reading embeddings
via MemoryRepository is retrieval-augmented generation, not a storage
write, so it stays within the AI layer's remit (04_AI_DESIGN.MD §6-7);
the agent never writes anything back.
"""

from __future__ import annotations

from app.ai.matching.similarity import top_k_similar
from app.ai.prompts import latest_version, load_prompt, render_prompt
from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.core.constants import MAX_SIMILARITY_CANDIDATES
from app.domain.entities import Task
from app.repositories.memory_repository import MemoryRepository
from app.schemas.ai import ExtractionResult, MatchCandidateResult, MatchResult

_PROMPT_PREFIX = "match_task"


def build_task_embedding_text(task: Task) -> str:
    """Canonical text used to embed a Task — kept identical everywhere
    a task embedding is generated so refreshes stay comparable."""
    parts = [task.title, ", ".join(task.stakeholder), task.summary, ", ".join(task.tags)]
    return " | ".join(p for p in parts if p)


class TaskMatchingAgent:
    def __init__(self, llm: LLMProvider, embeddings: EmbeddingProvider, memory: MemoryRepository) -> None:
        self._llm = llm
        self._embeddings = embeddings
        self._memory = memory

    async def run(
        self,
        *,
        message: str,
        extraction: ExtractionResult,
        tasks: list[Task],
    ) -> tuple[MatchResult, str]:
        version = latest_version(_PROMPT_PREFIX)

        if not tasks:
            return (
                MatchResult(
                    matched_task_id=None, confidence=0.0, candidates=[], explanation=["No existing tasks yet."]
                ),
                version,
            )

        stakeholder_text = ", ".join(extraction.stakeholder) if extraction.stakeholder else None
        query_text = " | ".join(p for p in [extraction.task_title, stakeholder_text, message] if p)
        query_vector = await self._embeddings.embed(query_text)
        stored_embeddings = await self._memory.get_all_embeddings()

        tasks_by_id = {t.task_id: t for t in tasks}
        available_embeddings = {tid: vec for tid, vec in stored_embeddings.items() if tid in tasks_by_id}

        if not available_embeddings:
            return (
                MatchResult(
                    matched_task_id=None,
                    confidence=0.0,
                    candidates=[],
                    explanation=["No task embeddings available yet."],
                ),
                version,
            )

        top = top_k_similar(query_vector, available_embeddings, MAX_SIMILARITY_CANDIDATES)
        candidates = [
            MatchCandidateResult(task_id=tid, title=tasks_by_id[tid].title, similarity=score) for tid, score in top
        ]

        candidates_text = "\n".join(
            f"- [{c.task_id}] {c.title} (stakeholder: {', '.join(tasks_by_id[c.task_id].stakeholder) or '—'}, "
            f"similarity: {c.similarity:.0%}, summary: {tasks_by_id[c.task_id].summary or '(none)'})"
            for c in candidates
        )

        template = load_prompt(version)
        system_prompt = render_prompt(
            template,
            EXTRACTED_ENTITIES=extraction.model_dump_json(),
            MESSAGE=message,
            CANDIDATES=candidates_text,
        )
        result = await self._llm.complete_structured(
            system_prompt=system_prompt,
            user_prompt="Decide the best match now.",
            response_model=MatchResult,
            prompt_version=version,
        )

        valid_ids = {c.task_id for c in candidates}
        if result.matched_task_id and result.matched_task_id not in valid_ids:
            # Guard against hallucinated task IDs (04_AI_DESIGN.MD §10).
            result = result.model_copy(update={"matched_task_id": None, "confidence": min(result.confidence, 0.5)})
        result = result.model_copy(update={"candidates": candidates})
        return result, version
