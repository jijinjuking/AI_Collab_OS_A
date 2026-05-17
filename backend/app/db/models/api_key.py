"""API Key model — programmatic access tokens for external integrations."""

from datetime import datetime

from sqlalchemy import Column, String, Text
from sqlmodel import Field

from app.db.models.base import TimestampModel, UUIDModel, utcnow


class ApiKey(UUIDModel, TimestampModel, table=True):
    """An API key for programmatic access (alternative to JWT)."""

    __tablename__ = "api_keys"

    user_id: str = Field(
        foreign_key="users.id", index=True, max_length=36, nullable=False
    )
    name: str = Field(max_length=100, nullable=False)
    # Store only the hash of the key; the raw key is shown once at creation
    key_hash: str = Field(sa_column=Column(String(255), nullable=False, unique=True))
    # First 8 chars of the key for identification (e.g. "ak_1a2b3c4d...")
    key_prefix: str = Field(max_length=12, nullable=False)
    # Scopes: comma-separated (e.g. "read,write,admin")
    scopes: str = Field(default="read,write", max_length=200)
    # Optional expiration
    expires_at: datetime | None = Field(default=None)
    last_used_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
