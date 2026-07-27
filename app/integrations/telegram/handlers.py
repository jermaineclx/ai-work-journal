"""Telegram handlers — a thin presentation layer with zero business logic
(02_ARCHITECTURE.md §5.1). Every handler's job is: parse input, call a
service, render the result.

Multi-step interactions (creating a task explicitly, editing a field)
are tracked via `context.user_data["flow"]` — a small dict describing
what free-text reply the bot is waiting for. `handle_message` checks
for a pending flow before falling through to normal log processing.
"""

from __future__ import annotations

import re
import uuid
from datetime import date, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from app.core.container import Container
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.domain.entities import Task
from app.domain.enums import ImpactLevel, Priority, Stakeholder, TaskStatus
from app.integrations.telegram.formatting import (
    render_all_logs,
    render_all_tasks,
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
    build_impact_picker_keyboard,
    build_log_detail_keyboard,
    build_log_list_keyboard,
    build_priority_picker_keyboard,
    build_recent_logs_keyboard,
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
    "/tasks — view and edit your tasks and their logs (tap-through)\n"
    "/logs — your 10 most recent logs, tap into any to view/edit (tap-through)\n"
    "/all_tasks [status] — every task, all columns, e.g. /all_tasks in progress\n"
    "/all_logs [task_id] [date] — every log, optionally filtered, e.g. /all_logs T001 today\n"
    "/edit task|log <id> <field> <value> — directly set any field, e.g. "
    "/edit task T001 stakeholder Liyuan\n"
    "/search <query> — search your work history\n"
    "/undo — remove your last log\n"
    "/cancel — cancel whatever I'm currently asking you\n"
    "/help — this message"
)

_TASK_ID_PATTERN = re.compile(r"^[Tt]\d+$")

_TASK_EDITABLE_FIELDS = ["title", "stakeholder", "status", "priority", "tags", "resources", "summary"]
_LOG_EDITABLE_FIELDS = ["date", "stakeholder", "next_steps", "tags", "resources", "impact", "log_summary"]


def _parse_status(value: str) -> TaskStatus | None:
    normalized = value.strip().lower().replace("_", " ")
    return next((s for s in TaskStatus if s.value.lower() == normalized), None)


def _parse_impact(value: str) -> ImpactLevel | None:
    normalized = value.strip().lower().replace("_", " ")
    return next((i for i in ImpactLevel if i.value.lower() == normalized), None)


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _parse_relative_or_iso_date(value: str) -> date | None:
    lowered = value.strip().lower()
    if lowered == "today":
        return date.today()
    if lowered == "yesterday":
        return date.today() - timedelta(days=1)
    return _parse_iso_date(value)


def _parse_stakeholders(value: str) -> tuple[list[str], list[str]]:
    """Parse a ", "-delimited list of names (e.g. "Liyuan, Ammir, Rosey").

    Returns (valid canonical names, raw names that didn't match the
    roster) so the caller can show a helpful error listing exactly which
    name(s) weren't recognized.
    """
    valid: list[str] = []
    invalid: list[str] = []
    for part in _parse_list(value):
        member = Stakeholder.parse(part)
        if member is None:
            invalid.append(part)
        elif member.value not in valid:
            valid.append(member.value)
    return valid, invalid


def _field_prompt(field: str, entity: str) -> str:
    if field == "resources":
        return f"Send resource(s) to add to this {entity}, comma-separated (added to the existing list, or /cancel):"
    if field == "log_summary":
        return "Send the new summary for this log (or /cancel):"
    return f"Send the new {field.replace('_', ' ')} for this {entity} (or /cancel):"


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
        valid, invalid = _parse_stakeholders(message)
        if invalid or not valid:
            unrecognized = ", ".join(invalid) if invalid else message
            await update.message.reply_text(
                f"Didn't recognize '{unrecognized}'. Pick one or more of: "
                f"{', '.join(s.value for s in Stakeholder)} (comma-separated, or /cancel)."
            )
            return
        container = _container(context)
        _clear_flow(context)
        try:
            outcome = await _create_task_from_flow(container, flow["ai_output"], flow["message"], valid)
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

    if flow_type == "task_impact":
        context.user_data.pop("flow", None)
        await _apply_task_impact(update, context, flow["task_id"], message)
        return

    if flow_type == "task_log":
        context.user_data.pop("flow", None)
        await _add_log_to_task(update, context, flow["task_id"], message)
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
    options = [s.value for s in Stakeholder]

    context.user_data["flow"] = {
        "type": "new_task",
        "stage": "awaiting_stakeholder",
        "ai_output": ai_output,
        "message": description,
    }
    context.user_data["ntpick_options"] = options

    title = ai_output.extraction.task_title or "Untitled Task"
    text = (
        f'Got it — draft task: "{title}"\n\n'
        "Who's this for? Pick one below, or type one or more names separated by commas "
        "(e.g. Liyuan, Ammir)."
    )
    keyboard = build_stakeholder_picker(options) if options else None
    await update.message.reply_text(text, reply_markup=keyboard)


async def _create_task_from_flow(container: Container, ai_output, description: str, stakeholders: list[str]):
    updated_extraction = ai_output.extraction.model_copy(update={"stakeholder": stakeholders})
    ai_output = ai_output.model_copy(update={"extraction": updated_extraction})
    request_id = f"tg-newtask-{uuid.uuid4().hex[:16]}"
    return await container.log_service.create_task_explicitly(
        request_id=request_id, message=description, ai_output=ai_output
    )


# --- Status changes (shared by the button picker and /edit) ---


async def _apply_task_status(container: Container, task_id: str, status: TaskStatus) -> tuple[Task, bool]:
    """Sets a task's status and reports whether this transition just
    completed it (i.e. wasn't already Completed) — the trigger for the
    impact-prompt flow."""
    current = await container.task_service.get_task(task_id)
    was_completed = current.status == TaskStatus.COMPLETED
    task = await container.task_service.edit_status(task_id, status)
    just_completed = status == TaskStatus.COMPLETED and not was_completed
    return task, just_completed


# --- Field edit application (shared by the free-text reply path) ---


async def _apply_task_field_edit(
    update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, task_id: str, value: str
) -> None:
    container = _container(context)
    try:
        if field == "title":
            task = await container.task_service.edit_title(task_id, value)
        elif field == "stakeholder":
            valid, invalid = _parse_stakeholders(value)
            if invalid or not valid:
                unrecognized = ", ".join(invalid) if invalid else value
                await update.message.reply_text(
                    f"Didn't recognize '{unrecognized}'. Valid: {', '.join(s.value for s in Stakeholder)} "
                    "(comma-separated for multiple)."
                )
                return
            task = await container.task_service.edit_stakeholder(task_id, valid)
        elif field == "tags":
            task = await container.task_service.edit_tags(task_id, _parse_list(value))
        elif field == "resources":
            task = await container.task_service.edit_resources(task_id, _parse_list(value))
        elif field == "summary":
            task = await container.task_service.edit_summary(task_id, value)
        elif field == "priority":
            priority = Priority.parse(value)
            if priority is None:
                await update.message.reply_text(
                    f"Unknown priority '{value}'. Valid: {', '.join(p.value for p in Priority)}"
                )
                return
            task = await container.task_service.edit_priority(task_id, priority)
        elif field == "status":
            status = _parse_status(value)
            if status is None:
                await update.message.reply_text(
                    f"Unknown status '{value}'. Valid: {', '.join(s.value for s in TaskStatus)}"
                )
                return
            task, just_completed = await _apply_task_status(container, task_id, status)
            if just_completed:
                context.user_data["flow"] = {"type": "task_impact", "task_id": task_id}
                await update.message.reply_text(
                    f'🎉 Marked "{task.title}" as Completed!\n\nWhat was the impact of this work?'
                )
                return
        else:
            await update.message.reply_text(f"Can't edit '{field}' on a task.")
            return
    except NotFoundError:
        await update.message.reply_text("That task no longer exists.")
        return
    await update.message.reply_text(
        f"Updated {field}.\n\n{render_task_detail(task)}", reply_markup=build_task_detail_keyboard(task.task_id)
    )


async def _apply_task_impact(
    update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: str, impact_text: str
) -> None:
    """Weaves the user's answer to "what was the impact?" into the task's
    summary via the Summary Agent, triggered after marking a task Completed."""
    container = _container(context)
    try:
        task = await container.task_service.get_task(task_id)
        summary_result, _ = await container.summary_agent.run(
            task_title=task.title,
            current_summary=task.summary,
            message=f"This task is now complete. Impact: {impact_text}",
            status=TaskStatus.COMPLETED,
        )
        task = await container.task_service.edit_summary(task_id, summary_result.summary)
    except NotFoundError:
        await update.message.reply_text("That task no longer exists.")
        return
    except Exception:  # noqa: BLE001
        logger.exception("task_impact_summary_failed", extra={"task_id": task_id})
        await update.message.reply_text(
            "Something went wrong recording that — you can add it manually via the Summary button or /edit."
        )
        return
    await update.message.reply_text(
        f"Got it — updated the summary.\n\n{render_task_detail(task)}",
        reply_markup=build_task_detail_keyboard(task.task_id),
    )


async def _add_log_to_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: str, message: str) -> None:
    """Logs a message against a task the user explicitly picked
    (/tasks → task → Add Log) — skips task matching entirely since the
    task is already known."""
    container = _container(context)
    try:
        task = await container.task_service.get_task(task_id)
    except NotFoundError:
        await update.message.reply_text("That task no longer exists.")
        return

    tasks = await container.task_repo.get_all()
    request_id = f"tg-addlog-{uuid.uuid4().hex[:16]}"
    try:
        ai_output = await container.orchestrator.describe_for_task(message=message, task=task, tasks=tasks)
        outcome = await container.log_service.log_to_task_explicitly(
            request_id=request_id, task_id=task_id, message=message, ai_output=ai_output
        )
        log = await container.log_service.get_log(outcome.log_id)
    except Exception:  # noqa: BLE001
        logger.exception("add_log_to_task_failed", extra={"task_id": task_id})
        await update.message.reply_text("Something went wrong logging that. Please try again.")
        return
    await update.message.reply_text(
        f"✅ Logged successfully\n\n{render_log_detail(log, outcome.task_title)}",
        reply_markup=build_log_detail_keyboard(log.log_id, log.task_id),
    )


async def _apply_log_field_edit(
    update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, log_id: str, value: str
) -> None:
    container = _container(context)
    try:
        if field == "stakeholder":
            valid, invalid = _parse_stakeholders(value)
            if invalid or not valid:
                unrecognized = ", ".join(invalid) if invalid else value
                await update.message.reply_text(
                    f"Didn't recognize '{unrecognized}'. Valid: {', '.join(s.value for s in Stakeholder)} "
                    "(comma-separated for multiple)."
                )
                return
            log = await container.log_service.edit_log_stakeholder(log_id, valid)
        elif field == "next_steps":
            log = await container.log_service.edit_log_next_steps(log_id, value)
        elif field == "tags":
            log = await container.log_service.edit_log_tags(log_id, _parse_list(value))
        elif field == "resources":
            log = await container.log_service.edit_log_resources(log_id, _parse_list(value))
        elif field == "date":
            parsed = _parse_iso_date(value)
            if parsed is None:
                await update.message.reply_text("Date must be in YYYY-MM-DD format, e.g. 2026-07-27.")
                return
            log = await container.log_service.edit_log_date(log_id, parsed)
        elif field == "impact":
            impact = _parse_impact(value)
            if impact is None:
                await update.message.reply_text(
                    f"Unknown impact '{value}'. Valid: {', '.join(i.value for i in ImpactLevel)}"
                )
                return
            log = await container.log_service.edit_log_impact(log_id, impact)
        elif field == "log_summary":
            log = await container.log_service.edit_log_summary(log_id, value)
        else:
            await update.message.reply_text(f"Can't edit '{field}' on a log.")
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
            await query.edit_message_text(_field_prompt(field, "task"))
            return

        if action == "tstatus":
            await query.edit_message_text(
                "Pick a status:", reply_markup=build_status_picker_keyboard("tsetstatus", rest)
            )
            return

        if action == "tsetstatus":
            task_id, idx = rest.split(":")
            status = list(TaskStatus)[int(idx)]
            task, just_completed = await _apply_task_status(container, task_id, status)
            if just_completed:
                context.user_data["flow"] = {"type": "task_impact", "task_id": task_id}
                await query.edit_message_text(
                    f'🎉 Marked "{task.title}" as Completed!\n\nWhat was the impact of this work?'
                )
                return
            await query.edit_message_text(
                render_task_detail(task), reply_markup=build_task_detail_keyboard(task.task_id)
            )
            return

        if action == "tpriority":
            await query.edit_message_text("Pick a priority:", reply_markup=build_priority_picker_keyboard(rest))
            return

        if action == "tsetpriority":
            task_id, idx = rest.split(":")
            priority = list(Priority)[int(idx)]
            task = await container.task_service.edit_priority(task_id, priority)
            await query.edit_message_text(
                render_task_detail(task), reply_markup=build_task_detail_keyboard(task.task_id)
            )
            return

        if action == "taddlog":
            task = await container.task_service.get_task(rest)
            context.user_data["flow"] = {"type": "task_log", "task_id": rest}
            await query.edit_message_text(
                f'What did you do on "{task.title}"? Describe it in your own words (or /cancel):'
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
            await query.edit_message_text(_field_prompt(field, "log"))
            return

        if action == "limpact":
            await query.edit_message_text("Pick an impact level:", reply_markup=build_impact_picker_keyboard(rest))
            return

        if action == "limpactset":
            log_id, idx = rest.split(":")
            impact = list(ImpactLevel)[int(idx)]
            log = await container.log_service.edit_log_impact(log_id, impact)
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
    outcome = await _create_task_from_flow(container, flow["ai_output"], flow["message"], [stakeholder])
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


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    logs = await container.log_service.list_recent_logs(limit=10)
    if not logs:
        await update.message.reply_text("No logs yet — send me an update to create your first one.")
        return
    tasks_by_id = {t.task_id: t for t in await container.task_service.list_tasks()}
    await update.message.reply_text("Your latest logs:", reply_markup=build_recent_logs_keyboard(logs, tasks_by_id))


async def cmd_all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    status_filter = None
    if context.args:
        status_filter = _parse_status(" ".join(context.args))
        if status_filter is None:
            await update.message.reply_text(f"Unknown status filter. Valid: {', '.join(s.value for s in TaskStatus)}")
            return

    tasks = await container.task_service.list_tasks(status=status_filter)
    if not tasks:
        await update.message.reply_text("No tasks match that filter." if status_filter else "No tasks yet.")
        return
    tasks = sorted(tasks, key=lambda t: t.task_id)
    for chunk in render_all_tasks(tasks):
        await update.message.reply_text(chunk)


async def cmd_all_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    container = _container(context)
    task_id_filter: str | None = None
    date_filter: date | None = None

    for arg in context.args or []:
        if _TASK_ID_PATTERN.match(arg):
            task_id_filter = arg.upper()
            continue
        parsed_date = _parse_relative_or_iso_date(arg)
        if parsed_date is not None:
            date_filter = parsed_date
            continue
        await update.message.reply_text(
            "Usage: /all_logs [task_id] [date]\n"
            "Examples: /all_logs, /all_logs T001, /all_logs 2026-07-26, /all_logs T001 today"
        )
        return

    logs = await container.log_service.search_logs(task_id=task_id_filter, on_date=date_filter)
    if not logs:
        await update.message.reply_text("No logs match those filters.")
        return

    logs = sorted(logs, key=lambda log: log.log_id)
    tasks_by_id = {t.task_id: t for t in await container.task_service.list_tasks()}
    for chunk in render_all_logs(logs, tasks_by_id):
        await update.message.reply_text(chunk)


EDIT_USAGE = (
    "Usage: /edit task|log <id> <field> <value>\n\n"
    f"Task fields: {', '.join(_TASK_EDITABLE_FIELDS)}\n"
    f"Log fields: {', '.join(_LOG_EDITABLE_FIELDS)}\n\n"
    "Stakeholder accepts multiple names, comma-separated. Resources are always "
    "appended to the existing list, never overwritten.\n\n"
    "Examples:\n"
    "/edit task T001 stakeholder Liyuan, Ammir\n"
    "/edit task T001 status KIV\n"
    "/edit task T001 priority P0\n"
    "/edit log L0002 next_steps Ship next week\n"
    "/edit log L0002 date 2026-07-26"
)


async def cmd_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) < 3:
        await update.message.reply_text(EDIT_USAGE)
        return

    entity_type, entity_id, field, *value_parts = args
    entity_type = entity_type.lower()
    field = field.lower()
    value = " ".join(value_parts)

    if not value and field not in ("tags", "resources"):
        await update.message.reply_text("Please provide a value to set.")
        return

    if entity_type == "task":
        if field not in _TASK_EDITABLE_FIELDS:
            await update.message.reply_text(
                f"Can't edit '{field}' on a task. Editable: {', '.join(_TASK_EDITABLE_FIELDS)}"
            )
            return
        await _apply_task_field_edit(update, context, field, entity_id.upper(), value)
    elif entity_type == "log":
        if field not in _LOG_EDITABLE_FIELDS:
            await update.message.reply_text(
                f"Can't edit '{field}' on a log. Editable: {', '.join(_LOG_EDITABLE_FIELDS)}"
            )
            return
        await _apply_log_field_edit(update, context, field, entity_id.upper(), value)
    else:
        await update.message.reply_text(EDIT_USAGE)


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
    "cmd_logs",
    "cmd_all_tasks",
    "cmd_all_logs",
    "cmd_edit",
    "cmd_search",
    "cmd_undo",
    "cmd_settings",
]
