"""APScheduler wiring (03_IMPLEMENTATION.md §22 — "APScheduler provides
sufficient functionality" for the MVP)."""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

from app.core.container import Container
from app.jobs.embedding_refresh_job import refresh_all_embeddings
from app.jobs.reminder_job import send_daily_reminder
from app.jobs.weekly_summary_job import send_weekly_summary


def build_scheduler(container: Container, bot: Bot) -> AsyncIOScheduler:
    settings = container.settings
    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    scheduler.add_job(
        send_daily_reminder,
        CronTrigger(hour=settings.reminder_hour_local, minute=settings.reminder_minute_local),
        args=[container, bot],
        id="daily_reminder",
        replace_existing=True,
    )
    scheduler.add_job(
        send_weekly_summary,
        CronTrigger(day_of_week=settings.weekly_summary_weekday, hour=settings.weekly_summary_hour_local),
        args=[container, bot],
        id="weekly_summary",
        replace_existing=True,
    )
    scheduler.add_job(
        refresh_all_embeddings,
        CronTrigger(hour=3, minute=0),
        args=[container],
        id="nightly_embedding_refresh",
        replace_existing=True,
    )

    return scheduler
