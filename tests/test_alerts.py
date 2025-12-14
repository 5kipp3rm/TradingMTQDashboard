"""
Tests for Alert and Notification System

Tests alert configuration, email notifications, and delivery tracking.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.api.app import create_app
from src.database.models import AlertConfiguration, AlertHistory, AlertType, NotificationChannel
from src.database.connection import get_session, init_db
from src.notifications.email_service import EmailConfig, EmailNotificationService
from src.notifications.alert_manager import AlertManager
from sqlalchemy import text


@pytest.fixture(scope="function")
def setup_database():
    """Initialize test database"""
    init_db()

    with get_session() as session:
        session.execute(text("DELETE FROM alert_history"))
        session.execute(text("DELETE FROM alert_configurations"))
        session.commit()

    yield

    with get_session() as session:
        session.execute(text("DELETE FROM alert_history"))
        session.execute(text("DELETE FROM alert_configurations"))
        session.commit()


@pytest.fixture
def client(setup_database):
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def email_service():
    """Create mock email service"""
    config = EmailConfig(
        smtp_host="smtp.test.com",
        smtp_port=587,
        username="test@test.com",
        password="testpass",
        from_email="test@test.com"
    )
    service = EmailNotificationService(config)
    service.enabled = False  # Disable actual sending in tests
    return service


@pytest.fixture
def alert_manager(email_service):
    """Create alert manager with mock email service"""
    return AlertManager(email_service)


# =============================================================================
# API Tests - Alert Configuration
# =============================================================================

class TestAlertConfigAPI:
    """Tests for alert configuration API endpoints"""

    def test_get_alert_types(self, client):
        """Test getting available alert types"""
        response = client.get("/api/alerts/types")
        assert response.status_code == 200

        data = response.json()
        assert "alert_types" in data
        assert "notification_channels" in data
        assert "trade_opened" in data["alert_types"]
        assert "email" in data["notification_channels"]

    def test_create_alert_configuration(self, client):
        """Test creating new alert configuration"""
        config_data = {
            "alert_type": "trade_opened",
            "enabled": True,
            "email_enabled": True,
            "sms_enabled": False,
            "websocket_enabled": True,
            "email_recipients": "test1@example.com, test2@example.com",
            "profit_threshold": None,
            "loss_threshold": None,
            "symbol_filter": "EURUSD, GBPUSD"
        }

        response = client.post("/api/alerts/config", json=config_data)
        assert response.status_code == 201

        data = response.json()
        assert data["alert_type"] == "trade_opened"
        assert data["enabled"] is True
        assert len(data["email_recipients"]) == 2
        assert len(data["symbol_filter"]) == 2

    def test_get_alert_configurations(self, client):
        """Test getting all alert configurations"""
        # Create a configuration first
        config_data = {
            "alert_type": "trade_closed",
            "enabled": True,
            "email_enabled": True,
            "email_recipients": "test@example.com"
        }
        client.post("/api/alerts/config", json=config_data)

        # Get all configurations
        response = client.get("/api/alerts/config")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_specific_alert_configuration(self, client):
        """Test getting specific alert configuration"""
        # Create configuration
        config_data = {
            "alert_type": "daily_summary",
            "enabled": True,
            "email_enabled": True,
            "email_recipients": "test@example.com"
        }
        client.post("/api/alerts/config", json=config_data)

        # Get specific configuration
        response = client.get("/api/alerts/config/daily_summary")
        assert response.status_code == 200

        data = response.json()
        assert data["alert_type"] == "daily_summary"

    def test_update_alert_configuration(self, client):
        """Test updating alert configuration"""
        # Create configuration
        config_data = {
            "alert_type": "error_alert",
            "enabled": True,
            "email_enabled": True,
            "email_recipients": "old@example.com"
        }
        client.post("/api/alerts/config", json=config_data)

        # Update configuration
        updated_data = {
            **config_data,
            "email_recipients": "new@example.com",
            "enabled": False
        }
        response = client.put("/api/alerts/config/error_alert", json=updated_data)
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is False
        assert "new@example.com" in data["email_recipients"]

    def test_delete_alert_configuration(self, client):
        """Test deleting alert configuration"""
        # Create configuration
        config_data = {
            "alert_type": "profit_threshold",
            "enabled": True,
            "email_enabled": True,
            "email_recipients": "test@example.com",
            "profit_threshold": 100.0
        }
        client.post("/api/alerts/config", json=config_data)

        # Delete configuration
        response = client.delete("/api/alerts/config/profit_threshold")
        assert response.status_code == 204

        # Verify deletion
        response = client.get("/api/alerts/config/profit_threshold")
        assert response.status_code == 404

    def test_create_duplicate_configuration(self, client):
        """Test creating duplicate configuration fails"""
        config_data = {
            "alert_type": "trade_opened",
            "enabled": True,
            "email_enabled": True,
            "email_recipients": "test@example.com"
        }

        # Create first configuration
        response = client.post("/api/alerts/config", json=config_data)
        assert response.status_code == 201

        # Try to create duplicate
        response = client.post("/api/alerts/config", json=config_data)
        assert response.status_code == 409  # Conflict

    def test_invalid_alert_type(self, client):
        """Test invalid alert type returns error"""
        config_data = {
            "alert_type": "invalid_type",
            "enabled": True,
            "email_enabled": True,
            "email_recipients": "test@example.com"
        }

        response = client.post("/api/alerts/config", json=config_data)
        assert response.status_code == 400


# =============================================================================
# Email Service Tests
# =============================================================================

class TestEmailService:
    """Tests for email notification service"""

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_service):
        """Test successful email sending"""
        email_service.enabled = True

        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Send email
        success = email_service.send_email(
            to_emails=["test@example.com"],
            subject="Test Email",
            body_html="<p>Test</p>",
            body_text="Test"
        )

        assert success is True
        mock_server.sendmail.assert_called_once()

    def test_notify_trade_opened(self, email_service):
        """Test trade opened notification"""
        trade_data = {
            "symbol": "EURUSD",
            "trade_type": "BUY",
            "entry_price": 1.12345,
            "volume": 0.1,
            "stop_loss": 1.12000,
            "take_profit": 1.13000
        }

        with patch.object(email_service, 'send_email', return_value=True) as mock_send:
            success = email_service.notify_trade_opened(["test@example.com"], trade_data)

            assert success is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "EURUSD" in call_args[1]['subject']

    def test_notify_trade_closed(self, email_service):
        """Test trade closed notification"""
        trade_data = {
            "symbol": "GBPUSD",
            "trade_type": "SELL",
            "entry_price": 1.25000,
            "exit_price": 1.24500,
            "profit": 50.00,
            "pips": 50.0
        }

        with patch.object(email_service, 'send_email', return_value=True) as mock_send:
            success = email_service.notify_trade_closed(["test@example.com"], trade_data)

            assert success is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "GBPUSD" in call_args[1]['subject']
            assert "$50.00" in call_args[1]['subject']

    def test_notify_daily_summary(self, email_service):
        """Test daily summary notification"""
        performance_data = {
            "total_trades": 10,
            "winning_trades": 6,
            "losing_trades": 4,
            "net_profit": 150.00,
            "win_rate": 60.0
        }

        with patch.object(email_service, 'send_email', return_value=True) as mock_send:
            success = email_service.notify_daily_summary(["test@example.com"], performance_data)

            assert success is True
            mock_send.assert_called_once()

    def test_notify_error(self, email_service):
        """Test error notification"""
        with patch.object(email_service, 'send_email', return_value=True) as mock_send:
            success = email_service.notify_error(
                ["test@example.com"],
                "Test error message",
                {"context": "test"}
            )

            assert success is True
            mock_send.assert_called_once()


# =============================================================================
# Alert Manager Tests
# =============================================================================

class TestAlertManager:
    """Tests for alert manager"""

    def test_send_trade_opened_alert(self, alert_manager, setup_database):
        """Test sending trade opened alert"""
        # Create configuration
        with get_session() as session:
            config = AlertConfiguration(
                alert_type=AlertType.TRADE_OPENED,
                enabled=True,
                email_enabled=True,
                websocket_enabled=False,
                email_recipients="test@example.com"
            )
            session.add(config)
            session.commit()

        trade_data = {
            "symbol": "EURUSD",
            "trade_type": "BUY",
            "entry_price": 1.12345,
            "volume": 0.1
        }

        with patch.object(alert_manager.email_service, 'notify_trade_opened', return_value=True):
            success = alert_manager.send_trade_opened_alert(trade_data, trade_id=1)
            assert success is True

        # Verify history was recorded
        with get_session() as session:
            history = session.query(AlertHistory).filter(
                AlertHistory.alert_type == AlertType.TRADE_OPENED
            ).all()
            assert len(history) > 0

    def test_send_trade_closed_alert(self, alert_manager, setup_database):
        """Test sending trade closed alert"""
        # Create configuration
        with get_session() as session:
            config = AlertConfiguration(
                alert_type=AlertType.TRADE_CLOSED,
                enabled=True,
                email_enabled=True,
                websocket_enabled=False,
                email_recipients="test@example.com"
            )
            session.add(config)
            session.commit()

        trade_data = {
            "symbol": "GBPUSD",
            "trade_type": "SELL",
            "profit": 50.00,
            "pips": 50.0
        }

        with patch.object(alert_manager.email_service, 'notify_trade_closed', return_value=True):
            success = alert_manager.send_trade_closed_alert(trade_data, trade_id=1)
            assert success is True

    def test_symbol_filter(self, alert_manager, setup_database):
        """Test symbol filtering"""
        # Create configuration with symbol filter
        with get_session() as session:
            config = AlertConfiguration(
                alert_type=AlertType.TRADE_OPENED,
                enabled=True,
                email_enabled=True,
                websocket_enabled=False,
                email_recipients="test@example.com",
                symbol_filter="EURUSD,GBPUSD"
            )
            session.add(config)
            session.commit()

        # Test with filtered symbol (should send)
        trade_data_allowed = {"symbol": "EURUSD", "trade_type": "BUY"}
        with patch.object(alert_manager.email_service, 'notify_trade_opened', return_value=True):
            success = alert_manager.send_trade_opened_alert(trade_data_allowed)
            assert success is True

        # Test with non-filtered symbol (should not send)
        trade_data_blocked = {"symbol": "USDJPY", "trade_type": "BUY"}
        with patch.object(alert_manager.email_service, 'notify_trade_opened', return_value=True):
            success = alert_manager.send_trade_opened_alert(trade_data_blocked)
            assert success is False

    def test_disabled_alert(self, alert_manager, setup_database):
        """Test disabled alert is not sent"""
        # Create disabled configuration
        with get_session() as session:
            config = AlertConfiguration(
                alert_type=AlertType.TRADE_OPENED,
                enabled=False,
                email_enabled=True,
                email_recipients="test@example.com"
            )
            session.add(config)
            session.commit()

        trade_data = {"symbol": "EURUSD", "trade_type": "BUY"}

        with patch.object(alert_manager.email_service, 'notify_trade_opened', return_value=True) as mock_notify:
            success = alert_manager.send_trade_opened_alert(trade_data)
            assert success is False
            mock_notify.assert_not_called()


# =============================================================================
# Alert History Tests
# =============================================================================

class TestAlertHistory:
    """Tests for alert delivery history"""

    def test_get_alert_history(self, client, setup_database):
        """Test getting alert history"""
        # Create some history records
        with get_session() as session:
            for i in range(5):
                history = AlertHistory(
                    alert_type=AlertType.TRADE_OPENED,
                    channel=NotificationChannel.EMAIL,
                    success=True,
                    recipient=f"test{i}@example.com",
                    subject="Test Alert"
                )
                session.add(history)
            session.commit()

        # Get history
        response = client.get("/api/alerts/history")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_get_alert_history_with_filters(self, client, setup_database):
        """Test getting alert history with filters"""
        # Create mixed history records
        with get_session() as session:
            for i in range(3):
                history = AlertHistory(
                    alert_type=AlertType.TRADE_OPENED,
                    channel=NotificationChannel.EMAIL,
                    success=True,
                    recipient="test@example.com"
                )
                session.add(history)

            for i in range(2):
                history = AlertHistory(
                    alert_type=AlertType.TRADE_CLOSED,
                    channel=NotificationChannel.EMAIL,
                    success=False,
                    recipient="test@example.com",
                    error_message="Test error"
                )
                session.add(history)
            session.commit()

        # Filter by alert type
        response = client.get("/api/alerts/history?alert_type=trade_opened")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Filter by success only
        response = client.get("/api/alerts/history?success_only=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
