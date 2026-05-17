"""Role template model — system presets and user-customised role definitions."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.types import JSON
from sqlmodel import Field

from app.db.models.base import UUIDModel, utcnow


class RoleTemplate(UUIDModel, table=True):
    """A reusable agent role definition (PM, Architect, Frontend, ...)."""

    __tablename__ = "role_templates"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_role_user_key"),
    )

    # NULL → system preset, otherwise → user-defined override/custom
    user_id: str | None = Field(
        default=None, foreign_key="users.id", index=True, max_length=36
    )
    key: str = Field(max_length=50, nullable=False, index=True)
    name: str = Field(max_length=50, nullable=False)
    icon: str | None = Field(default=None, max_length=50)
    system_prompt: str = Field(nullable=False)
    skills: list[str] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    default_model: str | None = Field(default=None, max_length=100)
    is_system: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
