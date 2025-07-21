"""Database connection management for FastAPI service.

Uses a thread-safe connection pool (psycopg2) initialised at app start-up.
We reuse the credentials from ``src.config.settings`` so there is a single
source of truth.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from src.config import settings

logger = logging.getLogger(__name__)


class DatabasePool:  # pragma: no cover – thin wrapper
    """Singleton wrapper around a psycopg2 connection pool."""

    _pool: ThreadedConnectionPool | None = None

    @classmethod
    def init_pool(cls) -> None:
        if cls._pool is not None:
            return  # already initialised
        logger.info("Creating Postgres connection pool …")
        cls._pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            connect_timeout=5,
        )

    @classmethod
    def close_pool(cls) -> None:
        if cls._pool is not None:
            logger.info("Closing Postgres connection pool …")
            cls._pool.closeall()
            cls._pool = None

    @classmethod
    @contextmanager
    def connection(cls):  # type: ignore[return-type]
        """Context manager yielding a pooled connection."""
        if cls._pool is None:
            raise RuntimeError("Pool not initialised. Call init_pool() first.")
        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)


# convenience wrappers -------------------------------------------------------

@contextmanager
def get_cursor():  # type: ignore[return-type]
    """Yield a *cursor* from the pool and handle commit/rollback."""
    with DatabasePool.connection() as conn:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                yield cur
                conn.commit()
            except Exception:
                conn.rollback()
                raise
