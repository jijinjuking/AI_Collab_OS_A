"""Base model utilities: UUID primary keys + timestamps."""

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Naive UTC now, compatible with TIMESTAMP WITHOUT TIME ZONE columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_uuid() -> str:
    """Generate a new UUID string. We store UUIDs as VARCHAR(36) for cross-DB portability."""
    return str(uuid.uuid4())


class UUIDModel(SQLModel):
    """Mixin: UUID primary key stored as string."""

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)


class TimestampModel(SQLModel):
    """Mixin: created_at + updated_at columns."""

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
