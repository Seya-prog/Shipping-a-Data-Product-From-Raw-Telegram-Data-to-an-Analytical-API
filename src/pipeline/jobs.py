"""Dagster job wiring the ETL/ML ops into a single pipeline."""
from __future__ import annotations

from dagster import job

from .ops import (
    scrape_telegram_data,
    load_raw_to_postgres,
    run_dbt_transformations,
    run_yolo_enrichment,
)


@job
def telegram_pipeline_job():
    """End-to-end pipeline: scrape → load → dbt → YOLO."""

    # Dependency order expressed by nested calls
    run_yolo_enrichment(
        run_dbt_transformations(
            load_raw_to_postgres(
                scrape_telegram_data()
            )
        )
    )
