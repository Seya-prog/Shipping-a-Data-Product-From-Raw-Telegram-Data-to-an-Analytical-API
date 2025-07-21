"""Dagster repository for the Telegram data product.

Run locally with::

    dagster dev

This exposes the UI at http://localhost:3000 where you can run & monitor the
`telegram_pipeline_job` and its daily schedule.
"""
from __future__ import annotations

from dagster import Definitions

from .jobs import telegram_pipeline_job
from .schedules import daily_telegram_schedule

# Dagster entry-point. The `dagster` CLI discovers this "defs" object.

defs = Definitions(jobs=[telegram_pipeline_job], schedules=[daily_telegram_schedule])
