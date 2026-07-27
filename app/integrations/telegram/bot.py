"""Builds the python-telegram-bot Application.

The Application is driven via webhook (`process_update`), not polling —
see the FastAPI `/webhook/telegram` route. It never runs its own event
loop; FastAPI/uvicorn owns that.
"""

from __future__ import annotations

from telegram import BotCommand, Update
from telegram.ext import Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from app.core.config import Settings
from app.core.container import Container
from app.core.logging import get_logger
from app.integrations.telegram import handlers

logger = get_logger(__name__)

# Shown as the native "/" autocomplete menu in Telegram clients. Kept in
# the same order as HELP_TEXT so both stay easy to eyeball together.
BOT_COMMANDS = [
    BotCommand("new_task", "Start a new task explicitly"),
    BotCommand("today", "What you've logged today"),
    BotCommand("summary", "This week's summary"),
    BotCommand("tasks", "View and edit your tasks and their logs"),
    BotCommand("all_tasks", "Full list of tasks, optionally filtered by status"),
    BotCommand("all_logs", "Full list of logs, optionally filtered by task/date"),
    BotCommand("edit", "Directly set any field on a task or log"),
    BotCommand("search", "Search your work history"),
    BotCommand("undo", "Remove your last log"),
    BotCommand("cancel", "Cancel whatever it's currently asking you"),
    BotCommand("settings", "Show current configuration"),
    BotCommand("help", "Show help"),
]


def build_application(settings: Settings, container: Container) -> Application:
    application = ApplicationBuilder().token(settings.telegram_token).build()
    application.bot_data["container"] = container

    application.add_handler(CommandHandler("help", handlers.cmd_help))
    application.add_handler(CommandHandler("start", handlers.cmd_help))
    application.add_handler(CommandHandler("new_task", handlers.cmd_new_task))
    application.add_handler(CommandHandler("cancel", handlers.cmd_cancel))
    application.add_handler(CommandHandler("today", handlers.cmd_today))
    application.add_handler(CommandHandler("summary", handlers.cmd_summary))
    application.add_handler(CommandHandler("tasks", handlers.cmd_tasks))
    application.add_handler(CommandHandler("all_tasks", handlers.cmd_all_tasks))
    application.add_handler(CommandHandler("all_logs", handlers.cmd_all_logs))
    application.add_handler(CommandHandler("edit", handlers.cmd_edit))
    application.add_handler(CommandHandler("search", handlers.cmd_search))
    application.add_handler(CommandHandler("undo", handlers.cmd_undo))
    application.add_handler(CommandHandler("settings", handlers.cmd_settings))
    application.add_handler(CallbackQueryHandler(handlers.handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))

    return application


async def configure_bot_commands(application: Application) -> None:
    """Registers the "/" autocomplete menu. Safe to call on every startup —
    Telegram just overwrites the previous list."""
    await application.bot.set_my_commands(BOT_COMMANDS)
    logger.info("telegram_commands_configured", extra={"count": len(BOT_COMMANDS)})


async def configure_webhook(application: Application, settings: Settings) -> None:
    if not settings.telegram_webhook_url:
        logger.warning(
            "telegram_webhook_url_not_set", extra={"hint": "Set TELEGRAM_WEBHOOK_URL or configure manually."}
        )
        return
    await application.bot.set_webhook(
        url=settings.telegram_webhook_url,
        secret_token=settings.telegram_webhook_secret or None,
        allowed_updates=Update.ALL_TYPES,
    )
    logger.info("telegram_webhook_configured", extra={"url": settings.telegram_webhook_url})
