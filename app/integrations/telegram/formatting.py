"""Message formatting for Telegram (01_PRD.md §10 — concise, conversational,
never exposing embeddings/similarity internals unless asked)."""

from __future__ import annotations

from app.domain.entities import DailyLog, Task
from app.schemas.decision import DecisionSchema
from app.schemas.log_result import LogOutcome
from app.schemas.search import SearchResponse
from app.schemas.summary import DailySummary, WeeklySummary


def _fmt_stakeholders(names: list[str]) -> str:
    return ", ".join(names) if names else "—"


def render_committed(outcome: LogOutcome) -> str:
    lines = ["✅ Logged successfully" if not outcome.is_new_task else "🆕 New task created"]
    lines.append("")
    lines.append(f"Task: {outcome.task_title}")
    if outcome.stakeholder:
        lines.append(f"Stakeholder: {_fmt_stakeholders(outcome.stakeholder)}")
    lines.append(f"Status: {outcome.task_status.value if outcome.task_status else '—'}")
    if outcome.tags:
        lines.append(f"Tags: {', '.join(outcome.tags)}")
    lines.append("")
    lines.append("Timeline updated." if not outcome.is_new_task else "Added to your work history.")
    return "\n".join(lines)


def render_pending(outcome: LogOutcome) -> str:
    decision: DecisionSchema | None = outcome.decision
    lines: list[str] = []
    if decision and decision.matched_task_id:
        best = next((c for c in decision.candidates if c.task_id == decision.matched_task_id), None)
        title = best.title if best else outcome.proposed_task_title
        lines.append("I think this belongs to:")
        lines.append("")
        lines.append(f"{title}")
        lines.append("")
        lines.append(f"Confidence: {outcome.confidence:.0%}" if outcome.confidence is not None else "")
        lines.append("")
        lines.append("Is that correct?")
    elif decision and decision.candidates:
        lines.append("I found multiple possible matches:")
        lines.append("")
        for c in decision.candidates:
            lines.append(f"• {c.title} ({c.similarity:.0%})")
        lines.append("")
        lines.append("Which one should I use?")
    else:
        lines.append("I couldn't confidently match this update.")
        lines.append("")
        if outcome.proposed_task_title:
            lines.append(f"Proposed new task: {outcome.proposed_task_title}")
        lines.append("Would you like to create a new task?")
    return "\n".join(line for line in lines if line is not None)


def render_daily_summary(summary: DailySummary) -> str:
    lines = ["Today's Work", ""]
    for title in summary.task_titles:
        lines.append(f"• {title}")
    if not summary.task_titles:
        lines.append("(nothing logged yet today)")
    lines.append("")
    lines.append(f"{summary.log_count} update{'s' if summary.log_count != 1 else ''} logged")
    return "\n".join(lines)


def render_weekly_summary(summary: WeeklySummary) -> str:
    return f"{summary.text}\n\n{summary.log_count} updates across {summary.tasks_touched} task(s) this week."


def render_search_results(response: SearchResponse) -> str:
    if not response.tasks and not response.logs:
        return f'No results for "{response.query}".'
    lines = [f'Results for "{response.query}"', ""]
    if response.tasks:
        lines.append("Tasks")
        for t in response.tasks:
            lines.append(f"• {t.title} — {t.status.value}")
        lines.append("")
    if response.logs:
        lines.append("Updates")
        for log in response.logs[:5]:
            lines.append(f"• {log.date.isoformat()} [{log.task_title}] {log.original_message[:80]}")
    return "\n".join(lines)


def render_task_detail(task: Task) -> str:
    lines = [
        f"📋 {task.title}",
        "",
        f"Stakeholder: {_fmt_stakeholders(task.stakeholder)}",
        f"Status: {task.status.value}",
        f"Tags: {', '.join(task.tags) if task.tags else '—'}",
        f"Resources: {', '.join(task.resources) if task.resources else '—'}",
        "",
        "Summary:",
        task.summary or "(none yet)",
        "",
        f"{task.total_updates} update(s) · last updated {task.updated_at.date().isoformat()}",
    ]
    return "\n".join(lines)


def render_log_detail(log: DailyLog, task_title: str) -> str:
    lines = [
        f"📝 Log for {task_title}",
        "",
        f"Date: {log.date.isoformat()}",
        f"Message: {log.original_message}",
        "",
        f"Stakeholder: {_fmt_stakeholders(log.stakeholder)}",
        f"Status: {log.status.value if log.status else '—'}",
        f"Next steps: {log.next_steps or '—'}",
        f"Resources: {', '.join(log.resources) if log.resources else '—'}",
        f"Tags: {', '.join(log.tags) if log.tags else '—'}",
        f"Impact: {log.impact.value}",
    ]
    return "\n".join(lines)


_MAX_MESSAGE_CHARS = 3500


def _chunk_blocks(blocks: list[str], *, header: str) -> list[str]:
    """Group text blocks into Telegram-message-sized chunks (4096 char
    hard limit; stay well under it). Never used for anything with markup
    that could be split mid-tag, since these are plain-text renders."""
    if not blocks:
        return [header]
    chunks: list[str] = []
    current: list[str] = [header]
    current_len = len(header)
    for block in blocks:
        block_len = len(block) + 2
        if current_len + block_len > _MAX_MESSAGE_CHARS and len(current) > 1:
            chunks.append("\n\n".join(current))
            current = [f"{header} (cont'd)"]
            current_len = len(current[0])
        current.append(block)
        current_len += block_len
    chunks.append("\n\n".join(current))
    return chunks


def render_all_tasks(tasks: list[Task]) -> list[str]:
    blocks = [
        (
            f"[{t.task_id}] {t.title}\n"
            f"Stakeholder: {_fmt_stakeholders(t.stakeholder)}\n"
            f"Status: {t.status.value}\n"
            f"Tags: {', '.join(t.tags) if t.tags else '—'}\n"
            f"Resources: {', '.join(t.resources) if t.resources else '—'}\n"
            f"Created: {t.created_at.date().isoformat()} · Updated: {t.updated_at.date().isoformat()} · "
            f"Updates: {t.total_updates}\n"
            f"Summary: {t.summary or '(none yet)'}"
        )
        for t in tasks
    ]
    return _chunk_blocks(blocks, header=f"{len(tasks)} task(s)")


def render_all_logs(logs: list[DailyLog], tasks_by_id: dict[str, Task]) -> list[str]:
    blocks = []
    for log in logs:
        task = tasks_by_id.get(log.task_id)
        task_label = f"{task.title} ({log.task_id})" if task else log.task_id
        blocks.append(
            f"[{log.log_id}] {log.date.isoformat()} — {task_label}\n"
            f"Message: {log.original_message}\n"
            f"Stakeholder: {_fmt_stakeholders(log.stakeholder)}\n"
            f"Status: {log.status.value if log.status else '—'}\n"
            f"Next steps: {log.next_steps or '—'}\n"
            f"Resources: {', '.join(log.resources) if log.resources else '—'}\n"
            f"Tags: {', '.join(log.tags) if log.tags else '—'}\n"
            f"Impact: {log.impact.value}\n"
            f"Logged: {log.timestamp.isoformat()}"
        )
    return _chunk_blocks(blocks, header=f"{len(logs)} log(s)")
