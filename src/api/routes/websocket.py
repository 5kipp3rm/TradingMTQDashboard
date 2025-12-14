"""
WebSocket Endpoints

Real-time updates via WebSocket connections for live dashboard monitoring.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import asyncio
import json

from src.api.websocket import connection_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Optional client identifier")
):
    """
    WebSocket endpoint for real-time dashboard updates.

    Clients can connect to receive:
    - Trade events (opened, closed, modified)
    - Performance updates
    - System events
    - Heartbeat messages

    Args:
        websocket: WebSocket connection
        client_id: Optional client identifier for tracking
    """
    await connection_manager.connect(websocket, client_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                # Handle different message types from client
                if message_type == "ping":
                    # Respond to ping with pong
                    await connection_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, websocket)

                elif message_type == "subscribe":
                    # Handle subscription requests
                    channels = message.get("channels", [])
                    await connection_manager.send_personal_message({
                        "type": "subscribed",
                        "channels": channels
                    }, websocket)

                elif message_type == "unsubscribe":
                    # Handle unsubscribe requests
                    channels = message.get("channels", [])
                    await connection_manager.send_personal_message({
                        "type": "unsubscribed",
                        "channels": channels
                    }, websocket)

                elif message_type == "get_stats":
                    # Send connection manager stats
                    stats = connection_manager.get_stats()
                    await connection_manager.send_personal_message({
                        "type": "stats",
                        "data": stats
                    }, websocket)

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await connection_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        connection_manager.disconnect(websocket)


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        Connection manager statistics including active connections
    """
    return connection_manager.get_stats()
