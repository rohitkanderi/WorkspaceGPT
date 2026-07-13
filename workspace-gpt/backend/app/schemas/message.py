"""Pydantic schemas for messages."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from app.schemas.base import SchemaBase

MessageRoleValue = Literal["system", "user", "assistant", "tool"]


class MessageBase(SchemaBase):
    """Common message fields."""

    conversation_id: int
    role: MessageRoleValue
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a message."""


class MessageRead(MessageBase):
    """Schema returned for a message."""

    id: int
    created_at: datetime
