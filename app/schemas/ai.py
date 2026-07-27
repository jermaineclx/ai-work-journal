"""Structured I/O contracts for the AI layer.

Every AI agent returns one of these validated models rather than free text.
Keeping AI output isolated in dedicated schemas (rather than reusing domain
entities) makes debugging and prompt evaluation significantly easier, per
03_IMPLEMENTATION.md §12 (AIExtraction) and §19 (Structured Outputs).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.enums import ImpactLevel, TaskStatus


class ExtractionResult(BaseModel):
    """Output of the Extraction Agent."""

    task_title: str | None = Field(default=None, description="Best-guess name for the workstream")
    stakeholder: list[str] = Field(default_factory=list, description="Zero or more people mentioned")
    status_hint: str | None = Field(default=None, description="Raw status language before classification")
    next_steps: str | None = None
    resource_mentions: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    log_summary: str = Field(
        default="", description="Coherent, organized restatement of the raw message for future reference"
    )
    extraction_confidence: float = Field(ge=0.0, le=1.0)


class MatchCandidateResult(BaseModel):
    task_id: str
    title: str
    similarity: float = Field(ge=0.0, le=1.0)


class MatchResult(BaseModel):
    """Output of the Task Matching Agent."""

    matched_task_id: str | None = None
    matched_task_title: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    candidates: list[MatchCandidateResult] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list, description="Human-readable reasons for the match")


class StatusResult(BaseModel):
    """Output of the Status Classification Agent."""

    status: TaskStatus
    confidence: float = Field(ge=0.0, le=1.0)


class TagResult(BaseModel):
    tags: list[str] = Field(default_factory=list)


class ResourceResult(BaseModel):
    resources: list[str] = Field(default_factory=list)


class ImpactResult(BaseModel):
    impact: ImpactLevel = ImpactLevel.INFORMATIONAL
    rationale: str | None = None


class SummaryResult(BaseModel):
    """Output of the Summary Agent: a rewritten (not appended) task summary."""

    summary: str


class AIPipelineOutput(BaseModel):
    """The single consolidated object the AI Orchestrator returns.

    This becomes the input to the deterministic Decision Engine. No agent
    in this pipeline ever writes to storage directly.
    """

    extraction: ExtractionResult
    match: MatchResult
    status: StatusResult
    tags: TagResult
    resources: ResourceResult
    impact: ImpactResult
    summary: SummaryResult | None = None
    overall_confidence: float = Field(ge=0.0, le=1.0)
    prompt_versions: dict[str, str] = Field(default_factory=dict)
