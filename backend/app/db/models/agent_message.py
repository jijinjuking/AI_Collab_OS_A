"""Agent message model — every conversation, handoff, review, and system event."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, Index
from sqlalchemy.types import JSON, Text
from sqlmodel import Field

from app.db.models.base import UUIDModel, utcnow


class AgentMessage(UUIDModel, table=True):
    """A persistent record of all agent and user communication."""

    __tablename__ = "agent_messages"
    __table_args__ = (
        Index("ix_msg_project_created", "project_id", "created_at"),
        Index("ix_msg_workflow", "workflow_id"),
        Index("ix_msg_from_agent", "from_agent_id"),
        Index("ix_msg_to_agent", "to_agent_id"),
    )

    project_id: str = Field(
        foreign_key="projects.id", max_length=36, nullable=False
    )
    # workflow / agent FKs are added when those tables exist; keep loose for M1
    workflow_id: str | None = Field(default=None, max_length=36)
    from_agent_id: str | None = Field(
        default=None, foreign_key="project_agents.id", max_length=36
    )
    to_agent_id: str | None = Field(
        default=None, foreign_key="project_agents.id", max_length=36
    )

    # chat / handoff / issue / review / discuss / system
    message_type: str = Field(max_length=20, nullable=False)
    # user / assistant / system
    role: str = Field(max_length=20, nullable=False)

    content: str = Field(sa_column=Column(Text, nullable=False))
    summary: str | None = Field(default=None, max_length=500)
    meta: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )
    token_count: int | None = Field(default=None)
    model_used: str | None = Field(default=None, max_length=100)

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
