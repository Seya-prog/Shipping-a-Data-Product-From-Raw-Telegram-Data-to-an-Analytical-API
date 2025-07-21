"""Dagster ops wrapping the existing ETL + ML scripts.

Each op simply shells out to the already-written script or command,
so we keep the single source of truth and avoid code duplication.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dagster import In, Nothing, Out, op

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PY_EXE = sys.executable  # e.g., path to python within the venv


def _run(cmd: list[str], context: OpExecutionContext) -> None:
    """Run *cmd* in a subprocess, streaming output to Dagster logs."""
    context.log.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


@op(out=Out(Nothing))
def scrape_telegram_data(context) -> None:
    """Fetch latest Telegram messages & images using Telethon scraper."""
    _run([PY_EXE, "-m", "src.telegram_scraper"], context)


@op(ins={"upstream": In(Nothing)}, out=Out(Nothing))
def load_raw_to_postgres(context) -> None:
    """Load scraped JSON files into raw.telegram_messages table."""
    _run([PY_EXE, "-m", "src.load_raw"], context)


@op(ins={"upstream": In(Nothing)}, out=Out(Nothing))
def run_dbt_transformations(context) -> None:
    """Execute dbt build & tests for all models."""
    _run(["dbt", "build", "--profiles-dir", "dbt"], context)


@op(ins={"upstream": In(Nothing)}, out=Out(Nothing))
def run_yolo_enrichment(context) -> None:
    """Run YOLOv8 detection to enrich images and insert detections."""
    _run([PY_EXE, "-m", "src.detect_objects"], context)
