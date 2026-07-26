"""Centralised application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    All configuration is sourced from environment variables (or a local
    `.env` file during development). Nothing here should ever be hardcoded.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    app_name: str = "AI Work Journal"
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"

    # --- Telegram ---
    telegram_token: str = ""
    telegram_allowed_user_id: int | None = None
    telegram_webhook_secret: str = ""
    telegram_webhook_url: str = ""

    # --- LLM Providers ---
    llm_provider: Literal["anthropic", "openai", "gemini"] = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    openai_api_key: str = ""
    embedding_provider: Literal["openai"] = "openai"
    embedding_model: str = "text-embedding-3-large"

    # --- Google Sheets ---
    google_service_account_json: str = ""
    google_service_account_file: str = ""
    google_sheet_id: str = ""
    google_account_email: str = ""
    google_sheet_name: str = "AI Work Journal"

    # --- Storage ---
    database_path: str = "data/ai_work_journal.db"

    # --- Decision Engine thresholds (configurable, not hardcoded in prompts) ---
    confidence_auto_apply: float = 0.95
    confidence_confirm_lower_bound: float = 0.80

    # --- Reminders ---
    reminders_enabled: bool = True
    reminder_hour_local: int = 18
    reminder_minute_local: int = 0
    timezone: str = "Asia/Singapore"

    # --- Weekly / Monthly reports ---
    weekly_summary_enabled: bool = True
    weekly_summary_weekday: int = 4  # Friday (Mon=0)
    weekly_summary_hour_local: int = 17

    # --- API ---
    api_request_timeout_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
