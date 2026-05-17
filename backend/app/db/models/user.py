"""User model."""

from typing import Any

from sqlalchemy import Column, String
from sqlalchemy.types import JSON
from sqlmodel import Field

from app.db.models.base import TimestampModel, UUIDModel


class User(UUIDModel, TimestampModel, table=True):
    """User account."""

    __tablename__ = "users"

    username: str = Field(
        sa_column=Column(String(50), unique=True, nullable=False, index=True)
    )
    email: str | None = Field(
        default=None,
        sa_column=Column(String(100), unique=True, nullable=True, index=True),
    )
    password_hash: str = Field(max_length=255, nullable=False)
    role: str = Field(default="user", max_length=20)  # admin/user
    settings: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
