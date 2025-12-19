"""
Tests for Trading Control Models (Value Objects)

Tests immutable value objects and their behavior.
"""

import pytest
from datetime import datetime
from dataclasses import FrozenInstanceError

from src.services.trading_control.models import (
    TradingStatus,
    TradingControlResult,
    AutoTradingStatus,
)


class TestTradingStatus:
    """Test TradingStatus enum"""

    def test_enum_values(self):
        """Test all enum values exist"""
        assert TradingStatus.ACTIVE == "active"
        assert TradingStatus.STOPPED == "stopped"
        assert TradingStatus.STARTING == "starting"
        assert TradingStatus.ERROR == "error"


class TestTradingControlResult:
    """Test TradingControlResult value object"""

    def test_create_success_result(self):
        """Test creating successful result"""
        timestamp = datetime.utcnow()
        result = TradingControlResult(
            success=True,
            message="Trading started",
            account_id="account-001",
            status=TradingStatus.ACTIVE,
            timestamp=timestamp,
        )

        assert result.success is True
        assert result.message == "Trading started"
        assert result.account_id == "account-001"
        assert result.status == TradingStatus.ACTIVE
        assert result.timestamp == timestamp
        assert result.error is None
        assert result.metadata is None

    def test_create_error_result(self):
        """Test creating error result"""
        timestamp = datetime.utcnow()
        result = TradingControlResult(
            success=False,
            message="Trading failed",
            account_id="account-001",
            status=TradingStatus.ERROR,
            timestamp=timestamp,
            error="Worker not found",
            metadata={"details": "No worker for account"},
        )

        assert result.success is False
        assert result.error == "Worker not found"
        assert result.metadata == {"details": "No worker for account"}

    def test_immutable(self):
        """Test value object is immutable"""
        result = TradingControlResult(
            success=True,
            message="Trading started",
            account_id="account-001",
            status=TradingStatus.ACTIVE,
            timestamp=datetime.utcnow(),
        )

        with pytest.raises(FrozenInstanceError):
            result.success = False

    def test_to_dict(self):
        """Test conversion to dictionary"""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        result = TradingControlResult(
            success=True,
            message="Trading started",
            account_id="account-001",
            status=TradingStatus.ACTIVE,
            timestamp=timestamp,
            metadata={"cycles": 1},
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["message"] == "Trading started"
        assert data["account_id"] == "account-001"
        assert data["status"] == "active"
        assert data["timestamp"] == "2025-01-01T12:00:00"
        assert data["error"] is None
        assert data["metadata"] == {"cycles": 1}


class TestAutoTradingStatus:
    """Test AutoTradingStatus value object"""

    def test_create_enabled_status(self):
        """Test creating enabled status"""
        checked_at = datetime.utcnow()
        status = AutoTradingStatus(
            enabled=True,
            account_id="account-001",
            checked_at=checked_at,
        )

        assert status.enabled is True
        assert status.account_id == "account-001"
        assert status.checked_at == checked_at
        assert status.instructions is None
        assert status.error is None

    def test_create_disabled_status_with_instructions(self):
        """Test creating disabled status with instructions"""
        checked_at = datetime.utcnow()
        instructions = {
            "step1": "Open MT5 terminal",
            "step2": "Click AutoTrading button",
        }
        status = AutoTradingStatus(
            enabled=False,
            account_id="account-001",
            checked_at=checked_at,
            instructions=instructions,
        )

        assert status.enabled is False
        assert status.instructions == instructions

    def test_create_error_status(self):
        """Test creating error status"""
        status = AutoTradingStatus(
            enabled=False,
            account_id="account-001",
            checked_at=datetime.utcnow(),
            error="Worker not responding",
        )

        assert status.enabled is False
        assert status.error == "Worker not responding"

    def test_immutable(self):
        """Test value object is immutable"""
        status = AutoTradingStatus(
            enabled=True,
            account_id="account-001",
            checked_at=datetime.utcnow(),
        )

        with pytest.raises(FrozenInstanceError):
            status.enabled = False

    def test_to_dict(self):
        """Test conversion to dictionary"""
        checked_at = datetime(2025, 1, 1, 12, 0, 0)
        instructions = {"step1": "Enable AutoTrading"}
        status = AutoTradingStatus(
            enabled=False,
            account_id="account-001",
            checked_at=checked_at,
            instructions=instructions,
            error=None,
        )

        data = status.to_dict()

        assert data["autotrading_enabled"] is False
        assert data["account_id"] == "account-001"
        assert data["checked_at"] == "2025-01-01T12:00:00"
        assert data["instructions"] == instructions
        # Error key not included when None
        assert "error" not in data

    def test_get_enable_instructions(self):
        """Test getting enable instructions"""
        instructions = AutoTradingStatus.get_enable_instructions()

        assert isinstance(instructions, dict)
        assert len(instructions) >= 3
        assert "step1" in instructions
        assert "step2" in instructions
        assert "step3" in instructions
        assert "MT5" in instructions["step1"] or "terminal" in instructions["step1"].lower()
