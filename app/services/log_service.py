"""LogService — the primary entry point for processing a Daily Log
(02_ARCHITECTURE.md §5.3, 03_IMPLEMENTATION.md §16).

Orchestrates: idempotency check -> AI pipeline -> deterministic Decision
Engine -> either immediate persistence (high confidence) or a persisted
pending confirmation awaiting a Telegram button tap.

Learning rule enforced here (not in the AI layer): confidence-history and
alias records are only written from `confirm()` — i.e. after an explicit
user action — never from the auto-apply path, per 01_PRD.md §14
("The system learns only from confirmed user behaviour").
"""

from __future__ import annotations

from datetime import date

from app.ai.embeddings import EmbeddingRefresher
from app.ai.orchestrator import AIOrchestrator
from app.ai.summarisation import SummaryAgent
from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.domain.entities import DailyLog, Task
from app.domain.enums import DecisionAction, ImpactLevel, TaskStatus
from app.domain.rules.decision import TaskMatchCandidate, decide
from app.repositories import DailyLogRepository, MemoryRepository, TaskRepository
from app.schemas.ai import AIPipelineOutput
from app.schemas.decision import decision_to_schema
from app.schemas.log_result import LogOutcome
from app.schemas.pending import PendingConfirmation

logger = get_logger(__name__)


class LogService:
    def __init__(
        self,
        *,
        orchestrator: AIOrchestrator,
        summary_agent: SummaryAgent,
        embedding_refresher: EmbeddingRefresher,
        task_repo: TaskRepository,
        log_repo: DailyLogRepository,
        memory: MemoryRepository,
        settings: Settings,
    ) -> None:
        self._orchestrator = orchestrator
        self._summary_agent = summary_agent
        self._embeddings = embedding_refresher
        self._tasks = task_repo
        self._logs = log_repo
        self._memory = memory
        self._settings = settings

    async def process_message(self, *, request_id: str, user_id: str, message: str) -> LogOutcome:
        cached = await self._memory.get_processed_request(request_id)
        if cached:
            logger.info("duplicate_request_replayed", extra={"request_id": request_id})
            return LogOutcome.model_validate_json(cached)

        tasks = await self._tasks.get_all()
        ai_output = await self._orchestrator.run(message=message, tasks=tasks)

        best_match = None
        if ai_output.match.matched_task_id:
            best_match = TaskMatchCandidate(
                task_id=ai_output.match.matched_task_id,
                title=ai_output.match.matched_task_title or "",
                similarity=ai_output.match.confidence,
            )
        candidates = [
            TaskMatchCandidate(task_id=c.task_id, title=c.title, similarity=c.similarity)
            for c in ai_output.match.candidates
        ]
        decision = decide(
            confidence=ai_output.overall_confidence,
            best_match=best_match,
            candidates=candidates,
            auto_apply_threshold=self._settings.confidence_auto_apply,
            confirm_threshold=self._settings.confidence_confirm_lower_bound,
        )
        logger.info(
            "decision_made",
            extra={"request_id": request_id, "action": decision.action.value, "confidence": decision.confidence},
        )

        if decision.action in (DecisionAction.AUTO_SAVE_EXISTING_TASK, DecisionAction.AUTO_SAVE_NEW_TASK):
            outcome = await self._commit(
                request_id=request_id,
                message=message,
                ai_output=ai_output,
                task_id=decision.matched_task_id,
                create_new=decision.action == DecisionAction.AUTO_SAVE_NEW_TASK,
                auto_applied=True,
            )
            await self._memory.mark_request_processed(request_id, outcome.model_dump_json())
            return outcome

        pending = PendingConfirmation(
            request_id=request_id,
            user_id=user_id,
            original_message=message,
            ai_output=ai_output,
            decision=decision_to_schema(decision),
        )
        await self._memory.save_pending_confirmation(request_id, user_id, pending.model_dump_json())

        return LogOutcome(
            status="pending_confirmation",
            request_id=request_id,
            decision=decision_to_schema(decision),
            proposed_task_title=ai_output.extraction.task_title,
            proposed_stakeholder=ai_output.extraction.stakeholder,
            proposed_status=ai_output.status.status,
            candidates=decision_to_schema(decision).candidates,
            confidence=ai_output.overall_confidence,
        )

    async def confirm(self, *, request_id: str, chosen_task_id: str | None, create_new: bool) -> LogOutcome:
        payload_json = await self._memory.get_pending_confirmation(request_id)
        if not payload_json:
            raise NotFoundError(f"No pending confirmation for request '{request_id}' (it may have expired)")
        pending = PendingConfirmation.model_validate_json(payload_json)
        ai_output = pending.ai_output

        outcome = await self._commit(
            request_id=request_id,
            message=pending.original_message,
            ai_output=ai_output,
            task_id=chosen_task_id,
            create_new=create_new,
            auto_applied=False,
        )

        matched_by_ai = ai_output.match.matched_task_id
        user_agreed_with_match = (not create_new) and chosen_task_id == matched_by_ai
        user_agreed_new = create_new and matched_by_ai is None
        await self._memory.record_confidence_outcome(
            request_id=request_id,
            task_id=chosen_task_id,
            stage="task_matching",
            predicted_confidence=ai_output.overall_confidence,
            user_accepted=user_agreed_with_match or user_agreed_new,
        )

        if not create_new and chosen_task_id and chosen_task_id != matched_by_ai and ai_output.extraction.task_title:
            chosen_task = await self._tasks.require_by_id(chosen_task_id)
            await self._memory.learn_alias(ai_output.extraction.task_title, chosen_task.title, "task")

        await self._memory.mark_request_processed(request_id, outcome.model_dump_json())
        await self._memory.delete_pending_confirmation(request_id)
        return outcome

    async def cancel(self, *, request_id: str) -> None:
        await self._memory.delete_pending_confirmation(request_id)

    async def undo_last(self) -> DailyLog | None:
        """Delete the most recently saved Daily Log (01_PRD.md §13, Reversible Actions).

        Single-user MVP, so "last action" is unambiguous. This removes the
        log row and decrements the task's update counter, but deliberately
        does not attempt to recompute status/summary/tags retroactively
        from the remaining history — those reflect the task's last known
        good state until the next real update arrives.
        """
        latest = await self._logs.get_latest()
        if latest is None:
            return None
        await self._logs.delete(latest.log_id)
        task = await self._tasks.get_by_id(latest.task_id)
        if task is not None:
            task.total_updates = max(0, task.total_updates - 1)
            await self._tasks.update(task)
        return latest

    async def create_task_explicitly(self, *, request_id: str, message: str, ai_output: AIPipelineOutput) -> LogOutcome:
        """Create a task the user explicitly asked for (`/new_task`), skipping
        the Decision Engine entirely — there's nothing to decide, the user
        already told us this is new work. `ai_output` should come from
        `AIOrchestrator.describe_new_task`, with `extraction.stakeholder`
        already overridden to whatever the user specified."""
        cached = await self._memory.get_processed_request(request_id)
        if cached:
            return LogOutcome.model_validate_json(cached)

        outcome = await self._commit(
            request_id=request_id,
            message=message,
            ai_output=ai_output,
            task_id=None,
            create_new=True,
            auto_applied=False,
        )
        await self._memory.mark_request_processed(request_id, outcome.model_dump_json())
        return outcome

    async def list_logs_for_task(self, task_id: str) -> list[DailyLog]:
        logs = await self._logs.get_by_task(task_id)
        return sorted(logs, key=lambda log: log.timestamp, reverse=True)

    async def search_logs(self, *, task_id: str | None = None, on_date: date | None = None) -> list[DailyLog]:
        """Most-recent-first, optionally filtered by task and/or date —
        backs the /all_logs command."""
        logs = await self._logs.get_all()
        if task_id is not None:
            logs = [log for log in logs if log.task_id == task_id]
        if on_date is not None:
            logs = [log for log in logs if log.date == on_date]
        return sorted(logs, key=lambda log: log.timestamp, reverse=True)

    async def get_log(self, log_id: str) -> DailyLog:
        return await self._logs.require_by_id(log_id)

    async def edit_log_stakeholder(self, log_id: str, stakeholder: str) -> DailyLog:
        log = await self._logs.require_by_id(log_id)
        log.stakeholder = stakeholder
        await self._logs.update_extracted_fields(log)
        return log

    async def edit_log_status(self, log_id: str, status: TaskStatus) -> DailyLog:
        log = await self._logs.require_by_id(log_id)
        log.status = status
        await self._logs.update_extracted_fields(log)
        return log

    async def edit_log_next_steps(self, log_id: str, next_steps: str) -> DailyLog:
        log = await self._logs.require_by_id(log_id)
        log.next_steps = next_steps
        await self._logs.update_extracted_fields(log)
        return log

    async def edit_log_tags(self, log_id: str, tags: list[str]) -> DailyLog:
        log = await self._logs.require_by_id(log_id)
        log.tags = tags
        await self._logs.update_extracted_fields(log)
        return log

    async def edit_log_resources(self, log_id: str, resources: list[str]) -> DailyLog:
        log = await self._logs.require_by_id(log_id)
        log.resources = resources
        await self._logs.update_extracted_fields(log)
        return log

    async def edit_log_impact(self, log_id: str, impact: ImpactLevel) -> DailyLog:
        log = await self._logs.require_by_id(log_id)
        log.impact = impact
        await self._logs.update_extracted_fields(log)
        return log

    async def edit_log_date(self, log_id: str, new_date: date) -> DailyLog:
        """Corrects which day the work happened on — e.g. logging
        yesterday's update the next morning. Does not touch `timestamp`,
        which always reflects when the log was actually submitted."""
        log = await self._logs.require_by_id(log_id)
        log.date = new_date
        await self._logs.update_extracted_fields(log)
        return log

    async def _commit(
        self,
        *,
        request_id: str,
        message: str,
        ai_output,
        task_id: str | None,
        create_new: bool,
        auto_applied: bool,
    ) -> LogOutcome:
        status = ai_output.status.status

        if create_new:
            new_id = await self._tasks.next_task_id()
            task = Task(
                task_id=new_id,
                title=ai_output.extraction.task_title or "Untitled Task",
                stakeholder=ai_output.extraction.stakeholder or "",
                status=status,
            )
            summary_result, _ = await self._summary_agent.run(
                task_title=task.title, current_summary="", message=message, status=status
            )
            task.summary = summary_result.summary
            task.apply_update(status=status, new_tags=ai_output.tags.tags, new_resources=ai_output.resources.resources)
            await self._tasks.create(task)
        else:
            if not task_id:
                raise NotFoundError("A task_id is required when create_new is False")
            task = await self._tasks.require_by_id(task_id)
            summary_result, _ = await self._summary_agent.run(
                task_title=task.title, current_summary=task.summary, message=message, status=status
            )
            task.summary = summary_result.summary
            task.apply_update(status=status, new_tags=ai_output.tags.tags, new_resources=ai_output.resources.resources)
            await self._tasks.update(task)

        await self._embeddings.refresh(task)

        log_id = await self._logs.next_log_id()
        daily_log = DailyLog(
            log_id=log_id,
            task_id=task.task_id,
            date=date.today(),
            original_message=message,
            stakeholder=ai_output.extraction.stakeholder,
            status=status,
            next_steps=ai_output.extraction.next_steps,
            resources=ai_output.resources.resources,
            tags=ai_output.tags.tags,
            impact=ai_output.impact.impact,
            request_id=request_id,
        )
        await self._logs.append(daily_log)

        return LogOutcome(
            status="committed",
            request_id=request_id,
            task_id=task.task_id,
            task_title=task.title,
            task_status=task.status,
            stakeholder=task.stakeholder,
            is_new_task=create_new,
            auto_applied=auto_applied,
            summary=task.summary,
            tags=task.tags,
            log_id=log_id,
        )
