"""Shared Pydantic v2 schema helpers."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SchemaBase(BaseModel):
    """Base class for API schemas that can serialize ORM/dataclass objects."""

    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(SchemaBase):
    """Common timestamp fields for persisted resources."""

    created_at: datetime
    updated_at: datetime
