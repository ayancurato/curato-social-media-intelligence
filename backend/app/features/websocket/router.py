"""
Curato AI — WebSocket Router

WebSocket endpoint for real-time workflow updates.
"""

from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.features.websocket.manager import get_connection_manager

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: UUID) -> None:
    """
    WebSocket endpoint for real-time workflow updates.

    Clients connect with a session_id and receive events:
    - workflow_started
    - agent_started
    - agent_completed
    - agent_failed
    - revision_loop_started
    - workflow_completed
    - workflow_failed
    """
    manager = get_connection_manager()
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Keep connection alive — listen for client messages
            # (ping/pong is handled automatically by FastAPI)
            data = await websocket.receive_text()
            # Client can send "ping" to keep alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)
        logger.info("WebSocket client disconnected", session_id=str(session_id))
    except Exception as e:
        logger.error("WebSocket error", session_id=str(session_id), error=str(e))
        await manager.disconnect(websocket, session_id)
