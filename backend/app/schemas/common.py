"""Common response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseBase(BaseModel):
    """Standard API response wrapper."""

    code: int = 0
    message: str = "success"
    data: Any = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
