"""AIOrchestrator tests using fake agents — verifies the deterministic
glue (which agents run, how overall_confidence is picked) without any
real LLM calls.
"""

from __future__ import annotations

import pytest

from app.ai.orchestrator import AIOrchestrator
from app.domain.entities import Task
from app.domain.enums import ImpactLevel, TaskStatus
from app.schemas.ai import (
    ExtractionResult,
    ImpactResult,
    MatchResult,
    ResourceResult,
    StatusResult,
    TagResult,
)


class FakeExtractionAgent:
    async def run(self, *, message, known_stakeholders, known_tasks, known_aliases):
        return ExtractionResult(task_title="Budget Projection", stakeholder=None, extraction_confidence=0.72), "v1"


class FakeMatchingAgent:
    def __init__(self):
        self.called = False

    async def run(self, *, message, extraction, tasks):
        self.called = True
        return MatchResult(matched_task_id="SHOULD_NOT_BE_USED", confidence=0.99), "v1"


class FakeStatusAgent:
    def __init__(self):
        self.received_prior_status = "unset"

    async def run(self, *, message, status_hint, prior_status):
        self.received_prior_status = prior_status
        return StatusResult(status=TaskStatus.IN_PROGRESS, confidence=0.8), "v1"


class FakeTagAgent:
    async def run(self, *, message, extraction, known_tags):
        return TagResult(tags=["Finance"]), "v1"


class FakeResourceAgent:
    async def run(self, *, message):
        return ResourceResult(resources=[]), "v1"


class FakeImpactAgent:
    async def run(self, *, message, extraction, status):
        return ImpactResult(impact=ImpactLevel.MEDIUM), "v1"


class FakeMemoryRepository:
    async def list_aliases(self, alias_type: str) -> dict[str, str]:
        return {}

    async def resolve_alias(self, alias: str, alias_type: str) -> str | None:
        return None


def _make_orchestrator(matching_agent):
    return AIOrchestrator(
        extraction=FakeExtractionAgent(),
        matching=matching_agent,
        status=FakeStatusAgent(),
        tags=FakeTagAgent(),
        resources=FakeResourceAgent(),
        impact=FakeImpactAgent(),
        memory=FakeMemoryRepository(),
    )


@pytest.mark.asyncio
async def test_describe_new_task_never_calls_matching_agent():
    matching_agent = FakeMatchingAgent()
    orchestrator = _make_orchestrator(matching_agent)

    output = await orchestrator.describe_new_task(message="Worked on the budget projection.", tasks=[])

    assert matching_agent.called is False
    assert output.match.matched_task_id is None
    assert output.extraction.task_title == "Budget Projection"
    assert orchestrator._status.received_prior_status is None


@pytest.mark.asyncio
async def test_describe_new_task_uses_extraction_confidence_as_overall():
    orchestrator = _make_orchestrator(FakeMatchingAgent())

    output = await orchestrator.describe_new_task(message="Worked on the budget projection.", tasks=[])

    assert output.overall_confidence == 0.72


@pytest.mark.asyncio
async def test_run_uses_match_confidence_when_matched():
    class MatchingAgentReturningMatch:
        async def run(self, *, message, extraction, tasks):
            return MatchResult(matched_task_id="T001", matched_task_title="Existing", confidence=0.9), "v1"

    orchestrator = _make_orchestrator(MatchingAgentReturningMatch())
    existing_task = Task(task_id="T001", title="Existing", stakeholder="Finance", status=TaskStatus.IN_PROGRESS)

    output = await orchestrator.run(message="Finance approved.", tasks=[existing_task])

    assert output.overall_confidence == 0.9
    assert output.match.matched_task_id == "T001"
