"""Custom exception classes for the application."""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
    ):
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationError(AppException):
    """Authentication failed."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(AppException):
    """Insufficient permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", detail: str | None = None):
        msg = detail or f"{resource} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


class ConflictError(AppException):
    """Resource conflict (duplicate, locked, etc.)."""

    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationError(AppException):
    """Business logic validation error."""

    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
