"""Timezone helpers.

The app stores naive UTC datetimes everywhere (Sheets round-trips them
as plain ISO strings with no offset) — this just replaces the
deprecated `datetime.utcnow()` without introducing timezone-aware vs.
naive comparison bugs elsewhere in the codebase.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
