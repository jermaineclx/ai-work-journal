"""Read-only Task/Search REST endpoints.

Not the primary interface (Telegram is), but keeping a thin REST surface
means a future web dashboard (01_PRD.md §18.5) can reuse the same
services without touching business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_container
from app.core.container import Container
from app.domain.entities import Task
from app.schemas.search import SearchResponse

router = APIRouter()


@router.get("/tasks", response_model=list[Task])
async def list_tasks(container: Container = Depends(get_container)) -> list[Task]:
    return await container.task_service.list_tasks()


@router.get("/search", response_model=SearchResponse)
async def search(q: str = Query(..., min_length=1), container: Container = Depends(get_container)) -> SearchResponse:
    return await container.search_service.search(q)
