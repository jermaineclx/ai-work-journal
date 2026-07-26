"""FastAPI dependency providers.

The Container is built once at startup (see main.py's lifespan handler)
and stashed on `app.state`; routes pull it out via `Depends`.
"""

from __future__ import annotations

from fastapi import Request

from app.core.container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container
