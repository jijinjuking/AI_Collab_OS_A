"""Project Agent model — a concrete agent instance bound to a project."""

from typing import Any

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.types import JSON
from sqlmodel import Field

from app.db.models.base import TimestampModel, UUIDModel


class ProjectAgent(UUIDModel, TimestampModel, table=True):
    """An agent instance in a project (e.g. 前端1号, 架构师A)."""

    __tablename__ = "project_agents"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "role_template_id",
            "instance_index",
            name="uq_agent_project_role_index",
        ),
    )

    project_id: str = Field(
        foreign_key="projects.id", index=True, max_length=36, nullable=False
    )
    role_template_id: str = Field(
        foreign_key="role_templates.id", index=True, max_length=36, nullable=False
    )
    instance_name: str = Field(max_length=100, nullable=False)
    instance_index: int = Field(nullable=False)
    # idle / working / paused / error
    status: str = Field(default="idle", max_length=20, index=True)

    provider: str | None = Field(default=None, max_length=50)
    base_url: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=100)
    api_key_id: str | None = Field(default=None, max_length=36)
    system_prompt_override: str | None = Field(default=None)
    config: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    token_used: int = Field(default=0)
