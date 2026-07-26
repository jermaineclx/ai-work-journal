"""Weekly summary job (FR11)."""

from __future__ import annotations

from telegram import Bot

from app.core.container import Container
from app.core.logging import get_logger
from app.integrations.telegram.formatting import render_weekly_summary

logger = get_logger(__name__)


async def send_weekly_summary(container: Container, bot: Bot) -> None:
    if not container.settings.weekly_summary_enabled:
        return
    if container.settings.telegram_allowed_user_id is None:
        logger.warning("weekly_summary_skipped_no_allowed_user")
        return
    summary = await container.summary_service.weekly_summary()
    if summary.log_count == 0:
        return
    await bot.send_message(chat_id=container.settings.telegram_allowed_user_id, text=render_weekly_summary(summary))
    logger.info("weekly_summary_sent")
