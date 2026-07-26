"""Telegram handlers — a thin presentation layer with zero business logic
(02_ARCHITECTURE.md §5.1). Every handler's job is: parse input, call a
service, render the result.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.core.container import Container
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.integrations.telegram.formatting import (
    render_committed,
    render_daily_summary,
    render_pending,
    render_search_results,
    render_weekly_summary,
)
from app.integrations.telegram.keyboards import build_confirmation_keyboard

logger = get_logger(__name__)

HELP_TEXT = (
    "I turn what you tell me into structured work history.\n\n"
    "Just send a message describing what you did — no format required.\n\n"
    "Commands:\n"
    "/today — what you've logged today\n"
    "/summary — this week's summary\n"
    "/tasks — your active tasks\n"
    "/search <query> — search your work history\n"
    "/undo — remove your last log\n"
    "/help — this message"
)


def _container(context: ContextTypes.DEFAULT_TYPE) -> Container:
    return context.application.bot_data["container"]


def _is_authorized(update: Update, container: Container) -> bool:
    allowed = container.settings.telegram_allowed_user_id
    if allowed is None:
        return True
    return update.effective_user is not None and update.effective_user.id == allowed


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    if not _is_authorized(update, container):
        await update.message.reply_text("This bot is private and not configured for your account.")
        return

    message = update.message.text
    if not message:
        return

    request_id = f"tg-{update.update_id}"
    user_id = str(update.effective_user.id)

    try:
        outcome = await container.log_service.process_message(request_id=request_id, user_id=user_id, message=message)
    except Exception:  # noqa: BLE001
        logger.exception("process_message_failed", extra={"request_id": request_id})
        await update.message.reply_text("Something went wrong processing that update. Please try again.")
        return

    if outcome.status == "committed":
        await update.message.reply_text(render_committed(outcome))
    else:
        keyboard = build_confirmation_keyboard(outcome.request_id, outcome.decision) if outcome.decision else None
        await update.message.reply_text(render_pending(outcome), reply_markup=keyboard)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    query = update.callback_query
    if not _is_authorized(update, container):
        await query.answer("Not authorized.")
        return

    await query.answer()
    action, _, rest = query.data.partition(":")

    try:
        if action == "cancel":
            request_id = rest
            await container.log_service.cancel(request_id=request_id)
            await query.edit_message_text("Cancelled. Nothing was saved.")
            return

        if action == "new":
            request_id = rest
            outcome = await container.log_service.confirm(request_id=request_id, chosen_task_id=None, create_new=True)
        elif action == "choose":
            request_id, _, task_id = rest.partition(":")
            outcome = await container.log_service.confirm(
                request_id=request_id, chosen_task_id=task_id, create_new=False
            )
        else:
            return
    except NotFoundError:
        await query.edit_message_text("This confirmation has expired. Please resend your update.")
        return
    except Exception:  # noqa: BLE001
        logger.exception("confirm_failed", extra={"data": query.data})
        await query.edit_message_text("Something went wrong saving that. Please try again.")
        return

    await query.edit_message_text(render_committed(outcome))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    summary = await container.summary_service.today_summary()
    await update.message.reply_text(render_daily_summary(summary))


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    await update.message.reply_text("Generating this week's summary…")
    summary = await container.summary_service.weekly_summary()
    await update.message.reply_text(render_weekly_summary(summary))


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    tasks = await container.task_service.list_tasks()
    if not tasks:
        await update.message.reply_text("No tasks yet — send me an update to create your first one.")
        return
    lines = [f"• {t.title} — {t.status.value}" for t in tasks[:20]]
    await update.message.reply_text("Your tasks:\n\n" + "\n".join(lines))


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /search <what you're looking for>")
        return
    response = await container.search_service.search(query)
    await update.message.reply_text(render_search_results(response))


async def cmd_undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    undone = await container.log_service.undo_last()
    if undone is None:
        await update.message.reply_text("Nothing to undo.")
        return
    await update.message.reply_text(f'Removed your last log: "{undone.original_message[:80]}"')


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    s = container.settings
    await update.message.reply_text(
        "Settings\n\n"
        f"LLM provider: {s.llm_provider}\n"
        f"Reminders: {'on' if s.reminders_enabled else 'off'}\n"
        f"Auto-apply threshold: {s.confidence_auto_apply:.0%}\n"
        f"Confirm threshold: {s.confidence_confirm_lower_bound:.0%}\n\n"
        "Edit these via environment variables and restart to change them."
    )


__all__ = [
    "handle_message",
    "handle_callback",
    "cmd_help",
    "cmd_today",
    "cmd_summary",
    "cmd_tasks",
    "cmd_search",
    "cmd_undo",
    "cmd_settings",
]
