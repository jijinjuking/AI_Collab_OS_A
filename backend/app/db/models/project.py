"""Project model."""

from typing import Any

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field

from app.db.models.base import TimestampModel, UUIDModel


class Project(UUIDModel, TimestampModel, table=True):
    """A user's project containing agents, workflows and files."""

    __tablename__ = "projects"

    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    name: str = Field(max_length=100, nullable=False)
    description: str | None = Field(default=None)
    plan: str | None = Field(default=None)
    # draft / active / paused / completed / archived
    status: str = Field(default="draft", max_length=20, index=True)
    config: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    workspace_path: str | None = Field(default=None, max_length=500)
