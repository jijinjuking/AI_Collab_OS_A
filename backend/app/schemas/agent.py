"""Agent-related request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class RoleTemplateCreate(BaseModel):
    """Create a custom role template."""

    key: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=50)
    icon: str | None = None
    system_prompt: str = Field(min_length=10)
    skills: list[str] | None = None
    default_model: str | None = None


class RoleTemplateOut(BaseModel):
    """Role template response."""

    id: str
    key: str
    name: str
    icon: str | None
    system_prompt: str
    skills: list[str] | None
    default_model: str | None
    is_system: bool
    user_id: str | None


class AgentChatRequest(BaseModel):
    """Send a message to an agent for conversation."""

    message: str = Field(min_length=1)
    # Optional: override model/provider for this call
    model: str | None = None
    provider: str | None = None
    temperature: float | None = None
    stream: bool = True


class AgentChatResponse(BaseModel):
    """Non-streaming agent chat response."""

    content: str
    model_used: str
    token_count: int
    message_id: str


# --- Agent Instance Management ---


class AgentInstanceCreate(BaseModel):
    """Create an agent instance in a project."""

    role_template_id: str
    instance_name: str = Field(min_length=1, max_length=100)
    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    system_prompt_override: str | None = None
    config: dict[str, Any] | None = None


class AgentInstanceUpdate(BaseModel):
    """Update an agent instance."""

    instance_name: str | None = Field(default=None, max_length=100)
    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    system_prompt_override: str | None = None
    config: dict[str, Any] | None = None
    status: str | None = Field(default=None, pattern="^(idle|working|paused|error)$")


class AgentInstanceOut(BaseModel):
    """Agent instance response."""

    id: str
    project_id: str
    role_template_id: str
    instance_name: str
    instance_index: int
    status: str
    provider: str | None
    base_url: str | None
    model: str | None
    system_prompt_override: str | None
    config: dict[str, Any] | None
    token_used: int
    created_at: str
    updated_at: str
