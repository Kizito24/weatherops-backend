"""Standardized API response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail information."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = Field(False)
    message: str
    error_code: str
    details: list[ErrorDetail] = Field(default_factory=list)


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response."""

    success: bool = Field(True)
    data: T
    message: str = Field(default="Request successful")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response."""

    success: bool = Field(True)
    data: list[T]
    total: int
    skip: int
    limit: int
    message: str = Field(default="Request successful")
