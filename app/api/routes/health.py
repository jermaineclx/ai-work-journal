"""Health/readiness/version endpoints (03_IMPLEMENTATION.md §17)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.core.container import Container
from app.core.logging import get_logger
from app.schemas.api import HealthResponse, VersionResponse

logger = get_logger(__name__)
router = APIRouter()

APP_VERSION = "0.1.0"


@router.get("/health", response_model=HealthResponse)
async def health(container: Container = Depends(get_container)) -> HealthResponse:
    checks = {"sqlite": False, "google_sheets": False}

    try:
        await container.memory_repo.get_preference("__health_check__")
        checks["sqlite"] = True
    except Exception:  # noqa: BLE001
        logger.warning("health_check_sqlite_failed")

    try:
        await container.task_repo.get_all()
        checks["google_sheets"] = True
    except Exception:  # noqa: BLE001
        logger.warning("health_check_sheets_failed")

    status = "healthy" if all(checks.values()) else "degraded"
    return HealthResponse(status=status, checks=checks)


@router.get("/version", response_model=VersionResponse)
async def version(container: Container = Depends(get_container)) -> VersionResponse:
    return VersionResponse(
        name=container.settings.app_name, version=APP_VERSION, environment=container.settings.environment
    )
