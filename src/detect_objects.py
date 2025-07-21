"""Detect objects in Telegram images using YOLOv8 and write results to Postgres.

This script scans `raw.telegram_messages` records where `media = true`, loads the
associated image from disk, runs YOLOv8 inference, and stores each detected
object into `raw.image_detections`.

Table definition (created if missing):
    raw.image_detections (
        message_id      bigint      -- FK -> raw.telegram_messages.id
      , object_class    text        -- YOLO label (e.g. "person")
      , confidence      numeric     -- 0-1
      , detected_at     timestamptz default current_timestamp
      , primary key (message_id, object_class, confidence)
    )

Run:
    python -m src.detect_objects

Environment variables: see `src.config.py` (same as loader).
"""
from __future__ import annotations

import logging

import json
from pathlib import Path
from typing import List, Tuple

import psycopg2
from psycopg2.extras import execute_batch
from ultralytics import YOLO

from src.config import settings

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Use the lightweight nano model for fast local inference; change if desired
YOLO_MODEL = "yolov8n.pt"
IMAGE_ROOT = Path("data/raw/telegram_images")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


# --- Path helpers -----------------------------------------------------------

def is_image_file(p: Path) -> bool:
    """Return True if *p* is an existing image with an allowed extension."""
    return p.suffix.lower() in IMAGE_EXTS and p.exists()
    """Return a Path to an existing image for the given message.

    1. If *json_or_img_path* already points to an existing file with an image
       extension, return it.
    2. If the path ends with `.json`, open the file, locate the message with
       matching *message_id*, and extract the `file` field (direct or under
       `media`). If that file exists on disk return it.
    3. Otherwise, try a simple fallback: IMAGE_ROOT / <filename>.
    4. Return None if nothing is found.
    """
    # case 1 – already an image path
    if json_or_img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}:
        return json_or_img_path if json_or_img_path.exists() else None

    # case 2 – JSON path
    if json_or_img_path.suffix.lower() == ".json" and json_or_img_path.exists():
        try:
            with json_or_img_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "messages" in data:
                messages = data["messages"]
            elif isinstance(data, list):
                messages = data
            else:
                messages = []
            for m in messages:
                if not isinstance(m, dict):
                    continue
                if m.get("id") == message_id:
                    fp = m.get("file")
                    if not fp:
                        media_field = m.get("media")
                        if isinstance(media_field, dict):
                            fp = media_field.get("file")
                    if fp:
                        p = Path(fp)
                        if p.exists():
                            return p
                        # If stored path lacks scrape-date folder, attempt under IMAGE_ROOT
                        candidate = IMAGE_ROOT / p.name
                        if candidate.exists():
                            return candidate
                    else:
                        # last resort: search dict values for any string that looks like image path
                        def _find_image_path(obj):
                            if isinstance(obj, str) and Path(obj).suffix.lower() in {'.jpg','.jpeg','.png','.webp','.bmp','.tif','.tiff'}:
                                p = Path(obj)
                                if p.exists():
                                    return p
                                cand = IMAGE_ROOT / p.name
                                if cand.exists():
                                    return cand
                            if isinstance(obj, dict):
                                for v in obj.values():
                                    res = _find_image_path(v)
                                    if res:
                                        return res
                            if isinstance(obj, list):
                                for v in obj:
                                    res = _find_image_path(v)
                                    if res:
                                        return res
                            return None
                        res_p = _find_image_path(m)
                        if res_p:
                            return res_p
                    break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not parse %s: %s", json_or_img_path, exc)

    # case 3 – fallback by filename
    candidate = IMAGE_ROOT / json_or_img_path.name
    if candidate.exists():
        return candidate

    return None

def get_conn() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        connect_timeout=5,
    )

def ensure_table(conn: psycopg2.extensions.connection) -> None:
    sql = """
    create schema if not exists raw;

    create table if not exists raw.image_detections (
        message_id   bigint,
        object_class text,
        confidence   numeric,
        detected_at  timestamptz default current_timestamp,
        primary key (message_id, object_class, confidence)
    );
    """
    with conn, conn.cursor() as cur:
        cur.execute(sql)


def fetch_unprocessed(conn: psycopg2.extensions.connection) -> List[Tuple[int, str, str, str]]:
    """Return (message_id, channel, ts_iso, file_path) where no detections exist."""
    sql = """
        select id, channel, to_char(date at time zone 'UTC', 'YYYY-MM-DD_HH24-MI-SS') as ts, file_path
        from raw.telegram_messages m
        where m.media is true
          and not exists (
              select 1 from raw.image_detections d where d.message_id = m.id
          );
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def insert_detections(
    conn: psycopg2.extensions.connection,
    rows: List[Tuple[int, str, float]],
) -> None:
    if not rows:
        return
    sql = """
        insert into raw.image_detections (message_id, object_class, confidence)
        values (%s, %s, %s)
        on conflict do nothing;
    """
    with conn, conn.cursor() as cur:
        execute_batch(cur, sql, rows, page_size=1000)
    conn.commit()


def detect_on_image(model: YOLO, img_path: Path) -> List[Tuple[str, float]]:
    """Run YOLO and return list of (class_name, confidence)."""
    results = model(img_path, verbose=False)[0]
    names = results.names  # mapping id -> label
    detections: List[Tuple[str, float]] = []
    if results.boxes is None:
        return detections
    for cls_id, conf in zip(results.boxes.cls, results.boxes.conf):  # type: ignore[attr-defined]
        label = names[int(cls_id)]
        detections.append((label, float(conf)))
    return detections


def main() -> None:
    logger.info("Loading YOLOv8 model – this may download weights on first run …")
    model = YOLO(YOLO_MODEL)

    conn = get_conn()
    ensure_table(conn)

    tasks = fetch_unprocessed(conn)
    if not tasks:
        logger.info("No new images to process – exiting.")
        return

    total_rows = 0
    for msg_id, channel, ts_str, path_str in tasks:
        img_path = Path(path_str)
        if not is_image_file(img_path):
            # try glob search by channel + timestamp
            pattern = f"**/{channel}/photo_{ts_str}.jpg"
            matches = list(IMAGE_ROOT.glob(pattern))
            if matches:
                img_path = matches[0]
            else:
                logger.warning("Image not found for message %s (channel %s ts %s)", msg_id, channel, ts_str)
                continue
        try:
            dets = detect_on_image(model, img_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("YOLO failed on %s: %s", img_path, exc)
            continue
        rows = [(msg_id, cls, conf) for cls, conf in dets]
        insert_detections(conn, rows)
        total_rows += len(rows)
        logger.info("%s detections saved for message %s (%s)", len(rows), msg_id, img_path.name)

    conn.close()
    logger.info("Finished. %s detections inserted.", total_rows)


if __name__ == "__main__":
    main()
