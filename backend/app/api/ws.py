"""WebSocket endpoint for real-time project communication."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_access_token
from app.core.websocket import ws_manager

router = APIRouter()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
    token: str = Query(...),
):
    """WebSocket connection for a project room.

    Client connects with: ws://host/ws/{project_id}?token=<jwt>
    Server sends JSON messages for all project events.
    """
    # Authenticate via JWT token in query param
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="无效的认证令牌")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="无效的认证令牌")
        return

    # Connect and join room
    await ws_manager.connect(websocket, user_id, project_id)

    try:
        while True:
            # Keep connection alive, handle client messages
            data = await websocket.receive_json()
            # Client can send ping or other control messages
            msg_type = data.get("type")

            if msg_type == "ping":
                await ws_manager.send_personal(websocket, {"type": "pong"})
            # Future: handle client-initiated events here

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
