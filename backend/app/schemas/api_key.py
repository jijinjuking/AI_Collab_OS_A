"""API Key request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    """Request: create a new API key."""
    name: str = Field(min_length=1, max_length=100)
    scopes: str = Field(default="read,write", max_length=200)
    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    """Response: API key info (no secret)."""
    id: str
    name: str
    key_prefix: str
    scopes: str
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class ApiKeyCreated(ApiKeyResponse):
    """Response: newly created API key (includes the raw key, shown only once)."""
    raw_key: str
