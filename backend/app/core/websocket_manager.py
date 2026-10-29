import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time communication."""

    def __init__(self):
        # channel -> set of websockets
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._user_map: Dict[WebSocket, str] = {}
        self._background_tasks: List[asyncio.Task] = []

    def start_background_tasks(self, loop: asyncio.AbstractEventLoop):
        """Start background heartbeat and cleanup tasks."""
        task = loop.create_task(self._heartbeat())
        self._background_tasks.append(task)

    async def _heartbeat(self):
        """Send periodic heartbeat to all connections."""
        while True:
            await asyncio.sleep(30)
            dead = []
            for channel, sockets in self._connections.items():
                for ws in list(sockets):
                    try:
                        await ws.send_json({"type": "heartbeat", "ts": datetime.now(timezone.utc).isoformat()})
                    except Exception:
                        dead.append((channel, ws))
            for channel, ws in dead:
                await self.disconnect(ws, channel)

    async def connect(self, websocket: WebSocket, channel: str, user_email: str):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if channel not in self._connections:
            self._connections[channel] = set()
        self._connections[channel].add(websocket)
        self._user_map[websocket] = user_email
        logger.info(f"WS connected: {user_email} on channel {channel}")

        await websocket.send_json({
            "type": "connected",
            "channel": channel,
            "user": user_email,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

    async def disconnect(self, websocket: WebSocket, channel: str):
        """Remove a WebSocket connection."""
        if channel in self._connections:
            self._connections[channel].discard(websocket)
        self._user_map.pop(websocket, None)

    async def broadcast(self, channel: str, message: dict):
        """Broadcast a message to all connections on a channel."""
        if channel not in self._connections:
            return
        dead = []
        for ws in list(self._connections[channel]):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws, channel)

    async def broadcast_all(self, message: dict):
        """Broadcast to all channels."""
        for channel in list(self._connections.keys()):
            await self.broadcast(channel, message)

    def active_connections_count(self) -> int:
        return sum(len(v) for v in self._connections.values())


ws_manager = WebSocketManager()
