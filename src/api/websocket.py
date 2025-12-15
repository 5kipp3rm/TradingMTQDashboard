"""
WebSocket Connection Manager

Manages WebSocket connections and broadcasts real-time updates to connected clients.
"""

from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages to all connected clients.
    """

    def __init__(self):
        # List of active WebSocket connections
        self.active_connections: List[WebSocket] = []
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self._broadcast_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            client_id: Optional client identifier
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "client_id": client_id or f"client_{id(websocket)}",
            "connected_at": datetime.utcnow().isoformat(),
            "messages_sent": 0
        }

        logger.info(
            f"WebSocket connected: {self.connection_metadata[websocket]['client_id']} "
            f"(Total connections: {len(self.active_connections)})"
        )

        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "client_id": self.connection_metadata[websocket]["client_id"],
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            client_id = self.connection_metadata.get(websocket, {}).get("client_id", "unknown")
            self.active_connections.remove(websocket)
            del self.connection_metadata[websocket]

            logger.info(
                f"WebSocket disconnected: {client_id} "
                f"(Total connections: {len(self.active_connections)})"
            )

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send a message to a specific client.

        Args:
            message: Message dict to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)

            # Update message counter
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["messages_sent"] += 1

        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any], exclude: WebSocket = None):
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message dict to broadcast
            exclude: Optional WebSocket to exclude from broadcast
        """
        async with self._broadcast_lock:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            disconnected = []

            for connection in self.active_connections:
                if connection == exclude:
                    continue

                try:
                    await connection.send_json(message)

                    # Update message counter
                    if connection in self.connection_metadata:
                        self.connection_metadata[connection]["messages_sent"] += 1

                except WebSocketDisconnect:
                    disconnected.append(connection)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection)

            if message.get("type") != "heartbeat":  # Don't log heartbeats
                logger.debug(f"Broadcast message type '{message.get('type')}' to {len(self.active_connections)} clients")

    async def broadcast_trade_event(self, event_type: str, trade_data: Dict[str, Any]):
        """
        Broadcast a trade-related event.

        Args:
            event_type: Type of event (trade_opened, trade_closed, etc.)
            trade_data: Trade data to broadcast
        """
        message = {
            "type": "trade_event",
            "event": event_type,
            "data": trade_data
        }
        await self.broadcast(message)

    async def broadcast_performance_update(self, performance_data: Dict[str, Any]):
        """
        Broadcast performance metrics update.

        Args:
            performance_data: Performance metrics to broadcast
        """
        message = {
            "type": "performance_update",
            "data": performance_data
        }
        await self.broadcast(message)

    async def broadcast_system_event(self, event_type: str, data: Dict[str, Any] = None):
        """
        Broadcast a system event.

        Args:
            event_type: Type of system event
            data: Optional event data
        """
        message = {
            "type": "system_event",
            "event": event_type,
            "data": data or {}
        }
        await self.broadcast(message)

    async def broadcast_currency_event(self, event_type: str, currency_data: Dict[str, Any]):
        """
        Broadcast a currency configuration event.

        Args:
            event_type: Type of event (created, updated, deleted, enabled, disabled, reloaded)
            currency_data: Currency configuration data
        """
        message = {
            "type": "currency_event",
            "event": event_type,
            "data": currency_data
        }
        await self.broadcast(message)
        logger.info(f"Broadcast currency event: {event_type} for {currency_data.get('symbol', 'unknown')}")

    async def heartbeat_loop(self):
        """
        Send periodic heartbeat messages to keep connections alive.
        """
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds

                if self.active_connections:
                    await self.broadcast({
                        "type": "heartbeat",
                        "connections": len(self.active_connections)
                    })

            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection manager statistics.

        Returns:
            Dict containing connection stats
        """
        total_messages = sum(
            meta.get("messages_sent", 0)
            for meta in self.connection_metadata.values()
        )

        return {
            "active_connections": len(self.active_connections),
            "total_messages_sent": total_messages,
            "connections": [
                {
                    "client_id": meta["client_id"],
                    "connected_at": meta["connected_at"],
                    "messages_sent": meta["messages_sent"]
                }
                for meta in self.connection_metadata.values()
            ]
        }


# Global connection manager instance
connection_manager = ConnectionManager()
