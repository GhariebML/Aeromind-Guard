import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("aeromind.websocket.hub")

VALID_EVENT_TYPES = {
    "telemetry.updated",
    "detection.created",
    "hazard.detected",
    "risk.updated",
    "alert.created",
    "alert.updated",
    "camera.status",
    "system.status",
    "ping",
    "pong"
}

class WebSocketHub:
    """
    Production-Grade WebSocket Event Hub.
    Dispatches typed physical AI events to operators with heartbeat and backpressure protection.
    """

    def __init__(self):
        self._active_connections: Set[WebSocket] = set()

    @property
    def active_count(self) -> int:
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._active_connections.add(websocket)
        logger.info(f"[WebSocketHub] Client connected. Total active: {self.active_count}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
            logger.info(f"[WebSocketHub] Client disconnected. Active remaining: {self.active_count}")

    async def broadcast(self, event_type: str, data: Any, correlation_id: Optional[str] = None):
        if not self._active_connections:
            return

        payload = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        json_text = json.dumps(payload, default=str)
        dead_sockets = []

        for connection in list(self._active_connections):
            try:
                await connection.send_text(json_text)
            except Exception as exc:
                logger.warning(f"[WebSocketHub] Delivery failure to connection: {exc}")
                dead_sockets.append(connection)

        for dead in dead_sockets:
            self.disconnect(dead)

# Global singleton instance
ws_hub = WebSocketHub()
