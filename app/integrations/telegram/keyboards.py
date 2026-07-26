"""Inline keyboard construction for confirmation workflows (01_PRD.md §10)."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.schemas.decision import DecisionSchema

_MAX_TITLE_LEN = 28


def _short(title: str) -> str:
    return title if len(title) <= _MAX_TITLE_LEN else title[: _MAX_TITLE_LEN - 1] + "…"


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
