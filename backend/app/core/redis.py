"""Redis connection management.

Provides a shared async Redis connection pool with lifecycle hooks
for startup/shutdown integration.
"""

import redis.asyncio as redis
from loguru import logger

from app.config import settings


class RedisManager:
    """Manages the async Redis connection pool."""

    def __init__(self):
        self._pool: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client. Raises if not connected."""
        if self._pool is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._pool

    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        self._pool = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
            socket_connect_timeout=5,
            socket_keepalive=True,
            retry_on_timeout=True,
        )
        # Verify connectivity
        try:
            await self._pool.ping()
            logger.info(f"Redis connected: {settings.redis_url}")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Falling back to in-memory mode.")
            await self._pool.aclose()
            self._pool = None

    async def disconnect(self) -> None:
        """Close the Redis connection pool."""
        if self._pool:
            await self._pool.aclose()
            self._pool = None
            logger.info("Redis disconnected")

    @property
    def is_connected(self) -> bool:
        """Check if Redis is available."""
        return self._pool is not None

    async def health_check(self) -> dict:
        """Return Redis health status."""
        if not self._pool:
            return {"status": "disconnected"}
        try:
            info = await self._pool.info("server")
            return {
                "status": "healthy",
                "version": info.get("redis_version", "unknown"),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Singleton
redis_manager = RedisManager()
