"""Data access helpers for analytical endpoints."""
from __future__ import annotations

from typing import List, Dict, Any

from psycopg2.extras import RealDictCursor

from .database import get_cursor


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def fetch_top_products(limit: int = 10) -> List[Dict[str, Any]]:
    sql = """
        select object_class as product, count(*) as mentions
        from raw.image_detections
        group by object_class
        order by mentions desc
        limit %s;
    """
    with get_cursor() as cur:  # type: RealDictCursor
        cur.execute(sql, (limit,))
        return cur.fetchall()


def fetch_channel_activity(channel: str) -> List[Dict[str, Any]]:
    sql = """
        select date_trunc('day', date) as date, count(*) as messages
        from raw.telegram_messages
        where channel = %s
        group by date
        order by date;
    """
    with get_cursor() as cur:
        cur.execute(sql, (channel,))
        return cur.fetchall()


def search_messages(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    sql = """
        select id as message_id, channel, message as text, date
        from raw.telegram_messages
        where message ilike %s
        order by date desc
        limit %s;
    """
    pattern = f"%{query}%"
    with get_cursor() as cur:
        cur.execute(sql, (pattern, limit))
        return cur.fetchall()
