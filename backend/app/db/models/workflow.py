"""Workflow and WorkflowStep models."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field

from app.db.models.base import TimestampModel, UUIDModel, utcnow


class Workflow(UUIDModel, TimestampModel, table=True):
    """A workflow defines a DAG of agent execution steps."""

    __tablename__ = "workflows"

    project_id: str = Field(foreign_key="projects.id", index=True, max_length=36)
    name: str | None = Field(default=None, max_length=100)
    # full / frontend / backend / custom
    type: str = Field(max_length=30, nullable=False)
    # pending / running / paused / completed / failed
    status: str = Field(default="pending", max_length=20, index=True)
    dag_config: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    current_step_id: str | None = Field(default=None, max_length=36)
    # auto / manual
    mode: str = Field(default="manual", max_length=10)
    max_review_rounds: int = Field(default=3)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)


class WorkflowStep(UUIDModel, table=True):
    """A single step in a workflow execution."""

    __tablename__ = "workflow_steps"

    workflow_id: str = Field(foreign_key="workflows.id", index=True, max_length=36)
    agent_id: str = Field(foreign_key="project_agents.id", max_length=36)
    # execute / review / discuss / assign
    step_type: str = Field(max_length=30, nullable=False)
    step_order: int = Field(nullable=False)
    depends_on: list[str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    # pending / running / completed / failed / skipped
    status: str = Field(default="pending", max_length=20)
    input_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    output_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    review_round: int = Field(default=0)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
