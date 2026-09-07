"""Common response / pagination schemas (U0)."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error body returned by the exception handlers."""

    error: str
    detail: str | None = None


class PageParams(BaseModel):
    """Common pagination query params."""

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


class Page(BaseModel, Generic[T]):
    """Generic paginated result envelope."""

    items: list[T]
    total: int
    offset: int
    limit: int
