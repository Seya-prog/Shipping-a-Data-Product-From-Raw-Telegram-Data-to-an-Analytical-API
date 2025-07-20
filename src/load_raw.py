"""Load raw Telegram JSON files into PostgreSQL (raw.telegram_messages).

This script is designed to be idempotent and safe to run multiple times.  It:
1. Creates the `raw` schema and `telegram_messages` table if they do not exist.
2. Scans the `data/raw/telegram_messages/<DATE>/` directory for `*.json` files, where
   `<DATE>` is the scrape execution date (e.g. `2025-07-20`).
3. Inserts only new messages (on primary-key conflict, the insert is ignored).
4. Adds minimal derived columns so downstream tools (dbt) can rely on a
   consistent structure.

Environment variables (loaded via `src.config.settings`):
    PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DB – fall-back defaults
    live in `src/config.py`.  Adjust via a `.env` file or CI secrets.

Usage:
    python -m src.load_raw  # or simply: python src/load_raw.py
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any, List, Tuple

import psycopg2
from psycopg2.extras import execute_batch, register_default_jsonb

from src.config import settings

# Ensure psycopg2 returns python dicts for JSON/JSONB columns
register_default_jsonb(loads=lambda x: x)

RAW_ROOT: Path = Path("data/raw/telegram_messages")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def get_conn() -> psycopg2.extensions.connection:
    """Connect to Postgres using credentials from `settings`."""
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        connect_timeout=5,
    )


def ensure_table(conn: psycopg2.extensions.connection) -> None:
    """Create raw schema & table if they do not exist."""
    create_sql = """
    create schema if not exists raw;

    create table if not exists raw.telegram_messages (
        id          bigint primary key,
        date        timestamptz,
        message     text,
        from_id     bigint,
        chat_id     bigint,
        media       boolean,
        channel     text,
        file_path   text,
        loaded_at   timestamptz default current_timestamp
    );
    """
    with conn, conn.cursor() as cur:
        cur.execute(create_sql)


def list_json_files() -> List[Path]:
    """Return all JSON files under today’s sub-directory."""
    today_dir = RAW_ROOT / date.today().isoformat()
    if not today_dir.exists():
        logger.warning("No scrape folder found at %s – nothing to load", today_dir)
        return []
    return list(today_dir.glob("*.json"))


def load_file(path: Path) -> List[Tuple[Any, ...]]:
    """Parse a single JSON file and return iterable rows for DB insert."""
    with path.open("r", encoding="utf-8") as f:
        msgs: list[dict[str, Any]] = json.load(f)
    channel = path.stem
    rows: list[tuple[Any, ...]] = []
    for m in msgs:
        rows.append(
            (
                m["id"],
                m["date"],
                m.get("message"),
                m.get("from_id"),
                m.get("chat_id"),
                m.get("media"),
                channel,
                str(path),
            )
        )
    return rows


def copy_into_db(conn: psycopg2.extensions.connection, rows: List[Tuple[Any, ...]]) -> None:
    """Insert rows with ON CONFLICT DO NOTHING."""
    if not rows:
        return
    insert_sql = """
    insert into raw.telegram_messages (
        id, date, message, from_id, chat_id, media, channel, file_path
    ) values (%s, %s, %s, %s, %s, %s, %s, %s)
    on conflict (id) do nothing;
    """
    with conn.cursor() as cur:
        execute_batch(cur, insert_sql, rows, page_size=1000)
    conn.commit()


def main() -> None:
    conn = get_conn()
    ensure_table(conn)

    files = list_json_files()
    total_inserted = 0
    for fp in files:
        try:
            rows = load_file(fp)
            before = total_inserted
            copy_into_db(conn, rows)
            total_inserted += len(rows)
            logger.info("Loaded %s rows from %s", len(rows), fp.name)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed loading %s: %s", fp, exc)
    logger.info("Finished. %s messages processed.", total_inserted)
    conn.close()


if __name__ == "__main__":
    main()
