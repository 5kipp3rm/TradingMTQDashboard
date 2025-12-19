"""
Tests for AutoTrading Checkers (Strategy and Decorator Patterns)

Tests both WorkerBasedAutoTradingChecker and CachedAutoTradingChecker.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from src.services.trading_control.checker import (
    WorkerBasedAutoTradingChecker,
    CachedAutoTradingChecker,
)
from src.services.trading_control.models import AutoTradingStatus


class TestWorkerBasedAutoTradingChecker:
    """Test WorkerBasedAutoTradingChecker (Strategy Pattern)"""

    def test_init(self):
        """Test checker initialization"""
        mock_pool = Mock()
        checker = WorkerBasedAutoTradingChecker(mock_pool)

        assert checker.worker_pool is mock_pool

    def test_check_autotrading_worker_not_found(self):
        """Test checking when worker doesn't exist"""
        mock_pool = Mock()
        mock_pool.has_worker_for_account.return_value = False

        checker = WorkerBasedAutoTradingChecker(mock_pool)

        with pytest.raises(ValueError, match="No worker found for account account-001"):
            checker.check_autotrading("account-001")

        mock_pool.has_worker_for_account.assert_called_once_with("account-001")

    def test_check_autotrading_enabled(self):
        """Test checking when AutoTrading is enabled"""
        mock_pool = Mock()
        mock_pool.has_worker_for_account.return_value = True
        mock_pool.execute_command_on_account.return_value = {
            "success": True,
            "result": {"healthy": True},
        }

        checker = WorkerBasedAutoTradingChecker(mock_pool)
        status = checker.check_autotrading("account-001")

        assert status.enabled is True
        assert status.account_id == "account-001"
        assert isinstance(status.checked_at, datetime)
        assert status.error is None

    def test_check_autotrading_disabled(self):
        """Test checking when AutoTrading is disabled"""
        mock_pool = Mock()
        mock_pool.has_worker_for_account.return_value = True
        mock_pool.execute_command_on_account.return_value = {
            "success": True,
            "result": {"healthy": False},
        }

        checker = WorkerBasedAutoTradingChecker(mock_pool)
        status = checker.check_autotrading("account-001")

        assert status.enabled is False
        assert status.account_id == "account-001"
        assert status.instructions is not None
        assert len(status.instructions) >= 3

    def test_check_autotrading_command_failure(self):
        """Test checking when health check fails"""
        mock_pool = Mock()
        mock_pool.has_worker_for_account.return_value = True
        mock_pool.execute_command_on_account.return_value = {
            "success": False,
            "error": "Worker timeout",
        }

        checker = WorkerBasedAutoTradingChecker(mock_pool)
        status = checker.check_autotrading("account-001")

        assert status.enabled is False
        assert status.error == "Worker timeout"
        assert status.instructions is not None

    def test_check_autotrading_exception(self):
        """Test checking when exception occurs"""
        mock_pool = Mock()
        mock_pool.has_worker_for_account.return_value = True
        mock_pool.execute_command_on_account.side_effect = Exception("Connection lost")

        checker = WorkerBasedAutoTradingChecker(mock_pool)

        with pytest.raises(RuntimeError, match="AutoTrading check failed"):
            checker.check_autotrading("account-001")


class TestCachedAutoTradingChecker:
    """Test CachedAutoTradingChecker (Decorator Pattern)"""

    def test_init(self):
        """Test decorator initialization"""
        mock_base = Mock()
        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=60)

        assert checker.base_checker is mock_base
        assert checker.cache_ttl == timedelta(seconds=60)
        assert len(checker._cache) == 0

    def test_check_autotrading_cache_miss(self):
        """Test checking with cache miss"""
        mock_base = Mock()
        expected_status = AutoTradingStatus(
            enabled=True,
            account_id="account-001",
            checked_at=datetime.utcnow(),
        )
        mock_base.check_autotrading.return_value = expected_status

        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=30)
        status = checker.check_autotrading("account-001")

        assert status is expected_status
        mock_base.check_autotrading.assert_called_once_with("account-001")
        assert "account-001" in checker._cache

    def test_check_autotrading_cache_hit(self):
        """Test checking with cache hit"""
        mock_base = Mock()
        cached_status = AutoTradingStatus(
            enabled=True,
            account_id="account-001",
            checked_at=datetime.utcnow(),
        )

        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=30)
        checker._cache["account-001"] = (cached_status, datetime.utcnow())

        status = checker.check_autotrading("account-001")

        assert status is cached_status
        mock_base.check_autotrading.assert_not_called()

    def test_check_autotrading_cache_expired(self):
        """Test checking with expired cache"""
        mock_base = Mock()
        old_status = AutoTradingStatus(
            enabled=True,
            account_id="account-001",
            checked_at=datetime.utcnow() - timedelta(seconds=100),
        )
        new_status = AutoTradingStatus(
            enabled=False,
            account_id="account-001",
            checked_at=datetime.utcnow(),
        )
        mock_base.check_autotrading.return_value = new_status

        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=30)
        # Add expired entry
        checker._cache["account-001"] = (old_status, datetime.utcnow() - timedelta(seconds=60))

        status = checker.check_autotrading("account-001")

        assert status is new_status
        mock_base.check_autotrading.assert_called_once_with("account-001")

    def test_check_autotrading_multiple_accounts(self):
        """Test caching for multiple accounts"""
        mock_base = Mock()
        status1 = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )
        status2 = AutoTradingStatus(
            enabled=False, account_id="account-002", checked_at=datetime.utcnow()
        )
        mock_base.check_autotrading.side_effect = [status1, status2]

        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=30)

        # First calls - cache misses
        result1 = checker.check_autotrading("account-001")
        result2 = checker.check_autotrading("account-002")

        assert result1 is status1
        assert result2 is status2
        assert len(checker._cache) == 2

        # Second calls - cache hits
        result1_cached = checker.check_autotrading("account-001")
        result2_cached = checker.check_autotrading("account-002")

        assert result1_cached is status1
        assert result2_cached is status2
        assert mock_base.check_autotrading.call_count == 2

    def test_clear_cache_single_account(self):
        """Test clearing cache for single account"""
        mock_base = Mock()
        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=30)

        # Add cache entries
        checker._cache["account-001"] = (Mock(), datetime.utcnow())
        checker._cache["account-002"] = (Mock(), datetime.utcnow())

        checker.clear_cache("account-001")

        assert "account-001" not in checker._cache
        assert "account-002" in checker._cache

    def test_clear_cache_all_accounts(self):
        """Test clearing cache for all accounts"""
        mock_base = Mock()
        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=30)

        # Add cache entries
        checker._cache["account-001"] = (Mock(), datetime.utcnow())
        checker._cache["account-002"] = (Mock(), datetime.utcnow())

        checker.clear_cache()

        assert len(checker._cache) == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        mock_base = Mock()
        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=45)

        # Add cache entries
        checker._cache["account-001"] = (Mock(), datetime.utcnow())
        checker._cache["account-002"] = (Mock(), datetime.utcnow())

        stats = checker.get_cache_stats()

        assert stats["cached_accounts"] == 2
        assert stats["ttl_seconds"] == 45

    def test_decorator_wraps_base_checker_interface(self):
        """Test decorator properly wraps base checker"""
        mock_base = Mock()
        mock_base.check_autotrading.return_value = AutoTradingStatus(
            enabled=True, account_id="account-001", checked_at=datetime.utcnow()
        )

        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=30)

        # Decorator should have same interface as base
        assert hasattr(checker, "check_autotrading")

        # Should forward to base checker
        status = checker.check_autotrading("account-001")
        assert status.enabled is True

    def test_exception_propagation(self):
        """Test exceptions from base checker propagate"""
        mock_base = Mock()
        mock_base.check_autotrading.side_effect = ValueError("Account not found")

        checker = CachedAutoTradingChecker(mock_base, cache_ttl_seconds=30)

        with pytest.raises(ValueError, match="Account not found"):
            checker.check_autotrading("account-001")
