"""Workflow request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    """Create a new workflow."""

    name: str | None = None
    type: str = Field(pattern="^(full|frontend|backend|custom)$")
    dag_config: dict[str, Any]
    mode: str = Field(default="manual", pattern="^(auto|manual)$")
    max_review_rounds: int = Field(default=3, ge=1, le=10)


class WorkflowOut(BaseModel):
    """Workflow response."""

    id: str
    project_id: str
    name: str | None
    type: str
    status: str
    dag_config: dict[str, Any]
    current_step_id: str | None
    mode: str
    max_review_rounds: int
    started_at: str | None
    completed_at: str | None
    created_at: str
    updated_at: str


class WorkflowListOut(BaseModel):
    """Lightweight workflow list item."""

    id: str
    name: str | None
    type: str
    status: str
    mode: str
    created_at: str


class WorkflowStartRequest(BaseModel):
    """Start a workflow execution."""

    task_description: str = Field(min_length=1)
