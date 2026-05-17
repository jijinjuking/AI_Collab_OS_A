"""Auth request/response schemas."""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """User registration payload."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    """User login payload."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str


class UserInfo(BaseModel):
    """Current user info (returned by /me)."""

    id: str
    username: str
    email: str | None
    role: str
    settings: dict | None = None
