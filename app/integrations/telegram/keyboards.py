"""Inline keyboard construction for confirmation workflows (01_PRD.md §10)."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.domain.entities import DailyLog, Task
from app.domain.enums import ImpactLevel, Priority, TaskStatus
from app.schemas.decision import DecisionSchema

_MAX_TITLE_LEN = 28


def _short(text: str, max_len: int = _MAX_TITLE_LEN) -> str:
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def build_confirmation_keyboard(request_id: str, decision: DecisionSchema) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if decision.matched_task_id:
        best = next((c for c in decision.candidates if c.task_id == decision.matched_task_id), None)
        if best:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"✅ Yes — {_short(best.title)}", callback_data=f"choose:{request_id}:{best.task_id}"
                    )
                ]
            )
        others = [c for c in decision.candidates if c.task_id != decision.matched_task_id]
    else:
        others = decision.candidates

    for candidate in others:
        rows.append(
            [
                InlineKeyboardButton(
                    f"Use: {_short(candidate.title)}", callback_data=f"choose:{request_id}:{candidate.task_id}"
                )
            ]
        )

    rows.append([InlineKeyboardButton("🆕 Create New", callback_data=f"new:{request_id}")])
    rows.append([InlineKeyboardButton("✖️ Cancel", callback_data=f"cancel:{request_id}")])

    return InlineKeyboardMarkup(rows)


def build_task_list_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{_short(t.title, 22)} ({t.status.value})", callback_data=f"tview:{t.task_id}")]
        for t in tasks[:25]
    ]
    return InlineKeyboardMarkup(rows)


def build_task_detail_keyboard(task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✏️ Title", callback_data=f"tfield:title:{task_id}"),
                InlineKeyboardButton("👤 Stakeholder", callback_data=f"tfield:stakeholder:{task_id}"),
            ],
            [
                InlineKeyboardButton("🔄 Status", callback_data=f"tstatus:{task_id}"),
                InlineKeyboardButton("🏷 Tags", callback_data=f"tfield:tags:{task_id}"),
            ],
            [
                InlineKeyboardButton("📄 Summary", callback_data=f"tfield:summary:{task_id}"),
                InlineKeyboardButton("🔗 Resources", callback_data=f"tfield:resources:{task_id}"),
            ],
            [InlineKeyboardButton("🚦 Priority", callback_data=f"tpriority:{task_id}")],
            [InlineKeyboardButton("➕ Add Log", callback_data=f"taddlog:{task_id}")],
            [InlineKeyboardButton("🕘 View Logs", callback_data=f"tlogs:{task_id}")],
            [InlineKeyboardButton("⬅️ Back to Tasks", callback_data="tlist")],
        ]
    )


def build_status_picker_keyboard(action_prefix: str, entity_id: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(status.value, callback_data=f"{action_prefix}:{entity_id}:{idx}")]
        for idx, status in enumerate(TaskStatus)
    ]
    return InlineKeyboardMarkup(rows)


def build_log_list_keyboard(logs: list[DailyLog], task_id: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"{log.date.isoformat()} — {_short(log.original_message, 30)}", callback_data=f"lview:{log.log_id}"
            )
        ]
        for log in logs[:25]
    ]
    rows.append([InlineKeyboardButton("⬅️ Back to Task", callback_data=f"tview:{task_id}")])
    return InlineKeyboardMarkup(rows)


def build_log_detail_keyboard(log_id: str, task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👤 Stakeholder", callback_data=f"lfield:stakeholder:{log_id}"),
                InlineKeyboardButton("🔄 Status", callback_data=f"lstatus:{log_id}"),
            ],
            [
                InlineKeyboardButton("➡️ Next Steps", callback_data=f"lfield:next_steps:{log_id}"),
                InlineKeyboardButton("🏷 Tags", callback_data=f"lfield:tags:{log_id}"),
            ],
            [
                InlineKeyboardButton("🔗 Resources", callback_data=f"lfield:resources:{log_id}"),
                InlineKeyboardButton("📅 Date", callback_data=f"lfield:date:{log_id}"),
            ],
            [
                InlineKeyboardButton("💥 Impact", callback_data=f"limpact:{log_id}"),
                InlineKeyboardButton("📝 Summary", callback_data=f"lfield:log_summary:{log_id}"),
            ],
            [InlineKeyboardButton("⬅️ Back to Task", callback_data=f"tview:{task_id}")],
        ]
    )


def build_impact_picker_keyboard(log_id: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(impact.value, callback_data=f"limpactset:{log_id}:{idx}")]
        for idx, impact in enumerate(ImpactLevel)
    ]
    return InlineKeyboardMarkup(rows)


def build_priority_picker_keyboard(task_id: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(priority.value, callback_data=f"tsetpriority:{task_id}:{idx}")]
        for idx, priority in enumerate(Priority)
    ]
    return InlineKeyboardMarkup(rows)


def build_stakeholder_picker(options: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(name, callback_data=f"ntpick:{i}")] for i, name in enumerate(options)]
    rows.append([InlineKeyboardButton("✖️ Cancel", callback_data="cancelflow")])
    return InlineKeyboardMarkup(rows)
