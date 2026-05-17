"""Global exception handling and request logging middleware.

Catches unhandled exceptions and returns consistent JSON error responses.
Logs errors with request context for debugging.
Adds structured request logging with timing.
"""

import time
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status code, and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        # Skip noisy endpoints
        if path in ("/health", "/metrics"):
            return await call_next(request)

        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Log with structured context
        logger.bind(
            method=method,
            path=path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
            client=request.client.host if request.client else "unknown",
        ).info(f"{method} {path} → {response.status_code} ({duration_ms:.1f}ms)")

        return response


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions (including our AppException subclasses)."""
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.status_code, exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors with readable messages."""
        errors = []
        for err in exc.errors():
            loc = " → ".join(str(l) for l in err.get("loc", []))
            errors.append(f"{loc}: {err.get('msg', 'invalid')}")

        detail = "; ".join(errors) if errors else "请求参数验证失败"

        logger.warning(
            f"Validation error: {request.method} {request.url.path} | {detail}"
        )

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": 422,
                    "message": "请求参数验证失败",
                    "details": errors,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions. Logs full traceback."""
        tb = traceback.format_exc()
        logger.error(
            f"Unhandled exception: {request.method} {request.url.path}\n"
            f"Error: {type(exc).__name__}: {exc}\n"
            f"Traceback:\n{tb}"
        )

        return JSONResponse(
            status_code=500,
            content=_error_body(500, "服务器内部错误，请稍后重试"),
        )


def _error_body(code: int, detail: Any) -> dict:
    """Build consistent error response body."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": detail if isinstance(detail, str) else str(detail),
        },
    }
