"""Telegram handlers — a thin presentation layer with zero business logic
(02_ARCHITECTURE.md §5.1). Every handler's job is: parse input, call a
service, render the result.

Multi-step interactions (creating a task explicitly, editing a field)
are tracked via `context.user_data["flow"]` — a small dict describing
what free-text reply the bot is waiting for. `handle_message` checks
for a pending flow before falling through to normal log processing.
"""

from __future__ import annotations

import uuid

from telegram import Update
from telegram.ext import ContextTypes

from app.core.container import Container
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.domain.enums import TaskStatus
from app.integrations.telegram.formatting import (
    render_committed,
    render_daily_summary,
    render_log_detail,
    render_pending,
    render_search_results,
    render_task_detail,
    render_weekly_summary,
)
from app.integrations.telegram.keyboards import (
    build_confirmation_keyboard,
    build_log_detail_keyboard,
    build_log_list_keyboard,
    build_stakeholder_picker,
    build_status_picker_keyboard,
    build_task_detail_keyboard,
    build_task_list_keyboard,
)

logger = get_logger(__name__)

HELP_TEXT = (
    "I turn what you tell me into structured work history.\n\n"
    "Just send a message describing what you did — no format required.\n\n"
    "Commands:\n"
    "/new_task <description> — explicitly start a new task (I'll ask who it's for)\n"
    "/today — what you've logged today\n"
    "/summary — this week's summary\n"
    "/tasks — view and edit your tasks and their logs\n"
    "/search <query> — search your work history\n"
    "/undo — remove your last log\n"
    "/cancel — cancel whatever I'm currently asking you\n"
    "/help — this message"
)


def _container(context: ContextTypes.DEFAULT_TYPE) -> Container:
    return context.application.bot_data["container"]


def _is_authorized(update: Update, container: Container) -> bool:
    allowed = container.settings.telegram_allowed_user_id
    if allowed is None:
        return True
    return update.effective_user is not None and update.effective_user.id == allowed


def _clear_flow(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("flow", None)
    context.user_data.pop("ntpick_options", None)


# --- Primary message handling ---


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    if not _is_authorized(update, container):
        await update.message.reply_text("This bot is private and not configured for your account.")
        return

    message = update.message.text
    if not message:
        return

    flow = context.user_data.get("flow")
    if flow:
        await _handle_flow_message(update, context, flow, message.strip())
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


async def _handle_flow_message(update: Update, context: ContextTypes.DEFAULT_TYPE, flow: dict, message: str) -> None:
    flow_type = flow.get("type")

    if flow_type == "new_task" and flow.get("stage") == "awaiting_description":
        context.user_data.pop("flow", None)
        await _start_new_task_flow(update, context, message)
        return

    if flow_type == "new_task" and flow.get("stage") == "awaiting_stakeholder":
        container = _container(context)
        _clear_flow(context)
        try:
            outcome = await _create_task_from_flow(container, flow["ai_output"], flow["message"], message)
        except Exception:  # noqa: BLE001
            logger.exception("create_task_explicitly_failed")
            await update.message.reply_text("Something went wrong creating that task. Please try again.")
            return
        await update.message.reply_text(render_committed(outcome))
        return

    if flow_type == "edit_task":
        context.user_data.pop("flow", None)
        await _apply_task_field_edit(update, context, flow["field"], flow["task_id"], message)
        return

    if flow_type == "edit_log":
        context.user_data.pop("flow", None)
        await _apply_log_field_edit(update, context, flow["field"], flow["log_id"], message)
        return

    context.user_data.pop("flow", None)


# --- /new_task ---


async def cmd_new_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    if not _is_authorized(update, container):
        await update.message.reply_text("This bot is private and not configured for your account.")
        return
    description = " ".join(context.args) if context.args else ""
    await _start_new_task_flow(update, context, description)


async def _start_new_task_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, description: str) -> None:
    if not description:
        context.user_data["flow"] = {"type": "new_task", "stage": "awaiting_description"}
        await update.message.reply_text("What did you work on? Describe it in your own words.")
        return

    container = _container(context)
    tasks = await container.task_repo.get_all()
    ai_output = await container.orchestrator.describe_new_task(message=description, tasks=tasks)
    options = await container.task_service.list_known_stakeholders()

    context.user_data["flow"] = {
        "type": "new_task",
        "stage": "awaiting_stakeholder",
        "ai_output": ai_output,
        "message": description,
    }
    context.user_data["ntpick_options"] = options

    title = ai_output.extraction.task_title or "Untitled Task"
    text = f'Got it — draft task: "{title}"\n\nWho\'s this for? Pick below, or just type a name.'
    keyboard = build_stakeholder_picker(options) if options else None
    await update.message.reply_text(text, reply_markup=keyboard)


async def _create_task_from_flow(container: Container, ai_output, description: str, stakeholder: str):
    updated_extraction = ai_output.extraction.model_copy(update={"stakeholder": stakeholder})
    ai_output = ai_output.model_copy(update={"extraction": updated_extraction})
    request_id = f"tg-newtask-{uuid.uuid4().hex[:16]}"
    return await container.log_service.create_task_explicitly(
        request_id=request_id, message=description, ai_output=ai_output
    )


# --- Field edit application (shared by the free-text reply path) ---


async def _apply_task_field_edit(
    update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, task_id: str, value: str
) -> None:
    container = _container(context)
    try:
        if field == "title":
            task = await container.task_service.edit_title(task_id, value)
        elif field == "stakeholder":
            task = await container.task_service.edit_stakeholder(task_id, value)
        elif field == "tags":
            tags = [t.strip() for t in value.split(",") if t.strip()]
            task = await container.task_service.edit_tags(task_id, tags)
        elif field == "summary":
            task = await container.task_service.edit_summary(task_id, value)
        else:
            return
    except NotFoundError:
        await update.message.reply_text("That task no longer exists.")
        return
    await update.message.reply_text(
        f"Updated {field}.\n\n{render_task_detail(task)}", reply_markup=build_task_detail_keyboard(task.task_id)
    )


async def _apply_log_field_edit(
    update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, log_id: str, value: str
) -> None:
    container = _container(context)
    try:
        if field == "stakeholder":
            log = await container.log_service.edit_log_stakeholder(log_id, value)
        elif field == "next_steps":
            log = await container.log_service.edit_log_next_steps(log_id, value)
        elif field == "tags":
            tags = [t.strip() for t in value.split(",") if t.strip()]
            log = await container.log_service.edit_log_tags(log_id, tags)
        else:
            return
        task = await container.task_service.get_task(log.task_id)
    except NotFoundError:
        await update.message.reply_text("That log or task no longer exists.")
        return
    await update.message.reply_text(
        f"Updated {field.replace('_', ' ')}.\n\n{render_log_detail(log, task.title)}",
        reply_markup=build_log_detail_keyboard(log.log_id, log.task_id),
    )


# --- Callback query routing ---


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
            await container.log_service.cancel(request_id=rest)
            await query.edit_message_text("Cancelled. Nothing was saved.")
            return

        if action == "new":
            outcome = await container.log_service.confirm(request_id=rest, chosen_task_id=None, create_new=True)
            await query.edit_message_text(render_committed(outcome))
            return

        if action == "choose":
            request_id, _, task_id = rest.partition(":")
            outcome = await container.log_service.confirm(
                request_id=request_id, chosen_task_id=task_id, create_new=False
            )
            await query.edit_message_text(render_committed(outcome))
            return

        if action == "cancelflow":
            _clear_flow(context)
            await query.edit_message_text("Cancelled.")
            return

        if action == "ntpick":
            await _handle_ntpick(query, context, container, rest)
            return

        if action == "tlist":
            tasks = await container.task_service.list_tasks()
            if not tasks:
                await query.edit_message_text("No tasks yet — send me an update to create your first one.")
                return
            await query.edit_message_text("Your tasks:", reply_markup=build_task_list_keyboard(tasks))
            return

        if action == "tview":
            task = await container.task_service.get_task(rest)
            await query.edit_message_text(
                render_task_detail(task), reply_markup=build_task_detail_keyboard(task.task_id)
            )
            return

        if action == "tfield":
            field, task_id = rest.split(":", 1)
            context.user_data["flow"] = {"type": "edit_task", "field": field, "task_id": task_id}
            await query.edit_message_text(f"Send the new {field} for this task (or /cancel):")
            return

        if action == "tstatus":
            await query.edit_message_text(
                "Pick a status:", reply_markup=build_status_picker_keyboard("tsetstatus", rest)
            )
            return

        if action == "tsetstatus":
            task_id, idx = rest.split(":")
            status = list(TaskStatus)[int(idx)]
            task = await container.task_service.edit_status(task_id, status)
            await query.edit_message_text(
                render_task_detail(task), reply_markup=build_task_detail_keyboard(task.task_id)
            )
            return

        if action == "tlogs":
            logs = await container.log_service.list_logs_for_task(rest)
            if not logs:
                await query.edit_message_text(
                    "No logs for this task yet.", reply_markup=build_task_detail_keyboard(rest)
                )
                return
            await query.edit_message_text("Logs:", reply_markup=build_log_list_keyboard(logs, rest))
            return

        if action == "lview":
            log = await container.log_service.get_log(rest)
            task = await container.task_service.get_task(log.task_id)
            await query.edit_message_text(
                render_log_detail(log, task.title), reply_markup=build_log_detail_keyboard(log.log_id, log.task_id)
            )
            return

        if action == "lfield":
            field, log_id = rest.split(":", 1)
            context.user_data["flow"] = {"type": "edit_log", "field": field, "log_id": log_id}
            await query.edit_message_text(f"Send the new {field.replace('_', ' ')} for this log (or /cancel):")
            return

        if action == "lstatus":
            await query.edit_message_text(
                "Pick a status:", reply_markup=build_status_picker_keyboard("lsetstatus", rest)
            )
            return

        if action == "lsetstatus":
            log_id, idx = rest.split(":")
            status = list(TaskStatus)[int(idx)]
            log = await container.log_service.edit_log_status(log_id, status)
            task = await container.task_service.get_task(log.task_id)
            await query.edit_message_text(
                render_log_detail(log, task.title), reply_markup=build_log_detail_keyboard(log.log_id, log.task_id)
            )
            return

    except NotFoundError:
        await query.edit_message_text("That no longer exists — it may have been removed.")
        return
    except Exception:  # noqa: BLE001
        logger.exception("callback_failed", extra={"data": query.data})
        await query.edit_message_text("Something went wrong. Please try again.")
        return


async def _handle_ntpick(query, context: ContextTypes.DEFAULT_TYPE, container: Container, rest: str) -> None:
    flow = context.user_data.get("flow")
    options = context.user_data.get("ntpick_options")
    if not flow or flow.get("type") != "new_task" or not options or not rest.isdigit() or int(rest) >= len(options):
        await query.edit_message_text("This has expired — send /new_task again.")
        return
    stakeholder = options[int(rest)]
    _clear_flow(context)
    outcome = await _create_task_from_flow(container, flow["ai_output"], flow["message"], stakeholder)
    await query.edit_message_text(render_committed(outcome))


# --- Commands ---


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _clear_flow(context)
    await update.message.reply_text("Cancelled.")


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
    await update.message.reply_text("Your tasks:", reply_markup=build_task_list_keyboard(tasks))


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
    "cmd_cancel",
    "cmd_new_task",
    "cmd_today",
    "cmd_summary",
    "cmd_tasks",
    "cmd_search",
    "cmd_undo",
    "cmd_settings",
]
