"""Dagster schedules for automated runs."""
from __future__ import annotations

from datetime import time

from dagster import ScheduleDefinition

from .jobs import telegram_pipeline_job

# Run every day at 02:00 AM local (server) time

daily_telegram_schedule = ScheduleDefinition(
    job=telegram_pipeline_job,
    cron_schedule="0 2 * * *",  # minute hour day month dow
    execution_timezone="UTC",  # change if you prefer specific tz
    name="daily_telegram_schedule",
)
