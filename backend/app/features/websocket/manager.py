"""
Curato AI — WebSocket Connection Manager

Manages WebSocket connections and broadcasts real-time events
to clients watching specific generation sessions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections per session.

    Clients subscribe to a specific session_id and receive
    real-time events about that workflow's progress.
    """

    def __init__(self) -> None:
        # Map session_id → list of connected WebSocket clients
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: UUID) -> None:
        """Accept a new WebSocket connection for a session."""
        await websocket.accept()
        key = str(session_id)
        if key not in self._connections:
            self._connections[key] = []
        self._connections[key].append(websocket)
        logger.info(
            "WebSocket connected",
            session_id=key,
            total_connections=len(self._connections[key]),
        )

    async def disconnect(self, websocket: WebSocket, session_id: UUID) -> None:
        """Remove a WebSocket connection."""
        key = str(session_id)
        if key in self._connections:
            self._connections[key] = [
                ws for ws in self._connections[key] if ws != websocket
            ]
            if not self._connections[key]:
                del self._connections[key]
        logger.info("WebSocket disconnected", session_id=key)

    async def broadcast_to_session(
        self,
        session_id: UUID,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """Broadcast an event to all clients watching a specific session."""
        key = str(session_id)
        connections = self._connections.get(key, [])

        if not connections:
            return

        message = json.dumps({
            "event_type": event_type,
            "session_id": key,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, default=str)

        disconnected: list[WebSocket] = []

        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(ws, session_id)

    async def broadcast_global(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """Broadcast to ALL connected clients across all sessions."""
        message = json.dumps({
            "event_type": event_type,
            "session_id": None,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, default=str)

        for key, connections in list(self._connections.items()):
            for websocket in connections:
                try:
                    await websocket.send_text(message)
                except Exception:
                    pass

    @property
    def active_connections_count(self) -> int:
        """Total number of active WebSocket connections."""
        return sum(len(conns) for conns in self._connections.values())


# ── Singleton ────────────────────────────────────────────────────────────────
_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the singleton ConnectionManager."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
