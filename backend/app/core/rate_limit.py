"""Rate limiting middleware — sliding window counter via Redis.

Supports per-user and per-IP rate limiting with configurable windows.
Falls back to in-memory counters when Redis is unavailable.
"""

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from loguru import logger

from app.config import settings
from app.core.redis import redis_manager


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter.

    Limits:
      - Authenticated users: RATE_LIMIT_USER requests per window
      - Anonymous (by IP): RATE_LIMIT_IP requests per window
    """

    def __init__(self, app):
        super().__init__(app)
        # In-memory fallback: {key: [(timestamp, ...)]}
        self._local: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks and docs
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Determine rate limit key and limit
        user_id = getattr(request.state, "user_id", None) if hasattr(request, "state") else None
        if user_id:
            key = f"rl:user:{user_id}"
            limit = settings.rate_limit_user
        else:
            # Use IP for anonymous requests
            ip = request.client.host if request.client else "unknown"
            key = f"rl:ip:{ip}"
            limit = settings.rate_limit_ip

        window = settings.rate_limit_window

        # Check rate limit
        allowed, current, reset_at = await self._check_limit(key, limit, window)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": 429,
                        "message": "请求过于频繁，请稍后再试",
                        "retry_after": reset_at,
                    },
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(reset_at),
                },
            )

        # Proceed with request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, limit - current)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)

        return response

    async def _check_limit(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, int, int]:
        """Check if request is within rate limit.

        Returns: (allowed, current_count, reset_timestamp)
        """
        now = time.time()
        reset_at = int(now) + window

        if redis_manager.is_connected:
            return await self._check_redis(key, limit, window, now, reset_at)
        return self._check_local(key, limit, window, now, reset_at)

    async def _check_redis(
        self, key: str, limit: int, window: int, now: float, reset_at: int
    ) -> tuple[bool, int, int]:
        """Redis sliding window counter."""
        pipe = redis_manager.client.pipeline()
        window_start = now - window

        # Remove expired entries, add current, count, set expiry
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window + 1)

        results = await pipe.execute()
        current = results[2]

        if current > limit:
            # Over limit — remove the entry we just added
            await redis_manager.client.zrem(key, str(now))
            return False, current, reset_at

        return True, current, reset_at

    def _check_local(
        self, key: str, limit: int, window: int, now: float, reset_at: int
    ) -> tuple[bool, int, int]:
        """In-memory sliding window fallback."""
        window_start = now - window

        # Clean expired entries
        self._local[key] = [t for t in self._local[key] if t > window_start]

        current = len(self._local[key])
        if current >= limit:
            return False, current, reset_at

        self._local[key].append(now)
        return True, current + 1, reset_at
