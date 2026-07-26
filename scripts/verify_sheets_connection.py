#!/usr/bin/env python
"""Standalone Google Sheets connectivity check (03_IMPLEMENTATION.md §7 Step 5).

Run this after setting up the service account and before starting the
full app, to confirm: authentication succeeds, the spreadsheet
opens/creates, and worksheets can be read/written.

Usage: python scripts/verify_sheets_connection.py
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.integrations.sheets.bootstrap import ensure_spreadsheet
from app.integrations.sheets.client import GoogleSheetsClient
from app.memory.database import Database
from app.repositories.memory_repository import MemoryRepository


async def main() -> None:
    settings = get_settings()

    print(f"Authenticating with service account for '{settings.app_name}'...")
    sheets = GoogleSheetsClient(
        service_account_json=settings.google_service_account_json,
        service_account_file=settings.google_service_account_file,
    )
    print(f"✓ Authenticated as: {sheets.service_account_email}")

    database = Database(settings.database_path)
    await database.init()
    memory = MemoryRepository(database)

    spreadsheet_id = await ensure_spreadsheet(settings, sheets, memory)
    print(f"✓ Spreadsheet ready: {spreadsheet_id}")
    print(f"  https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

    tasks = await sheets.get_all_records(spreadsheet_id, "Tasks")
    logs = await sheets.get_all_records(spreadsheet_id, "Daily Logs")
    print(f"✓ Tasks sheet readable ({len(tasks)} rows)")
    print(f"✓ Daily Logs sheet readable ({len(logs)} rows)")

    if not settings.google_sheet_id:
        print(
            "\nHint: set GOOGLE_SHEET_ID="
            f"{spreadsheet_id} in your .env so this same spreadsheet is reused on every restart."
        )


if __name__ == "__main__":
    asyncio.run(main())
