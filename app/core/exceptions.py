"""Custom exception classes for the application."""

from typing import Any


class ApplicationException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize exception.

        Args:
            message: Error message.
            status_code: HTTP status code.
            error_code: Application-specific error code.
            details: Additional error details.
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(ApplicationException):
    """Validation error exception."""

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundException(ApplicationException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
        )


class UnauthorizedException(ApplicationException):
    """Unauthorized access exception."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(ApplicationException):
    """Forbidden access exception."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
        )


class ConflictException(ApplicationException):
    """Resource conflict exception."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
        )
