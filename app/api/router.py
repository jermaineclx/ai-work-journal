from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import health, tasks, webhook

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(webhook.router, tags=["webhook"])
api_router.include_router(tasks.router, tags=["tasks"])
