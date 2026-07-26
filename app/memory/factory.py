from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.memory.database import Database


@lru_cache
def get_database() -> Database:
    return Database(get_settings().database_path)
