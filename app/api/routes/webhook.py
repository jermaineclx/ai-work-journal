"""Telegram webhook endpoint (02_ARCHITECTURE.md §6). Validation only —
all reasoning happens inside `process_update`/the handlers it dispatches to."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from telegram import Update

from app.api.dependencies import get_container
from app.core.container import Container
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    container: Container = Depends(get_container),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    expected_secret = container.settings.telegram_webhook_secret
    if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    payload = await request.json()
    application = request.app.state.telegram_application
    update = Update.de_json(payload, application.bot)
    await application.process_update(update)
    return {"ok": True}
