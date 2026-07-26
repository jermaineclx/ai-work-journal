"""Resolves which spreadsheet the app should use, creating one if needed.

Resolution order:
  1. `GOOGLE_SHEET_ID` env var, if set — explicit override always wins.
  2. A previously auto-created ID cached in the SQLite `preferences` table
     (so restarts don't create a new spreadsheet every time).
  3. Otherwise, create a new spreadsheet via the service account, share
     it with `GOOGLE_ACCOUNT_EMAIL` so the user can actually see it in
     their own Drive, provision the Tasks/Daily Logs tabs, and cache the
     resulting ID for next time.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.constants import DAILY_LOGS_HEADER, DAILY_LOGS_WORKSHEET_TITLE, TASKS_HEADER, TASKS_WORKSHEET_TITLE
from app.core.exceptions import SheetsIntegrationError
from app.core.logging import get_logger
from app.integrations.sheets.client import GoogleSheetsClient
from app.repositories.memory_repository import MemoryRepository

logger = get_logger(__name__)

_PREFERENCE_KEY = "auto_created_google_sheet_id"


async def ensure_spreadsheet(
    settings: Settings,
    sheets: GoogleSheetsClient,
    memory: MemoryRepository,
) -> str:
    if settings.google_sheet_id:
        spreadsheet_id = settings.google_sheet_id
        logger.info("using_configured_sheet_id", extra={"spreadsheet_id": spreadsheet_id})
    else:
        cached = await memory.get_preference(_PREFERENCE_KEY)
        if cached:
            spreadsheet_id = cached
            logger.info("using_cached_sheet_id", extra={"spreadsheet_id": spreadsheet_id})
        else:
            spreadsheet_id = await sheets.create_spreadsheet(settings.google_sheet_name)
            logger.warning(
                "created_new_spreadsheet",
                extra={
                    "spreadsheet_id": spreadsheet_id,
                    "hint": "Set GOOGLE_SHEET_ID to this value to avoid re-creating it on restart.",
                },
            )
            if settings.google_account_email:
                await sheets.share(spreadsheet_id, settings.google_account_email)
            else:
                logger.warning(
                    "no_google_account_email_configured",
                    extra={
                        "spreadsheet_id": spreadsheet_id,
                        "warning": "Sheet created but not shared with any personal account.",
                    },
                )
            await memory.set_preference(_PREFERENCE_KEY, spreadsheet_id)

    try:
        await sheets.ensure_worksheet(spreadsheet_id, TASKS_WORKSHEET_TITLE, TASKS_HEADER)
        await sheets.ensure_worksheet(spreadsheet_id, DAILY_LOGS_WORKSHEET_TITLE, DAILY_LOGS_HEADER)
    except SheetsIntegrationError:
        logger.error("failed_to_provision_worksheets", extra={"spreadsheet_id": spreadsheet_id})
        raise

    return spreadsheet_id
