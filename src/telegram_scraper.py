"""Telegram channel scraper relocated to src/ directory.
Run with:
    python -m src.telegram_scraper
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List

from telethon import TelegramClient
from telethon.errors import ChannelInvalidError, ChannelPrivateError
from telethon.tl.custom.message import Message
from telethon.tl.functions.messages import GetHistoryRequest

from src.config import settings

CHANNELS: List[str] = [
    "CheMed123",
    "lobelia4cosmetics",
    "tikvahpharma",
]

RAW_DATA_DIR = Path("data/raw")
MSG_DIR = RAW_DATA_DIR / "telegram_messages"
IMG_DIR = RAW_DATA_DIR / "telegram_images"
LOG_DIR = Path("logs")

# No date cutoff; we'll fetch the latest messages (newest first)
CUTOFF_DATE: datetime | None = None

# No hard cap; iterate until cutoff date reached
# Fetch at most 1 500 messages per channel to keep processing manageable
MESSAGE_LIMIT_PER_CHANNEL: int | None = 1500

def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(LOG_DIR / "scrape.log"), logging.StreamHandler()],
    )

def ensure_dirs() -> tuple[Path, Path]:
    today = date.today().isoformat()
    msg_dir = MSG_DIR / today
    img_dir = IMG_DIR / today
    msg_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)
    return msg_dir, img_dir


def message_to_dict(msg: Message) -> dict:
    return {
        "id": msg.id,
        "date": msg.date.isoformat() if msg.date else None,
        "message": msg.message,
        "from_id": getattr(msg.from_id, "user_id", None) if msg.from_id else None,
        "chat_id": getattr(msg.chat, "id", None) if msg.chat else None,
        "media": bool(msg.media),
    }


async def download_images(msg: Message, out_dir: Path) -> None:
    if not msg.media:
        return
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = await msg.download_media(file=out_dir)
        if path:
            logging.info("Downloaded media to %s", path)
    except Exception as exc:  # noqa: BLE001
        logging.warning("Failed to download media for message %s: %s", msg.id, exc)


async def scrape_channel(client: TelegramClient, channel: str, msg_out: Path, img_out: Path) -> None:
    logging.info("Scraping %s", channel)
    try:
        entity = await client.get_entity(channel)
    except (ChannelInvalidError, ChannelPrivateError) as exc:
        logging.error("Cannot access %s: %s", channel, exc)
        return

    hist = await client(
        GetHistoryRequest(peer=entity, limit=0, offset_date=None, add_offset=0, offset_id=0, max_id=0, min_id=0, hash=0)
    )
    logging.info("Total %s messages: %s", channel, hist.count)

    msgs: list[dict] = []
    async for msg in client.iter_messages(entity, limit=MESSAGE_LIMIT_PER_CHANNEL):
        # Messages are already returned in reverse chronological order; limit ensures we stop once we reach MESSAGE_LIMIT_PER_CHANNEL

        msgs.append(message_to_dict(msg))
        await download_images(msg, img_out / channel)

    out_file = msg_out / f"{channel}.json"
    out_file.write_text(json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("Saved %s messages to %s", len(msgs), out_file)


async def main() -> None:
    setup_logging()
    msg_out, img_out = ensure_dirs()

    if not (settings.api_id and settings.api_hash):
        raise RuntimeError("TG_API_ID and TG_API_HASH must be set")

    session_path = os.getenv("TG_SESSION", "session")
    async with TelegramClient(session_path, settings.api_id, settings.api_hash) as client:
        for chan in CHANNELS:
            await scrape_channel(client, chan, msg_out, img_out)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
