"""Message formatting for Telegram (01_PRD.md §10 — concise, conversational,
never exposing embeddings/similarity internals unless asked)."""

from __future__ import annotations

from app.schemas.decision import DecisionSchema
from app.schemas.log_result import LogOutcome
from app.schemas.search import SearchResponse
from app.schemas.summary import DailySummary, WeeklySummary


def render_committed(outcome: LogOutcome) -> str:
    lines = ["✅ Logged successfully" if not outcome.is_new_task else "🆕 New task created"]
    lines.append("")
    lines.append(f"Task: {outcome.task_title}")
    if outcome.stakeholder:
        lines.append(f"Stakeholder: {outcome.stakeholder}")
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
