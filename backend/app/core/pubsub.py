"""Distributed WebSocket pub/sub via Redis.

When running multiple uvicorn workers, WebSocket connections are local to each
process. This module uses Redis Pub/Sub to relay broadcast messages across all
workers so every connected client receives events regardless of which worker
they're attached to.
"""

import asyncio
import json
from typing import Any

from loguru import logger

from app.core.redis import redis_manager
from app.core.websocket import ws_manager

# Redis channel prefix for project rooms
CHANNEL_PREFIX = "ws:project:"


class RedisPubSub:
    """Redis-backed pub/sub for cross-worker WebSocket broadcasting."""

    def __init__(self):
        self._subscriber = None
        self._listen_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the Redis subscriber listener."""
        if not redis_manager.is_connected:
            logger.info("Redis unavailable — WebSocket pub/sub disabled (single-worker mode)")
            return

        self._subscriber = redis_manager.client.pubsub()
        # Subscribe to all project channels via pattern
        await self._subscriber.psubscribe(f"{CHANNEL_PREFIX}*")
        self._listen_task = asyncio.create_task(self._listen())
        logger.info("Redis WebSocket pub/sub started")

    async def stop(self) -> None:
        """Stop the subscriber listener."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        if self._subscriber:
            await self._subscriber.punsubscribe()
            await self._subscriber.aclose()
            self._subscriber = None
            logger.info("Redis WebSocket pub/sub stopped")

    async def publish(self, project_id: str, message: dict[str, Any]) -> None:
        """Publish a message to a project channel.

        All workers subscribed to this channel will relay it to their local
        WebSocket connections.
        """
        if not redis_manager.is_connected:
            # Fallback: direct local broadcast (single-worker)
            await ws_manager.broadcast(project_id, message)
            return

        channel = f"{CHANNEL_PREFIX}{project_id}"
        payload = json.dumps(message, ensure_ascii=False)
        await redis_manager.client.publish(channel, payload)

    async def _listen(self) -> None:
        """Background task: listen for Redis pub/sub messages and relay to local WS."""
        try:
            async for raw_message in self._subscriber.listen():
                if raw_message["type"] != "pmessage":
                    continue

                channel: str = raw_message["channel"]
                project_id = channel.removeprefix(CHANNEL_PREFIX)
                data = raw_message["data"]

                try:
                    message = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    continue

                # Relay to local WebSocket connections in this worker
                await ws_manager.broadcast(project_id, message)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Redis pub/sub listener error: {e}")
            # Auto-restart after brief delay
            await asyncio.sleep(2)
            if redis_manager.is_connected:
                self._listen_task = asyncio.create_task(self._listen())


# Singleton
redis_pubsub = RedisPubSub()
