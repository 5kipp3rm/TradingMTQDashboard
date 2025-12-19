"""
Integration Tests for Trading Control API Routes

Tests the FastAPI endpoints for trading control.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from src.api.app import create_app
from src.services.trading_control.models import (
    TradingStatus,
    TradingControlResult,
    AutoTradingStatus,
)


@pytest.fixture
def client():
    """Create FastAPI test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Create mock trading control service"""
    return Mock()


class TestStartTradingEndpoint:
    """Test POST /api/accounts/{id}/trading/start"""

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_start_trading_success(self, mock_get_service, client, mock_service):
        """Test successful trading start"""
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.start_trading.return_value = TradingControlResult(
            success=True,
            message="Trading started successfully",
            account_id="account-001",
            status=TradingStatus.ACTIVE,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        # Make request
        response = client.post(
            "/api/accounts/account-001/trading/start",
            json={"currency_symbols": ["EURUSD", "GBPUSD"]},
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "active"
        assert data["account_id"] == "account-001"
        assert "started" in data["message"].lower()

        # Verify service was called correctly
        mock_service.start_trading.assert_called_once_with(
            account_id="account-001",
            currency_symbols=["EURUSD", "GBPUSD"],
            check_autotrading=True,
        )

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_start_trading_without_currency_symbols(
        self, mock_get_service, client, mock_service
    ):
        """Test starting trading without specifying currencies"""
        mock_get_service.return_value = mock_service
        mock_service.start_trading.return_value = TradingControlResult(
            success=True,
            message="Trading started",
            account_id="account-001",
            status=TradingStatus.ACTIVE,
            timestamp=datetime.utcnow(),
        )

        response = client.post("/api/accounts/account-001/trading/start", json={})

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify None was passed for currency_symbols
        call_args = mock_service.start_trading.call_args
        assert call_args[1]["currency_symbols"] is None

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_start_trading_autotrading_disabled(
        self, mock_get_service, client, mock_service
    ):
        """Test starting trading when AutoTrading is disabled"""
        mock_get_service.return_value = mock_service
        mock_service.start_trading.return_value = TradingControlResult(
            success=False,
            message="AutoTrading is not enabled",
            account_id="account-001",
            status=TradingStatus.ERROR,
            timestamp=datetime.utcnow(),
            error="AutoTrading disabled",
            metadata={"instructions": {"step1": "Enable AutoTrading"}},
        )

        response = client.post("/api/accounts/account-001/trading/start", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "error"
        assert "AutoTrading" in data["message"]
        assert data["error"] == "AutoTrading disabled"
        assert "instructions" in data["metadata"]

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_start_trading_service_exception(self, mock_get_service, client, mock_service):
        """Test error handling when service raises exception"""
        mock_get_service.return_value = mock_service
        mock_service.start_trading.side_effect = Exception("Connection lost")

        response = client.post("/api/accounts/account-001/trading/start", json={})

        assert response.status_code == 500
        assert "Failed to start trading" in response.json()["detail"]


class TestStopTradingEndpoint:
    """Test POST /api/accounts/{id}/trading/stop"""

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_stop_trading_success(self, mock_get_service, client, mock_service):
        """Test successful trading stop"""
        mock_get_service.return_value = mock_service
        mock_service.stop_trading.return_value = TradingControlResult(
            success=True,
            message="Trading stopped successfully",
            account_id="account-001",
            status=TradingStatus.STOPPED,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )

        response = client.post("/api/accounts/account-001/trading/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "stopped"
        assert data["account_id"] == "account-001"
        assert "stopped" in data["message"].lower()

        mock_service.stop_trading.assert_called_once_with(account_id="account-001")

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_stop_trading_worker_not_found(self, mock_get_service, client, mock_service):
        """Test stopping trading when worker not found"""
        mock_get_service.return_value = mock_service
        mock_service.stop_trading.return_value = TradingControlResult(
            success=False,
            message="No worker found for account",
            account_id="account-001",
            status=TradingStatus.UNKNOWN,
            timestamp=datetime.utcnow(),
            error="Account not connected",
        )

        response = client.post("/api/accounts/account-001/trading/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Account not connected"

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_stop_trading_service_exception(self, mock_get_service, client, mock_service):
        """Test error handling when service raises exception"""
        mock_get_service.return_value = mock_service
        mock_service.stop_trading.side_effect = Exception("Worker crashed")

        response = client.post("/api/accounts/account-001/trading/stop")

        assert response.status_code == 500
        assert "Failed to stop trading" in response.json()["detail"]


class TestGetTradingStatusEndpoint:
    """Test GET /api/accounts/{id}/trading/status"""

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_get_status_active(self, mock_get_service, client, mock_service):
        """Test getting active trading status"""
        mock_get_service.return_value = mock_service
        mock_service.get_trading_status.return_value = TradingControlResult(
            success=True,
            message="Trading is active",
            account_id="account-001",
            status=TradingStatus.ACTIVE,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            metadata={"worker_id": "worker-123"},
        )

        response = client.get("/api/accounts/account-001/trading/status")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "active"
        assert data["metadata"]["worker_id"] == "worker-123"

        mock_service.get_trading_status.assert_called_once_with(account_id="account-001")

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_get_status_stopped(self, mock_get_service, client, mock_service):
        """Test getting stopped trading status"""
        mock_get_service.return_value = mock_service
        mock_service.get_trading_status.return_value = TradingControlResult(
            success=True,
            message="Account not connected",
            account_id="account-001",
            status=TradingStatus.STOPPED,
            timestamp=datetime.utcnow(),
        )

        response = client.get("/api/accounts/account-001/trading/status")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "stopped"

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_get_status_service_exception(self, mock_get_service, client, mock_service):
        """Test error handling when service raises exception"""
        mock_get_service.return_value = mock_service
        mock_service.get_trading_status.side_effect = Exception("Database error")

        response = client.get("/api/accounts/account-001/trading/status")

        assert response.status_code == 500
        assert "Failed to get trading status" in response.json()["detail"]


class TestCheckAutoTradingStatusEndpoint:
    """Test GET /api/accounts/{id}/autotrading/status"""

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_check_autotrading_enabled(self, mock_get_service, client, mock_service):
        """Test checking AutoTrading when enabled"""
        mock_get_service.return_value = mock_service
        mock_service.check_autotrading.return_value = AutoTradingStatus(
            enabled=True,
            account_id="account-001",
            checked_at=datetime(2025, 1, 1, 12, 0, 0),
        )

        response = client.get("/api/accounts/account-001/autotrading/status")

        assert response.status_code == 200
        data = response.json()
        assert data["autotrading_enabled"] is True
        assert data["account_id"] == "account-001"
        assert data["checked_at"] == "2025-01-01T12:00:00"

        mock_service.check_autotrading.assert_called_once_with(account_id="account-001")

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_check_autotrading_disabled_with_instructions(
        self, mock_get_service, client, mock_service
    ):
        """Test checking AutoTrading when disabled with instructions"""
        mock_get_service.return_value = mock_service
        mock_service.check_autotrading.return_value = AutoTradingStatus(
            enabled=False,
            account_id="account-001",
            checked_at=datetime.utcnow(),
            instructions={
                "step1": "Open MetaTrader 5 terminal",
                "step2": "Click AutoTrading button",
                "step3": "Enable Algo Trading in Options",
            },
        )

        response = client.get("/api/accounts/account-001/autotrading/status")

        assert response.status_code == 200
        data = response.json()
        assert data["autotrading_enabled"] is False
        assert "instructions" in data
        assert len(data["instructions"]) == 3
        assert "MetaTrader" in data["instructions"]["step1"]

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_check_autotrading_account_not_found(
        self, mock_get_service, client, mock_service
    ):
        """Test checking AutoTrading when account not found"""
        mock_get_service.return_value = mock_service
        mock_service.check_autotrading.side_effect = ValueError(
            "No worker found for account account-001"
        )

        response = client.get("/api/accounts/account-001/autotrading/status")

        assert response.status_code == 404
        assert "No worker found" in response.json()["detail"]

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_check_autotrading_runtime_error(self, mock_get_service, client, mock_service):
        """Test checking AutoTrading when runtime error occurs"""
        mock_get_service.return_value = mock_service
        mock_service.check_autotrading.side_effect = RuntimeError("Check failed")

        response = client.get("/api/accounts/account-001/autotrading/status")

        assert response.status_code == 500
        assert "Failed to check AutoTrading status" in response.json()["detail"]


class TestAPIResponseFormats:
    """Test API response format consistency"""

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_trading_control_response_format(self, mock_get_service, client, mock_service):
        """Test TradingControlResponse format matches expected structure"""
        mock_get_service.return_value = mock_service
        mock_service.start_trading.return_value = TradingControlResult(
            success=True,
            message="Trading started",
            account_id="account-001",
            status=TradingStatus.ACTIVE,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            metadata={"cycles": 1},
        )

        response = client.post("/api/accounts/account-001/trading/start", json={})

        data = response.json()
        # Verify all required fields present
        assert "success" in data
        assert "message" in data
        assert "account_id" in data
        assert "status" in data
        assert "timestamp" in data
        assert "error" in data
        assert "metadata" in data

        # Verify types
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        assert isinstance(data["account_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["metadata"], dict)

    @patch("src.api.routes.trading_control.get_trading_control_service")
    def test_autotrading_status_response_format(
        self, mock_get_service, client, mock_service
    ):
        """Test AutoTradingStatusResponse format matches expected structure"""
        mock_get_service.return_value = mock_service
        mock_service.check_autotrading.return_value = AutoTradingStatus(
            enabled=False,
            account_id="account-001",
            checked_at=datetime(2025, 1, 1, 12, 0, 0),
            instructions={"step1": "Enable AutoTrading"},
        )

        response = client.get("/api/accounts/account-001/autotrading/status")

        data = response.json()
        # Verify required fields present
        assert "autotrading_enabled" in data
        assert "account_id" in data
        assert "checked_at" in data
        assert "instructions" in data

        # Verify types
        assert isinstance(data["autotrading_enabled"], bool)
        assert isinstance(data["account_id"], str)
        assert isinstance(data["checked_at"], str)
        assert isinstance(data["instructions"], dict)
