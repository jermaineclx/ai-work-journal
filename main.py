"""Application entry point.

Keeps this file minimal per 03_IMPLEMENTATION.md §17 — all real wiring
lives in `app.api.app.create_app()` / `app.core.container.Container`.
```"""

from __future__ import annotations

import os

import uvicorn

from app.api.app import create_app
from app.core.config import get_settings

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.environment == "development")
