"""Daily reminder job (FR12)."""

from __future__ import annotations

from telegram import Bot

from app.core.container import Container
from app.core.logging import get_logger

logger = get_logger(__name__)

REMINDER_TEXT = "👋 You haven't logged any work today. Anything you'd like me to remember?"


async def send_daily_reminder(container: Container, bot: Bot) -> None:
    if not container.settings.reminders_enabled:
        return
    if container.settings.telegram_allowed_user_id is None:
        logger.warning("reminder_skipped_no_allowed_user")
        return
    should_remind = await container.reminder_service.should_remind()
    if not should_remind:
        return
    await bot.send_message(chat_id=container.settings.telegram_allowed_user_id, text=REMINDER_TEXT)
    logger.info("daily_reminder_sent")
