"""FastAPI application factory (03_IMPLEMENTATION.md §17)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.container import Container
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.integrations.telegram.bot import build_application, configure_bot_commands, configure_webhook
from app.jobs.scheduler import build_scheduler
from app.schemas.api import ErrorResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    container = await Container.create(settings)
    app.state.container = container

    telegram_application = build_application(settings, container)
    await telegram_application.initialize()
    await configure_webhook(telegram_application, settings)
    await configure_bot_commands(telegram_application)
    app.state.telegram_application = telegram_application

    scheduler = build_scheduler(container, telegram_application.bot)
    scheduler.start()
    app.state.scheduler = scheduler

    logger.info("application_started", extra={"environment": settings.environment})
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await telegram_application.shutdown()
        logger.info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(api_router)

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("app_error", extra={"code": exc.code, "path": request.url.path})
        return JSONResponse(status_code=exc.http_status, content=ErrorResponse(error=exc.message).model_dump())

    return app
