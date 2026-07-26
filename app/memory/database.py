"""SQLite AI-memory store.

Stores everything Google Sheets should never see: embeddings, learned
aliases, cached LLM outputs, confidence history and preferences
(02_ARCHITECTURE.md §11). Business records always live in Google Sheets;
this file exists purely to make the AI smarter over time.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT NOT NULL,
    canonical TEXT NOT NULL,
    alias_type TEXT NOT NULL CHECK (alias_type IN ('stakeholder', 'task', 'vocabulary')),
    confirmed_count INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(alias, alias_type)
);

CREATE TABLE IF NOT EXISTS embeddings (
    task_id TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    vector TEXT NOT NULL,
    source_text TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS confidence_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    task_id TEXT,
    stage TEXT NOT NULL,
    predicted_confidence REAL NOT NULL,
    user_accepted INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS response_cache (
    cache_key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS processed_requests (
    request_id TEXT PRIMARY KEY,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pending_confirmations (
    request_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class Database:
    def __init__(self, path: str) -> None:
        self._path = path

    async def init(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        async with aiosqlite.connect(self._path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[aiosqlite.Connection]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            yield db
