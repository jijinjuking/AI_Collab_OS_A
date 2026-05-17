"""Cache service — Redis-backed with in-memory fallback.

Provides a simple key-value cache with TTL support.
Falls back to a TTL dict when Redis is unavailable.
"""

import json
import time
from typing import Any

from loguru import logger

from app.core.redis import redis_manager


class CacheService:
    """Application cache layer with Redis backend + in-memory fallback."""

    def __init__(self):
        # In-memory fallback: {key: (value, expire_at)}
        self._local: dict[str, tuple[str, float]] = {}

    @property
    def _use_redis(self) -> bool:
        return redis_manager.is_connected

    async def get(self, key: str) -> Any | None:
        """Get a cached value. Returns None if missing or expired."""
        if self._use_redis:
            raw = await redis_manager.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)

        # Fallback: local dict
        entry = self._local.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if expire_at and time.time() > expire_at:
            del self._local[key]
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a cached value with TTL (seconds). Default 5 minutes."""
        raw = json.dumps(value, ensure_ascii=False)

        if self._use_redis:
            await redis_manager.client.setex(key, ttl, raw)
            return

        # Fallback: local dict
        expire_at = time.time() + ttl if ttl > 0 else 0
        self._local[key] = (raw, expire_at)

    async def delete(self, key: str) -> None:
        """Delete a cached key."""
        if self._use_redis:
            await redis_manager.client.delete(key)
            return

        self._local.pop(key, None)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern (e.g. 'project:*'). Returns count deleted."""
        if self._use_redis:
            count = 0
            async for key in redis_manager.client.scan_iter(match=pattern, count=100):
                await redis_manager.client.delete(key)
                count += 1
            return count

        # Fallback: local dict
        import fnmatch
        to_delete = [k for k in self._local if fnmatch.fnmatch(k, pattern)]
        for k in to_delete:
            del self._local[k]
        return len(to_delete)

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        if self._use_redis:
            return bool(await redis_manager.client.exists(key))

        entry = self._local.get(key)
        if entry is None:
            return False
        _, expire_at = entry
        if expire_at and time.time() > expire_at:
            del self._local[key]
            return False
        return True

    async def incr(self, key: str, ttl: int = 60) -> int:
        """Increment a counter. Creates with value 1 if missing. Returns new value."""
        if self._use_redis:
            pipe = redis_manager.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = await pipe.execute()
            return results[0]

        # Fallback: local
        entry = self._local.get(key)
        if entry is None or (entry[1] and time.time() > entry[1]):
            val = 1
        else:
            val = json.loads(entry[0]) + 1
        expire_at = time.time() + ttl
        self._local[key] = (json.dumps(val), expire_at)
        return val

    def _cleanup_expired(self) -> None:
        """Remove expired entries from local cache (call periodically)."""
        now = time.time()
        expired = [k for k, (_, exp) in self._local.items() if exp and now > exp]
        for k in expired:
            del self._local[k]


# Singleton
cache = CacheService()
