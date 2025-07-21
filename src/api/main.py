"""FastAPI application exposing analytical endpoints over the Telegram data mart.

Run locally with:

    uvicorn src.api.main:app --reload

The API intentionally exposes *analytical* endpoints (not generic CRUD) that
answer concrete business questions using SQL against the warehouse. Results are
validated with Pydantic models.
"""
from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI, Query, Path, HTTPException
from fastapi.responses import JSONResponse, Response

from .database import DatabasePool
from . import crud, schemas

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Analytics API", version="0.1.0")


# ---------------------------------------------------------------------------
# Lifespan events
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def _startup() -> None:  # pragma: no cover – side-effect only
    DatabasePool.init_pool()
    logger.info("API started – connection pool initialised")


@app.on_event("shutdown")
async def _shutdown() -> None:  # pragma: no cover
    DatabasePool.close_pool()
    logger.info("API shutdown – connection pool closed")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/api/reports/top-products",
    response_model=schemas.TopProductsResponse,
    summary="Top products (object classes) mentioned in images",
)
async def top_products(limit: int = Query(10, ge=1, le=100)) -> schemas.TopProductsResponse:
    """Return the *limit* most frequent YOLO object classes detected in images."""
    rows = crud.fetch_top_products(limit)
    items = [schemas.TopProduct(**row) for row in rows]
    return schemas.TopProductsResponse(items=items)


@app.get(
    "/api/channels/{channel_name}/activity",
    response_model=schemas.ChannelActivityResponse,
    summary="Posting activity for a Telegram channel",
)
async def channel_activity(
    channel_name: str = Path(..., title="Channel name"),
) -> schemas.ChannelActivityResponse:
    rows = crud.fetch_channel_activity(channel_name)
    if not rows:
        raise HTTPException(status_code=404, detail="Channel not found or no activity")
    points = [schemas.ChannelActivityPoint(**row) for row in rows]
    return schemas.ChannelActivityResponse(channel=channel_name, points=points)


@app.get(
    "/api/search/messages",
    response_model=schemas.MessageSearchResponse,
    summary="Search messages containing a keyword",
)
async def search_messages(
    query: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
) -> schemas.MessageSearchResponse:
    rows = crud.search_messages(query, limit)
    results = [schemas.MessageResult(**row) for row in rows]
    return schemas.MessageSearchResponse(query=query, results=results)


# ---------------------------------------------------------------------------
# Favicon
# ---------------------------------------------------------------------------
import base64

# 16×16 transparent PNG (1×1 pixel) encoded in base64
_FAVICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
    "ASsJTYQAAAAASUVORK5CYII="
)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    png_bytes = base64.b64decode(_FAVICON_B64)
    return Response(content=png_bytes, media_type="image/png")

# ---------------------------------------------------------------------------
# Health and root
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> JSONResponse:  # untyped simple response
    return JSONResponse({"status": "ok"})


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"message": "Telegram Analytical API – see /docs"})
