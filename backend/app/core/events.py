"""Event bus for cross-service communication.

In dev mode (single process): uses in-memory pub/sub via local WebSocket manager.
In production (multi-worker): uses Redis Pub/Sub for cross-process messaging.
"""

import json
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from loguru import logger

from app.core.pubsub import redis_pubsub

# Event handler type
EventHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class EventBus:
    """Application event bus. Publishes events to WebSocket rooms and local subscribers."""

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)

    async def publish(self, project_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event: broadcast to WebSocket room + invoke local handlers.

        Uses Redis pub/sub when available (multi-worker), falls back to direct
        local broadcast (single-worker).
        """
        message = {
            "type": event_type,
            "project_id": project_id,
            **data,
        }

        # Broadcast via Redis pub/sub (or direct local if Redis unavailable)
        await redis_pubsub.publish(project_id, message)

        # Invoke local handlers
        for handler in self._handlers.get(event_type, []):
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Event handler error: {event_type} -> {e}")

    async def publish_agent_message(
        self,
        project_id: str,
        from_agent: str | None,
        to_agent: str | None,
        message_type: str,
        content: str,
        **extra: Any,
    ) -> None:
        """Convenience: publish an agent message event."""
        await self.publish(project_id, "agent_message", {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "content": content,
            **extra,
        })

    async def publish_agent_status(
        self, project_id: str, agent_id: str, status: str
    ) -> None:
        """Convenience: publish agent status change."""
        await self.publish(project_id, "agent_status", {
            "agent_id": agent_id,
            "status": status,
        })

    async def publish_workflow_event(
        self, project_id: str, workflow_id: str, event: str, **extra: Any
    ) -> None:
        """Convenience: publish workflow lifecycle event."""
        await self.publish(project_id, "workflow_event", {
            "workflow_id": workflow_id,
            "event": event,
            **extra,
        })


# Singleton
event_bus = EventBus()
