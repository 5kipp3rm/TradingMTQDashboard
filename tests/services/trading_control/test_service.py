"""
Tests for TradingControlService (Service Layer)

Tests business logic and coordination between worker pool and checkers.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from src.services.trading_control.service import TradingControlService
from src.services.trading_control.models import (
    TradingStatus,
    TradingControlResult,
    AutoTradingStatus,
)
from src.workers.commands import ExecuteTradingCycleCommand


class TestTradingControlService:
    """Test TradingControlService"""

    def test_init(self):
        """Test service initialization"""
        mock_pool = Mock()
        mock_checker = Mock()

        service = TradingControlService(
            worker_pool=mock_pool, autotrading_checker=mock_checker
        )

        assert service.worker_pool is mock_pool
        assert service.autotrading_checker is mock_checker

    def test_start_trading_success(self):
        """Test starting trading successfully"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Mock AutoTrading check
        mock_checker.check_autotrading.return_value = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )

        # Mock trading cycle execution
        mock_pool.execute_command_on_account.return_value = {
            "success": True,
            "result": {"cycles_executed": 1},
        }

        service = TradingControlService(mock_pool, mock_checker)
        result = service.start_trading("account-001")

        assert result.success is True
        assert result.status == TradingStatus.ACTIVE
        assert result.account_id == "account-001"
        assert "started" in result.message.lower()
        mock_checker.check_autotrading.assert_called_once_with("account-001")

    def test_start_trading_with_currency_symbols(self):
        """Test starting trading with specific currency symbols"""
        mock_pool = Mock()
        mock_checker = Mock()

        mock_checker.check_autotrading.return_value = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )

        mock_pool.execute_command_on_account.return_value = {
            "success": True,
            "result": {"cycles_executed": 1},
        }

        service = TradingControlService(mock_pool, mock_checker)
        result = service.start_trading("account-001", currency_symbols=["EURUSD", "GBPUSD"])

        assert result.success is True
        # Verify command was called with currency symbols
        call_args = mock_pool.execute_command_on_account.call_args
        command = call_args[0][1]
        assert isinstance(command, ExecuteTradingCycleCommand)
        assert command.currency_symbols == ["EURUSD", "GBPUSD"]

    def test_start_trading_skip_autotrading_check(self):
        """Test starting trading without AutoTrading check"""
        mock_pool = Mock()
        mock_checker = Mock()

        mock_pool.execute_command_on_account.return_value = {
            "success": True,
            "result": {"cycles_executed": 1},
        }

        service = TradingControlService(mock_pool, mock_checker)
        result = service.start_trading("account-001", check_autotrading=False)

        assert result.success is True
        mock_checker.check_autotrading.assert_not_called()

    def test_start_trading_autotrading_disabled(self):
        """Test starting trading when AutoTrading is disabled"""
        mock_pool = Mock()
        mock_checker = Mock()

        # AutoTrading disabled
        mock_checker.check_autotrading.return_value = AutoTradingStatus(
            enabled=False,
            account_id="account-001",
            checked_at=datetime.utcnow(),
            instructions={"step1": "Enable AutoTrading"},
        )

        service = TradingControlService(mock_pool, mock_checker)
        result = service.start_trading("account-001")

        assert result.success is False
        assert result.status == TradingStatus.ERROR
        assert "AutoTrading" in result.message
        assert result.metadata is not None
        assert "instructions" in result.metadata
        mock_pool.execute_command_on_account.assert_not_called()

    def test_start_trading_worker_not_found(self):
        """Test starting trading when worker doesn't exist"""
        mock_pool = Mock()
        mock_checker = Mock()

        mock_checker.check_autotrading.return_value = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )

        # Worker not found
        mock_pool.execute_command_on_account.side_effect = ValueError(
            "No worker for account"
        )

        service = TradingControlService(mock_pool, mock_checker)
        result = service.start_trading("account-001")

        assert result.success is False
        assert result.status == TradingStatus.ERROR
        assert "worker" in result.message.lower() or "not found" in result.message.lower()

    def test_start_trading_command_failure(self):
        """Test starting trading when command execution fails"""
        mock_pool = Mock()
        mock_checker = Mock()

        mock_checker.check_autotrading.return_value = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )

        # Command fails
        mock_pool.execute_command_on_account.return_value = {
            "success": False,
            "error": "Connection timeout",
        }

        service = TradingControlService(mock_pool, mock_checker)
        result = service.start_trading("account-001")

        assert result.success is False
        assert result.status == TradingStatus.ERROR
        assert result.error is not None

    def test_stop_trading_success(self):
        """Test stopping trading successfully"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Mock worker exists check
        mock_pool.has_worker_for_account.return_value = True

        service = TradingControlService(mock_pool, mock_checker)
        result = service.stop_trading("account-001")

        assert result.success is True
        assert result.status == TradingStatus.STOPPED
        assert result.account_id == "account-001"
        assert "stopped" in result.message.lower()

    def test_stop_trading_worker_not_found(self):
        """Test stopping trading when worker doesn't exist"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Worker doesn't exist
        mock_pool.has_worker_for_account.return_value = False

        service = TradingControlService(mock_pool, mock_checker)
        result = service.stop_trading("account-001")

        assert result.success is False
        assert result.status == TradingStatus.UNKNOWN
        assert "worker" in result.message.lower() or "not found" in result.message.lower()

    def test_get_trading_status_active(self):
        """Test getting trading status when active"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Mock worker exists and is healthy
        mock_pool.has_worker_for_account.return_value = True
        mock_pool.get_worker_health.return_value = {"healthy": True, "connected": True}

        service = TradingControlService(mock_pool, mock_checker)
        result = service.get_trading_status("account-001")

        assert result.success is True
        assert result.status == TradingStatus.ACTIVE
        assert result.account_id == "account-001"

    def test_get_trading_status_stopped(self):
        """Test getting trading status when stopped"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Worker doesn't exist
        mock_pool.has_worker_for_account.return_value = False

        service = TradingControlService(mock_pool, mock_checker)
        result = service.get_trading_status("account-001")

        assert result.success is True
        assert result.status == TradingStatus.STOPPED
        assert result.account_id == "account-001"

    def test_get_trading_status_error(self):
        """Test getting trading status when in error state (worker not alive)"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Mock worker handle
        mock_handle = Mock()
        mock_handle.is_alive.return_value = False

        # Worker exists but not alive
        mock_pool.has_worker_for_account.return_value = True
        mock_pool.get_worker_by_account.return_value = mock_handle

        service = TradingControlService(mock_pool, mock_checker)
        result = service.get_trading_status("account-001")

        assert result.success is True
        assert result.status == TradingStatus.STOPPED
        assert "not running" in result.message.lower()

    def test_check_autotrading_success(self):
        """Test checking AutoTrading status"""
        mock_pool = Mock()
        mock_checker = Mock()

        expected_status = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )
        mock_checker.check_autotrading.return_value = expected_status

        service = TradingControlService(mock_pool, mock_checker)
        status = service.check_autotrading("account-001")

        assert status is expected_status
        mock_checker.check_autotrading.assert_called_once_with("account-001")

    def test_check_autotrading_worker_not_found(self):
        """Test checking AutoTrading when worker not found"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Checker raises ValueError
        mock_checker.check_autotrading.side_effect = ValueError("No worker found")

        service = TradingControlService(mock_pool, mock_checker)

        with pytest.raises(ValueError, match="No worker found"):
            service.check_autotrading("account-001")

    def test_check_autotrading_runtime_error(self):
        """Test checking AutoTrading when runtime error occurs"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Checker raises RuntimeError
        mock_checker.check_autotrading.side_effect = RuntimeError("Check failed")

        service = TradingControlService(mock_pool, mock_checker)

        with pytest.raises(RuntimeError, match="Check failed"):
            service.check_autotrading("account-001")

    def test_service_layer_coordination(self):
        """Test service coordinates worker pool and checker properly"""
        mock_pool = Mock()
        mock_checker = Mock()

        # Setup mocks
        mock_checker.check_autotrading.return_value = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )
        mock_pool.execute_command_on_account.return_value = {
            "success": True,
            "result": {"cycles_executed": 1},
        }

        service = TradingControlService(mock_pool, mock_checker)

        # Execute service method
        result = service.start_trading("account-001", currency_symbols=["EURUSD"])

        # Verify coordination: checker called first, then pool
        assert mock_checker.check_autotrading.call_count == 1
        assert mock_pool.execute_command_on_account.call_count == 1

        # Verify order (checker before pool)
        mock_checker_call = mock_checker.method_calls[0]
        mock_pool_call = mock_pool.method_calls[0]
        assert mock_checker_call < mock_pool_call

    def test_multiple_operations_sequence(self):
        """Test sequence of multiple trading operations"""
        mock_pool = Mock()
        mock_checker = Mock()

        mock_checker.check_autotrading.return_value = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )
        mock_pool.execute_command_on_account.return_value = {
            "success": True,
            "result": {},
        }
        mock_pool.has_worker_for_account.return_value = True

        service = TradingControlService(mock_pool, mock_checker)

        # 1. Start trading
        result1 = service.start_trading("account-001")
        assert result1.success is True
        assert result1.status == TradingStatus.ACTIVE

        # 2. Get status
        result2 = service.get_trading_status("account-001")
        assert result2.success is True

        # 3. Check AutoTrading
        status = service.check_autotrading("account-001")
        assert status.enabled is True

        # 4. Stop trading
        result3 = service.stop_trading("account-001")
        assert result3.success is True
        assert result3.status == TradingStatus.STOPPED
