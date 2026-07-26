"""Persistence abstraction for AI-specific metadata (SQLite).

Everything here supports AI behaviour, never user-facing business
records (03_IMPLEMENTATION.md §15). The learning rule enforced at the
call sites (services layer), not here, is that writes only happen after
explicit user confirmation.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from app.memory.database import Database


class MemoryRepository:
    def __init__(self, database: Database) -> None:
        self._db = database

    # --- Preferences (generic key/value, e.g. auto-created sheet id) ---

    async def get_preference(self, key: str) -> str | None:
        async with self._db.connect() as conn:
            cursor = await conn.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row["value"] if row else None

    async def set_preference(self, key: str, value: str) -> None:
        async with self._db.connect() as conn:
            await conn.execute(
                "INSERT INTO preferences (key, value, updated_at) VALUES (?, ?, datetime('now')) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')",
                (key, value),
            )
            await conn.commit()

    # --- Aliases (learned stakeholder/task/vocabulary mappings) ---

    async def resolve_alias(self, alias: str, alias_type: str) -> str | None:
        async with self._db.connect() as conn:
            cursor = await conn.execute(
                "SELECT canonical FROM aliases WHERE alias = ? AND alias_type = ?",
                (alias.strip().lower(), alias_type),
            )
            row = await cursor.fetchone()
            return row["canonical"] if row else None

    async def list_aliases(self, alias_type: str) -> dict[str, str]:
        async with self._db.connect() as conn:
            cursor = await conn.execute("SELECT alias, canonical FROM aliases WHERE alias_type = ?", (alias_type,))
            rows = await cursor.fetchall()
            return {row["alias"]: row["canonical"] for row in rows}

    async def learn_alias(self, alias: str, canonical: str, alias_type: str) -> None:
        """Record (or reinforce) a confirmed alias. Only call after user confirmation."""
        normalised = alias.strip().lower()
        if normalised == canonical.strip().lower():
            return
        async with self._db.connect() as conn:
            await conn.execute(
                """
                INSERT INTO aliases (alias, canonical, alias_type, confirmed_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(alias, alias_type) DO UPDATE SET
                    canonical = excluded.canonical,
                    confirmed_count = confirmed_count + 1,
                    updated_at = datetime('now')
                """,
                (normalised, canonical, alias_type),
            )
            await conn.commit()

    # --- Embeddings ---

    async def save_embedding(self, task_id: str, vector: list[float], model: str, source_text: str) -> None:
        async with self._db.connect() as conn:
            await conn.execute(
                """
                INSERT INTO embeddings (task_id, model, vector, source_text, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                ON CONFLICT(task_id) DO UPDATE SET
                    model = excluded.model,
                    vector = excluded.vector,
                    source_text = excluded.source_text,
                    updated_at = datetime('now')
                """,
                (task_id, model, json.dumps(vector), source_text),
            )
            await conn.commit()

    async def get_all_embeddings(self) -> dict[str, list[float]]:
        async with self._db.connect() as conn:
            cursor = await conn.execute("SELECT task_id, vector FROM embeddings")
            rows = await cursor.fetchall()
            return {row["task_id"]: json.loads(row["vector"]) for row in rows}

    async def delete_embedding(self, task_id: str) -> None:
        async with self._db.connect() as conn:
            await conn.execute("DELETE FROM embeddings WHERE task_id = ?", (task_id,))
            await conn.commit()

    # --- Confidence history / adaptive confidence ---

    async def record_confidence_outcome(
        self,
        *,
        request_id: str,
        task_id: str | None,
        stage: str,
        predicted_confidence: float,
        user_accepted: bool | None,
    ) -> None:
        async with self._db.connect() as conn:
            await conn.execute(
                """
                INSERT INTO confidence_history
                    (request_id, task_id, stage, predicted_confidence, user_accepted)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    task_id,
                    stage,
                    predicted_confidence,
                    None if user_accepted is None else int(user_accepted),
                ),
            )
            await conn.commit()

    async def get_acceptance_rate(self, stage: str, *, task_id: str | None = None) -> float | None:
        """Historical acceptance rate for a stage, optionally scoped to one task.

        Used to nudge confidence upward for patterns the AI has repeatedly
        gotten right for this user (04_AI_DESIGN.MD §9, Adaptive Confidence).
        """
        query = "SELECT AVG(user_accepted) as rate, COUNT(*) as n FROM confidence_history WHERE stage = ? AND user_accepted IS NOT NULL"
        params: list[object] = [stage]
        if task_id is not None:
            query += " AND task_id = ?"
            params.append(task_id)
        async with self._db.connect() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            if row is None or row["n"] == 0:
                return None
            return float(row["rate"])

    # --- Response cache ---

    async def cache_get(self, key: str) -> str | None:
        async with self._db.connect() as conn:
            cursor = await conn.execute("SELECT value, expires_at FROM response_cache WHERE cache_key = ?", (key,))
            row = await cursor.fetchone()
            if row is None:
                return None
            if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) < datetime.now(UTC):
                return None
            return row["value"]

    async def cache_set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        expires_at = (datetime.now(UTC) + timedelta(seconds=ttl_seconds)).isoformat() if ttl_seconds else None
        async with self._db.connect() as conn:
            await conn.execute(
                """
                INSERT INTO response_cache (cache_key, value, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at
                """,
                (key, value, expires_at),
            )
            await conn.commit()

    # --- Idempotency (webhook retry protection) ---

    async def get_processed_request(self, request_id: str) -> str | None:
        async with self._db.connect() as conn:
            cursor = await conn.execute(
                "SELECT result_json FROM processed_requests WHERE request_id = ?", (request_id,)
            )
            row = await cursor.fetchone()
            return row["result_json"] if row else None

    async def mark_request_processed(self, request_id: str, result_json: str) -> None:
        async with self._db.connect() as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO processed_requests (request_id, result_json) VALUES (?, ?)",
                (request_id, result_json),
            )
            await conn.commit()

    # --- Pending confirmations (awaiting a Telegram button tap) ---

    async def save_pending_confirmation(self, request_id: str, user_id: str, payload_json: str) -> None:
        async with self._db.connect() as conn:
            await conn.execute(
                """
                INSERT INTO pending_confirmations (request_id, user_id, payload_json)
                VALUES (?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET payload_json = excluded.payload_json
                """,
                (request_id, user_id, payload_json),
            )
            await conn.commit()

    async def get_pending_confirmation(self, request_id: str) -> str | None:
        async with self._db.connect() as conn:
            cursor = await conn.execute(
                "SELECT payload_json FROM pending_confirmations WHERE request_id = ?", (request_id,)
            )
            row = await cursor.fetchone()
            return row["payload_json"] if row else None

    async def delete_pending_confirmation(self, request_id: str) -> None:
        async with self._db.connect() as conn:
            await conn.execute("DELETE FROM pending_confirmations WHERE request_id = ?", (request_id,))
            await conn.commit()
