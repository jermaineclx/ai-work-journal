"""AI Orchestrator (02_ARCHITECTURE.md §5.4, 03_IMPLEMENTATION.md §19).

Coordinates the specialised agents and returns one consolidated
`AIPipelineOutput`. Contains no prompt logic of its own — only the
deterministic glue (alias resolution, confidence selection) between
agent calls. This object never writes to storage; that is the
Decision Engine's and Application Service's job.

Deliberate deviation from the literal pipeline diagram in
03_IMPLEMENTATION.md §19 (which lists Summary Update before the
Decision Engine): summary regeneration only touches the Task the user
has *confirmed*, so it happens after confirmation (in `LogService`),
not speculatively for a match that might be rejected or corrected. This
keeps unconfirmed LLM output away from persisted summaries, per
01_PRD.md §13 ("No significant changes should occur silently").
"""

from __future__ import annotations

from app.ai.classification import ImpactAgent, ResourceAgent, StatusAgent, TagAgent
from app.ai.extraction import ExtractionAgent
from app.ai.matching import TaskMatchingAgent
from app.domain.entities import Task
from app.domain.enums import Stakeholder
from app.repositories.memory_repository import MemoryRepository
from app.schemas.ai import AIPipelineOutput, ExtractionResult, MatchResult


class AIOrchestrator:
    def __init__(
        self,
        *,
        extraction: ExtractionAgent,
        matching: TaskMatchingAgent,
        status: StatusAgent,
        tags: TagAgent,
        resources: ResourceAgent,
        impact: ImpactAgent,
        memory: MemoryRepository,
    ) -> None:
        self._extraction = extraction
        self._matching = matching
        self._status = status
        self._tags = tags
        self._resources = resources
        self._impact = impact
        self._memory = memory

    async def run(self, *, message: str, tasks: list[Task]) -> AIPipelineOutput:
        tasks_by_id = {t.task_id: t for t in tasks}
        known_stakeholders = [s.value for s in Stakeholder]
        known_tasks = [t.title for t in tasks]
        known_tags = sorted({tag for t in tasks for tag in t.tags})

        stakeholder_aliases = await self._memory.list_aliases("stakeholder")
        task_aliases = await self._memory.list_aliases("task")
        known_aliases = {**stakeholder_aliases, **task_aliases}

        extraction, extraction_version = await self._extraction.run(
            message=message,
            known_stakeholders=known_stakeholders,
            known_tasks=known_tasks,
            known_aliases=known_aliases,
        )

        extraction = await self._normalize_extraction(extraction)

        match, match_version = await self._matching.run(message=message, extraction=extraction, tasks=tasks)

        prior_task = tasks_by_id.get(match.matched_task_id) if match.matched_task_id else None

        status_result, status_version = await self._status.run(
            message=message,
            status_hint=extraction.status_hint,
            prior_status=prior_task.status if prior_task else None,
        )

        tags_result, tags_version = await self._tags.run(message=message, extraction=extraction, known_tags=known_tags)
        resources_result, resources_version = await self._resources.run(message=message)
        impact_result, impact_version = await self._impact.run(
            message=message, extraction=extraction, status=status_result.status
        )

        overall_confidence = match.confidence if match.matched_task_id else extraction.extraction_confidence

        return AIPipelineOutput(
            extraction=extraction,
            match=match,
            status=status_result,
            tags=tags_result,
            resources=resources_result,
            impact=impact_result,
            summary=None,
            overall_confidence=overall_confidence,
            prompt_versions={
                "extraction": extraction_version,
                "matching": match_version,
                "status": status_version,
                "tags": tags_version,
                "resources": resources_version,
                "impact": impact_version,
            },
        )

    async def describe_new_task(self, *, message: str, tasks: list[Task]) -> AIPipelineOutput:
        """Like `run()`, but skips Task Matching entirely.

        Used when the user explicitly commands task creation (`/new_task`)
        rather than leaving the AI to decide whether this is new or
        existing work — there is nothing to match against by definition.
        """
        known_stakeholders = [s.value for s in Stakeholder]
        known_tasks = [t.title for t in tasks]
        known_tags = sorted({tag for t in tasks for tag in t.tags})

        stakeholder_aliases = await self._memory.list_aliases("stakeholder")
        task_aliases = await self._memory.list_aliases("task")
        known_aliases = {**stakeholder_aliases, **task_aliases}

        extraction, extraction_version = await self._extraction.run(
            message=message,
            known_stakeholders=known_stakeholders,
            known_tasks=known_tasks,
            known_aliases=known_aliases,
        )

        extraction = await self._normalize_extraction(extraction)

        match = MatchResult(
            matched_task_id=None, confidence=0.0, candidates=[], explanation=["Explicitly created via /new_task."]
        )

        status_result, status_version = await self._status.run(
            message=message, status_hint=extraction.status_hint, prior_status=None
        )
        tags_result, tags_version = await self._tags.run(message=message, extraction=extraction, known_tags=known_tags)
        resources_result, resources_version = await self._resources.run(message=message)
        impact_result, impact_version = await self._impact.run(
            message=message, extraction=extraction, status=status_result.status
        )

        return AIPipelineOutput(
            extraction=extraction,
            match=match,
            status=status_result,
            tags=tags_result,
            resources=resources_result,
            impact=impact_result,
            summary=None,
            overall_confidence=extraction.extraction_confidence,
            prompt_versions={
                "extraction": extraction_version,
                "status": status_version,
                "tags": tags_version,
                "resources": resources_version,
                "impact": impact_version,
            },
        )

    async def _normalize_extraction(self, extraction: ExtractionResult) -> ExtractionResult:
        """Applies learned aliases, then validates the stakeholder against
        the fixed roster (04_AI_DESIGN.MD §10, Hallucination Prevention) —
        a name the AI wrote that isn't a known coworker and wasn't resolved
        by a learned alias gets nulled out rather than trusted verbatim."""
        updates: dict[str, str | None] = {}
        if extraction.stakeholder:
            canonical = await self._memory.resolve_alias(extraction.stakeholder, "stakeholder")
            if canonical:
                updates["stakeholder"] = canonical
        if extraction.task_title:
            canonical = await self._memory.resolve_alias(extraction.task_title, "task")
            if canonical:
                updates["task_title"] = canonical
        extraction = extraction.model_copy(update=updates) if updates else extraction

        resolved_stakeholder = Stakeholder.parse(extraction.stakeholder)
        canonical_value = resolved_stakeholder.value if resolved_stakeholder else None
        if canonical_value != extraction.stakeholder:
            extraction = extraction.model_copy(update={"stakeholder": canonical_value})

        return extraction
