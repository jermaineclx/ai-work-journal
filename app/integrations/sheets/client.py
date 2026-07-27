"""Thin wrapper around gspread — the only module in the codebase allowed
to import gspread directly (03_IMPLEMENTATION.md §14).

Responsibilities: authenticate, open/create the spreadsheet, ensure
worksheets + headers exist, append/update rows, retry transient
failures with exponential backoff. Row <-> domain-object mapping lives
in the repository layer, not here.
"""

from __future__ import annotations

import asyncio
import json
import random
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from app.core.exceptions import SheetsIntegrationError
from app.core.logging import get_logger

logger = get_logger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 4


def _load_credentials(*, json_str: str, json_file: str) -> Credentials:
    if json_str:
        info = json.loads(json_str)
        return Credentials.from_service_account_info(info, scopes=_SCOPES)
    if json_file:
        return Credentials.from_service_account_file(json_file, scopes=_SCOPES)
    raise SheetsIntegrationError(
        "No Google service account credentials configured "
        "(set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE)"
    )


async def _with_retry(fn, *args, **kwargs):
    """Run a blocking gspread call in a thread with exponential backoff."""
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        except gspread.exceptions.APIError as exc:
            status = exc.response.status_code if exc.response is not None else None
            last_exc = exc
            if status not in _RETRYABLE_STATUS_CODES or attempt == _MAX_RETRIES - 1:
                raise SheetsIntegrationError(f"Google Sheets API error: {exc}") from exc
            delay = (2**attempt) + random.random()
            logger.warning("sheets_retry", extra={"attempt": attempt, "status": status, "delay": delay})
            await asyncio.sleep(delay)
        except Exception as exc:  # noqa: BLE001
            raise SheetsIntegrationError(f"Google Sheets operation failed: {exc}") from exc
    raise SheetsIntegrationError(f"Google Sheets operation failed after retries: {last_exc}")


class GoogleSheetsClient:
    def __init__(self, *, service_account_json: str = "", service_account_file: str = "") -> None:
        credentials = _load_credentials(json_str=service_account_json, json_file=service_account_file)
        self._gc = gspread.authorize(credentials)
        self.service_account_email: str = credentials.service_account_email

    async def create_spreadsheet(self, title: str) -> str:
        try:
            spreadsheet = await _with_retry(self._gc.create, title)
        except SheetsIntegrationError as exc:
            if "storage quota" in str(exc).lower():
                raise SheetsIntegrationError(
                    "Google rejected spreadsheet creation because this service account has no "
                    "Drive storage quota of its own (normal for service accounts on personal/non-"
                    "Workspace Google accounts — they can edit shared files but can't own new ones). "
                    "Fix: create a blank Google Sheet manually in your own Google account, share it "
                    f"with '{self.service_account_email}' as Editor, then set GOOGLE_SHEET_ID to that "
                    "sheet's ID (from its URL) so the app never tries to create one itself."
                ) from exc
            raise
        return spreadsheet.id

    async def share(self, spreadsheet_id: str, email: str, *, role: str = "writer") -> None:
        spreadsheet = await _with_retry(self._gc.open_by_key, spreadsheet_id)
        await _with_retry(spreadsheet.share, email, perm_type="user", role=role, notify=False)

    async def ensure_worksheet(self, spreadsheet_id: str, title: str, header: list[str]) -> None:
        spreadsheet = await _with_retry(self._gc.open_by_key, spreadsheet_id)

        def _ensure(ss: gspread.Spreadsheet) -> None:
            try:
                worksheet = ss.worksheet(title)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = ss.add_worksheet(title=title, rows=1000, cols=max(len(header), 10))
                worksheet.append_row(header, value_input_option="RAW")
                return
            first_row = worksheet.row_values(1)
            if first_row != header:
                worksheet.update("A1", [header])

        await _with_retry(_ensure, spreadsheet)

    async def set_dropdown_validation(
        self, spreadsheet_id: str, worksheet_title: str, *, header: list[str], column_name: str, values: list[str]
    ) -> None:
        """Applies a native single-select dropdown (Data validation, list
        of items) to every data row of one column, so editing that column
        directly in Sheets is constrained to `values`. Re-applying is
        idempotent — safe to call on every boot, same as ensure_worksheet's
        header sync.

        Google Sheets' multi-select "chip" dropdown style has no API
        equivalent (as of writing, only settable by hand in the UI) — this
        only produces the classic single-value arrow dropdown, so it's
        only appropriate for single-valued columns like Status.
        """
        spreadsheet = await _with_retry(self._gc.open_by_key, spreadsheet_id)

        def _apply(ss: gspread.Spreadsheet) -> None:
            worksheet = ss.worksheet(worksheet_title)
            col_idx = header.index(column_name) + 1
            # rowcol_to_a1(1, n) always yields "<COLUMN_LETTERS>1" — column
            # letters are never digits, so stripping the trailing "1" from
            # row=1 leaves exactly the column letters, safely at any width.
            col_letter = gspread.utils.rowcol_to_a1(1, col_idx).rstrip("1")
            cell_range = f"{col_letter}2:{col_letter}{worksheet.row_count}"
            worksheet.add_validation(
                cell_range, gspread.utils.ValidationConditionType.one_of_list, values, strict=True, showCustomUi=True
            )

        await _with_retry(_apply, spreadsheet)

    async def get_all_records(self, spreadsheet_id: str, worksheet_title: str) -> list[dict[str, Any]]:
        spreadsheet = await _with_retry(self._gc.open_by_key, spreadsheet_id)
        worksheet = await _with_retry(spreadsheet.worksheet, worksheet_title)
        return await _with_retry(worksheet.get_all_records)

    async def append_row(self, spreadsheet_id: str, worksheet_title: str, row: list[Any]) -> None:
        spreadsheet = await _with_retry(self._gc.open_by_key, spreadsheet_id)
        worksheet = await _with_retry(spreadsheet.worksheet, worksheet_title)
        await _with_retry(worksheet.append_row, row, value_input_option="RAW")

    async def update_row_by_key(
        self,
        spreadsheet_id: str,
        worksheet_title: str,
        *,
        key_column: str,
        key_value: str,
        header: list[str],
        row_values: dict[str, Any],
    ) -> bool:
        """Find the row whose ``key_column`` equals ``key_value`` and overwrite it.

        Returns False if no matching row was found.
        """
        spreadsheet = await _with_retry(self._gc.open_by_key, spreadsheet_id)
        worksheet = await _with_retry(spreadsheet.worksheet, worksheet_title)
        all_values = await _with_retry(worksheet.get_all_values)
        if not all_values:
            return False
        header_row = all_values[0]
        try:
            key_idx = header_row.index(key_column)
        except ValueError as exc:
            raise SheetsIntegrationError(f"Column '{key_column}' not found in '{worksheet_title}'") from exc

        for row_number, existing_row in enumerate(all_values[1:], start=2):
            if len(existing_row) > key_idx and existing_row[key_idx] == key_value:
                new_row = [
                    row_values.get(col, existing_row[i] if i < len(existing_row) else "")
                    for i, col in enumerate(header)
                ]

                def _update(
                    ws: gspread.Worksheet = worksheet, rn: int = row_number, values: list[Any] = new_row
                ) -> None:
                    ws.update(f"A{rn}", [values])

                await _with_retry(_update)
                return True
        return False

    async def delete_row_by_key(
        self, spreadsheet_id: str, worksheet_title: str, *, key_column: str, key_value: str
    ) -> bool:
        spreadsheet = await _with_retry(self._gc.open_by_key, spreadsheet_id)
        worksheet = await _with_retry(spreadsheet.worksheet, worksheet_title)
        all_values = await _with_retry(worksheet.get_all_values)
        if not all_values:
            return False
        header_row = all_values[0]
        try:
            key_idx = header_row.index(key_column)
        except ValueError as exc:
            raise SheetsIntegrationError(f"Column '{key_column}' not found in '{worksheet_title}'") from exc

        for row_number, existing_row in enumerate(all_values[1:], start=2):
            if len(existing_row) > key_idx and existing_row[key_idx] == key_value:
                await _with_retry(worksheet.delete_rows, row_number)
                return True
        return False
