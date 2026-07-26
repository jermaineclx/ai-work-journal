"""Composition root.

The one place that wires concrete implementations together. Every
layer above this (API routes, Telegram handlers, background jobs) only
ever depends on the service classes, never on how they were built.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.classification import ImpactAgent, ResourceAgent, StatusAgent, TagAgent
from app.ai.embeddings import EmbeddingRefresher
from app.ai.extraction import ExtractionAgent
from app.ai.matching import TaskMatchingAgent
from app.ai.orchestrator import AIOrchestrator
from app.ai.providers import EmbeddingProvider, LLMProvider, build_embedding_provider, build_llm_provider
from app.ai.summarisation import SummaryAgent, WeeklySummaryAgent
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.integrations.sheets import GoogleSheetsClient, ensure_spreadsheet
from app.memory import Database
from app.repositories import DailyLogRepository, MemoryRepository, TaskRepository
from app.services import LogService, ReminderService, SearchService, SummaryService, TaskService

logger = get_logger(__name__)


@dataclass
class Container:
    settings: Settings
    database: Database
    sheets: GoogleSheetsClient
    spreadsheet_id: str
    llm: LLMProvider
    embeddings: EmbeddingProvider
    task_repo: TaskRepository
    log_repo: DailyLogRepository
    memory_repo: MemoryRepository
    orchestrator: AIOrchestrator
    embedding_refresher: EmbeddingRefresher
    summary_agent: SummaryAgent
    log_service: LogService
    task_service: TaskService
    search_service: SearchService
    summary_service: SummaryService
    reminder_service: ReminderService

    @classmethod
    async def create(cls, settings: Settings | None = None) -> Container:
        settings = settings or get_settings()
        configure_logging(settings.log_level)

        database = Database(settings.database_path)
        await database.init()

        memory_repo = MemoryRepository(database)

        sheets = GoogleSheetsClient(
            service_account_json=settings.google_service_account_json,
            service_account_file=settings.google_service_account_file,
        )
        spreadsheet_id = await ensure_spreadsheet(settings, sheets, memory_repo)

        task_repo = TaskRepository(sheets, spreadsheet_id)
        log_repo = DailyLogRepository(sheets, spreadsheet_id)

        llm = build_llm_provider(settings)
        embeddings = build_embedding_provider(settings)

        extraction_agent = ExtractionAgent(llm)
        matching_agent = TaskMatchingAgent(llm, embeddings, memory_repo)
        status_agent = StatusAgent(llm)
        tag_agent = TagAgent(llm)
        resource_agent = ResourceAgent(llm)
        impact_agent = ImpactAgent(llm)
        summary_agent = SummaryAgent(llm)
        weekly_summary_agent = WeeklySummaryAgent(llm)

        orchestrator = AIOrchestrator(
            extraction=extraction_agent,
            matching=matching_agent,
            status=status_agent,
            tags=tag_agent,
            resources=resource_agent,
            impact=impact_agent,
            memory=memory_repo,
        )

        embedding_refresher = EmbeddingRefresher(embeddings, memory_repo)

        log_service = LogService(
            orchestrator=orchestrator,
            summary_agent=summary_agent,
            embedding_refresher=embedding_refresher,
            task_repo=task_repo,
            log_repo=log_repo,
            memory=memory_repo,
            settings=settings,
        )
        task_service = TaskService(task_repo, embedding_refresher)
        search_service = SearchService(task_repo, log_repo, embeddings, memory_repo)
        summary_service = SummaryService(task_repo, log_repo, weekly_summary_agent)
        reminder_service = ReminderService(log_repo)

        logger.info("container_ready", extra={"spreadsheet_id": spreadsheet_id})

        return cls(
            settings=settings,
            database=database,
            sheets=sheets,
            spreadsheet_id=spreadsheet_id,
            llm=llm,
            embeddings=embeddings,
            task_repo=task_repo,
            log_repo=log_repo,
            memory_repo=memory_repo,
            orchestrator=orchestrator,
            embedding_refresher=embedding_refresher,
            summary_agent=summary_agent,
            log_service=log_service,
            task_service=task_service,
            search_service=search_service,
            summary_service=summary_service,
            reminder_service=reminder_service,
        )
