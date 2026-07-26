"""API-facing response/request contracts (02_ARCHITECTURE.md §5.2)."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    checks: dict[str, bool]


class VersionResponse(BaseModel):
    name: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    error: str
    request_id: str | None = None
