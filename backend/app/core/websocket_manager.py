"""
WebSocket connection manager for real-time event broadcasting.
"""

import json
from typing import Any, Dict, List

from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, data: Dict[str, Any]):
        """Broadcast JSON data to all connected clients."""
        message = json.dumps(data, default=str)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_bytes(self, data: bytes):
        """Broadcast binary data (e.g., video frames) to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_bytes(data)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Global singleton instances
event_manager = ConnectionManager()
video_manager = ConnectionManager()
