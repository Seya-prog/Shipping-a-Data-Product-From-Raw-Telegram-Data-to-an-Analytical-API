"""Pydantic response models for the analytical API."""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class TopProduct(BaseModel):
    product: str = Field(..., description="Product name or object class")
    mentions: int = Field(..., ge=0)


class ChannelActivityPoint(BaseModel):
    date: datetime
    messages: int = Field(..., ge=0)


class MessageResult(BaseModel):
    message_id: int
    channel: str
    text: str
    date: datetime


class TopProductsResponse(BaseModel):
    items: List[TopProduct]


class ChannelActivityResponse(BaseModel):
    channel: str
    points: List[ChannelActivityPoint]


class MessageSearchResponse(BaseModel):
    query: str
    results: List[MessageResult]
