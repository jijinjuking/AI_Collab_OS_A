"""Project request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Create a new project."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    plan: str | None = None
    config: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    """Update an existing project."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    plan: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|active|paused|completed|archived)$")
    config: dict[str, Any] | None = None


class ProjectOut(BaseModel):
    """Project response."""

    id: str
    user_id: str
    name: str
    description: str | None
    plan: str | None
    status: str
    config: dict[str, Any] | None
    workspace_path: str | None
    created_at: str
    updated_at: str


class ProjectListOut(BaseModel):
    """Lightweight project list item."""

    id: str
    name: str
    status: str
    description: str | None
    created_at: str
