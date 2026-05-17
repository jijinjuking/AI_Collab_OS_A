"""WebSocket connection manager.

Manages per-project rooms. Each connected client joins a project room
and receives real-time agent messages, status updates, and workflow events.
"""

import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """In-memory WebSocket connection manager (single-process dev mode).

    For production with multiple workers, layer Redis Pub/Sub on top
    via the EventBus class in events.py.
    """

    def __init__(self):
        # project_id -> set of active WebSocket connections
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        # websocket -> (user_id, project_id)
        self._connections: dict[WebSocket, tuple[str, str]] = {}

    async def connect(self, ws: WebSocket, user_id: str, project_id: str) -> None:
        """Accept connection and join project room."""
        await ws.accept()
        self._rooms[project_id].add(ws)
        self._connections[ws] = (user_id, project_id)
        logger.info(f"WS connected: user={user_id} project={project_id}")

        # Notify room
        await self.broadcast(project_id, {
            "type": "user_joined",
            "user_id": user_id,
            "online_count": len(self._rooms[project_id]),
        })

    async def disconnect(self, ws: WebSocket) -> None:
        """Remove connection from room."""
        info = self._connections.pop(ws, None)
        if info:
            user_id, project_id = info
            self._rooms[project_id].discard(ws)
            if not self._rooms[project_id]:
                del self._rooms[project_id]
            else:
                await self.broadcast(project_id, {
                    "type": "user_left",
                    "user_id": user_id,
                    "online_count": len(self._rooms.get(project_id, set())),
                })
            logger.info(f"WS disconnected: user={user_id} project={project_id}")

    async def broadcast(self, project_id: str, message: dict[str, Any]) -> None:
        """Send message to all connections in a project room."""
        room = self._rooms.get(project_id)
        if not room:
            return

        payload = json.dumps(message, ensure_ascii=False)
        dead: list[WebSocket] = []

        for ws in room:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            await self.disconnect(ws)

    async def send_personal(self, ws: WebSocket, message: dict[str, Any]) -> None:
        """Send message to a specific connection."""
        try:
            await ws.send_text(json.dumps(message, ensure_ascii=False))
        except Exception:
            await self.disconnect(ws)

    def get_room_count(self, project_id: str) -> int:
        """Get number of connections in a project room."""
        return len(self._rooms.get(project_id, set()))

    def get_all_rooms(self) -> dict[str, int]:
        """Get all active rooms and their connection counts."""
        return {pid: len(conns) for pid, conns in self._rooms.items()}


# Singleton instance
ws_manager = ConnectionManager()
