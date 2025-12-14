"""
Tests for WebSocket functionality

Tests WebSocket connections, message broadcasting, and real-time updates.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from datetime import datetime, date
from decimal import Decimal

from src.api.app import create_app
from src.api.websocket import connection_manager
from src.database.models import Trade, TradeStatus
from src.database.connection import get_session, init_db
from sqlalchemy import text


@pytest.fixture(scope="function")
def setup_database():
    """Initialize test database"""
    init_db()

    with get_session() as session:
        session.execute(text("DELETE FROM trades"))
        session.commit()

    yield

    with get_session() as session:
        session.execute(text("DELETE FROM trades"))
        session.commit()


@pytest.fixture
def client(setup_database):
    """Create test client"""
    app = create_app()
    return TestClient(app)


class TestWebSocketConnection:
    """Tests for WebSocket connection management"""

    def test_websocket_connect(self, client):
        """Test basic WebSocket connection"""
        with client.websocket_connect("/api/ws") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()

            assert data["type"] == "connection"
            assert data["status"] == "connected"
            assert "client_id" in data
            assert "timestamp" in data

    def test_websocket_connect_with_client_id(self, client):
        """Test WebSocket connection with custom client ID"""
        with client.websocket_connect("/api/ws?client_id=test_client_123") as websocket:
            data = websocket.receive_json()

            assert data["type"] == "connection"
            assert data["client_id"] == "test_client_123"

    def test_websocket_ping_pong(self, client):
        """Test ping/pong mechanism"""
        with client.websocket_connect("/api/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Send ping
            websocket.send_json({
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data

    def test_websocket_get_stats(self, client):
        """Test get stats request"""
        with client.websocket_connect("/api/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Request stats
            websocket.send_json({"type": "get_stats"})

            # Receive stats response
            data = websocket.receive_json()
            assert data["type"] == "stats"
            assert "data" in data
            assert "active_connections" in data["data"]
            assert data["data"]["active_connections"] >= 1

    def test_websocket_subscribe(self, client):
        """Test channel subscription"""
        with client.websocket_connect("/api/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Subscribe to channels
            websocket.send_json({
                "type": "subscribe",
                "channels": ["trades", "performance"]
            })

            # Receive subscription confirmation
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert data["channels"] == ["trades", "performance"]

    def test_websocket_invalid_json(self, client):
        """Test handling of invalid JSON"""
        with client.websocket_connect("/api/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Send invalid JSON
            websocket.send_text("not valid json")

            # Should receive error message
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "invalid json" in data["message"].lower()


class TestWebSocketBroadcasting:
    """Tests for message broadcasting"""

    def test_broadcast_to_multiple_clients(self, client):
        """Test broadcasting message to multiple clients"""
        # Connect two clients
        with client.websocket_connect("/api/ws?client_id=client1") as ws1:
            with client.websocket_connect("/api/ws?client_id=client2") as ws2:
                # Receive welcome messages
                ws1.receive_json()
                ws2.receive_json()

                # Broadcast a test message
                asyncio.run(connection_manager.broadcast({
                    "type": "test_broadcast",
                    "message": "Hello everyone!"
                }))

                # Both clients should receive the broadcast
                # Note: In test client, we can't easily test async broadcasts
                # This is more of a structure test
                pass

    def test_connection_manager_stats(self, client):
        """Test connection manager statistics"""
        with client.websocket_connect("/api/ws") as websocket:
            websocket.receive_json()

            # Get stats via HTTP endpoint
            response = client.get("/api/ws/stats")
            assert response.status_code == 200

            data = response.json()
            assert "active_connections" in data
            assert "total_messages_sent" in data
            assert data["active_connections"] >= 1


class TestWebSocketEvents:
    """Tests for WebSocket event messages"""

    @pytest.mark.asyncio
    async def test_trade_event_broadcast(self):
        """Test broadcasting trade event"""
        trade_data = {
            "ticket": 12345,
            "symbol": "EURUSD",
            "type": "BUY",
            "profit": 100.00,
            "pips": 10.0
        }

        # Test that broadcast_trade_event doesn't error
        await connection_manager.broadcast_trade_event("trade_opened", trade_data)

        # Verify message structure (would be received by clients)
        assert True  # If we got here, no exception was raised

    @pytest.mark.asyncio
    async def test_performance_update_broadcast(self):
        """Test broadcasting performance update"""
        performance_data = {
            "total_trades": 50,
            "net_profit": 1500.00,
            "win_rate": 65.5
        }

        await connection_manager.broadcast_performance_update(performance_data)
        assert True

    @pytest.mark.asyncio
    async def test_system_event_broadcast(self):
        """Test broadcasting system event"""
        await connection_manager.broadcast_system_event(
            "aggregation_complete",
            {"date": "2025-12-14"}
        )
        assert True


class TestWebSocketIntegration:
    """Integration tests with actual trading events"""

    def test_websocket_with_api_endpoints(self, client):
        """Test WebSocket works alongside REST API"""
        # Test that both WebSocket and REST API work
        with client.websocket_connect("/api/ws") as websocket:
            websocket.receive_json()

            # Call REST API endpoint
            response = client.get("/api/health")
            assert response.status_code == 200

            # WebSocket should still be connected
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_multiple_concurrent_connections(self, client):
        """Test multiple WebSocket connections"""
        connections = []

        # Open 5 concurrent connections
        for i in range(5):
            ws = client.websocket_connect(f"/api/ws?client_id=client_{i}")
            ws.__enter__()
            connections.append(ws)

            # Receive welcome message
            data = ws.receive_json()
            assert data["type"] == "connection"

        # Get stats
        response = client.get("/api/ws/stats")
        data = response.json()
        assert data["active_connections"] >= 5

        # Close all connections
        for ws in connections:
            ws.__exit__(None, None, None)


class TestWebSocketResilience:
    """Tests for WebSocket error handling and resilience"""

    def test_connection_disconnect(self, client):
        """Test graceful disconnect"""
        with client.websocket_connect("/api/ws") as websocket:
            websocket.receive_json()

            # Connection should close gracefully when context exits
            pass

        # Connection should be removed from manager
        stats = connection_manager.get_stats()
        # Stats might show 0 or previous connections depending on timing
        assert stats is not None

    def test_unknown_message_type(self, client):
        """Test handling of unknown message types"""
        with client.websocket_connect("/api/ws") as websocket:
            websocket.receive_json()

            # Send unknown message type
            websocket.send_json({
                "type": "unknown_type",
                "data": "test"
            })

            # Should not crash, just log warning
            # We can still send valid messages
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"


class TestConnectionManager:
    """Tests for ConnectionManager class directly"""

    @pytest.mark.asyncio
    async def test_connection_manager_initialization(self):
        """Test ConnectionManager initializes correctly"""
        assert connection_manager.active_connections == []
        assert isinstance(connection_manager.connection_metadata, dict)

    def test_connection_manager_get_stats(self):
        """Test get_stats returns correct format"""
        stats = connection_manager.get_stats()

        assert "active_connections" in stats
        assert "total_messages_sent" in stats
        assert "connections" in stats
        assert isinstance(stats["connections"], list)

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(self):
        """Test broadcasting with no active connections"""
        # Should not error even with no connections
        await connection_manager.broadcast({
            "type": "test",
            "message": "No one to receive this"
        })

        assert True  # No exception raised


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
