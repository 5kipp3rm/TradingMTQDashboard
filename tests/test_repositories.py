"""
Unit Tests for Database Repositories

Tests repository methods with mocked sessions
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from src.database.repository import (
    TradeRepository, SignalRepository,
    AccountSnapshotRepository, DailyPerformanceRepository
)
from src.database.models import Trade, Signal, AccountSnapshot, DailyPerformance
from src.exceptions import DatabaseError


class TestTradeRepository:
    """Test TradeRepository"""

    def test_create_trade(self):
        """Test creating a trade"""
        repo = TradeRepository()
        session = Mock()

        # Mock session operations
        session.add = Mock()
        session.flush = Mock()

        trade = repo.create(
            session,
            ticket=123456,
            symbol="EURUSD",
            trade_type="BUY",
            status="OPEN",
            entry_price=Decimal("1.0850"),
            entry_time=datetime.now(),
            volume=Decimal("0.1")
        )

        # Verify session methods were called
        session.add.assert_called_once()
        session.flush.assert_called_once()

        # Verify trade was created
        assert isinstance(trade, Trade)

    def test_create_trade_with_error_handling(self):
        """Test trade creation with error"""
        repo = TradeRepository()
        session = Mock()

        # Mock session to raise error
        session.add.side_effect = Exception("Database error")

        with pytest.raises(DatabaseError) as exc_info:
            repo.create(
                session,
                ticket=123456,
                symbol="EURUSD",
                trade_type="BUY",
                status="OPEN",
                entry_price=Decimal("1.0850"),
                entry_time=datetime.now(),
                volume=Decimal("0.1")
            )

        assert "Database create failed" in str(exc_info.value)

    def test_get_by_ticket(self):
        """Test getting trade by ticket"""
        repo = TradeRepository()
        session = Mock()

        # Mock query chain
        mock_trade = Trade(
            ticket=123456,
            symbol="EURUSD",
            trade_type="BUY",
            status="OPEN",
            entry_price=Decimal("1.0850"),
            entry_time=datetime.now(),
            volume=Decimal("0.1")
        )

        session.query.return_value.filter.return_value.first.return_value = mock_trade

        trade = repo.get_by_ticket(session, 123456)

        assert trade == mock_trade
        session.query.assert_called_once()

    def test_get_trade_statistics_empty(self):
        """Test statistics with no trades"""
        repo = TradeRepository()
        session = Mock()

        # Mock empty query result
        session.query.return_value.filter.return_value.all.return_value = []

        stats = repo.get_trade_statistics(session)

        assert stats['total_trades'] == 0
        assert stats['win_rate'] == 0.0
        assert stats['total_profit'] == 0.0


class TestSignalRepository:
    """Test SignalRepository"""

    def test_create_signal(self):
        """Test creating a signal"""
        repo = SignalRepository()
        session = Mock()

        session.add = Mock()
        session.flush = Mock()

        signal = repo.create(
            session,
            symbol="EURUSD",
            signal_type="BUY",
            timestamp=datetime.now(),
            price=Decimal("1.0850"),
            confidence=0.85,
            strategy_name="TestStrategy",
            timeframe="M5"
        )

        session.add.assert_called_once()
        session.flush.assert_called_once()

        assert isinstance(signal, Signal)

    def test_mark_executed(self):
        """Test marking signal as executed"""
        repo = SignalRepository()
        session = Mock()

        mock_signal = Signal(
            symbol="EURUSD",
            signal_type="BUY",
            timestamp=datetime.now(),
            price=Decimal("1.0850"),
            confidence=0.85,
            strategy_name="TestStrategy",
            timeframe="M5"
        )

        session.query.return_value.filter.return_value.first.return_value = mock_signal
        session.flush = Mock()

        result = repo.mark_executed(session, 1, 100, "Test reason")

        assert result.executed is True
        assert result.trade_id == 100
        assert result.execution_reason == "Test reason"
        session.flush.assert_called_once()

    def test_mark_executed_not_found(self):
        """Test marking non-existent signal"""
        repo = SignalRepository()
        session = Mock()

        session.query.return_value.filter.return_value.first.return_value = None

        result = repo.mark_executed(session, 999, 100, "Test reason")

        assert result is None


class TestAccountSnapshotRepository:
    """Test AccountSnapshotRepository"""

    def test_create_snapshot(self):
        """Test creating account snapshot"""
        repo = AccountSnapshotRepository()
        session = Mock()

        session.add = Mock()
        session.flush = Mock()

        snapshot = repo.create(
            session,
            account_number=12345,
            server="TestServer",
            broker="TestBroker",
            balance=Decimal("10000.00"),
            equity=Decimal("10050.00"),
            profit=Decimal("50.00"),
            margin=Decimal("100.00"),
            margin_free=Decimal("9900.00"),
            open_positions=1,
            total_volume=Decimal("0.1"),
            snapshot_time=datetime.now()
        )

        session.add.assert_called_once()
        session.flush.assert_called_once()

        assert isinstance(snapshot, AccountSnapshot)

    def test_get_latest_snapshot(self):
        """Test getting latest snapshot"""
        repo = AccountSnapshotRepository()
        session = Mock()

        mock_snapshot = AccountSnapshot(
            account_number=12345,
            server="TestServer",
            broker="TestBroker",
            balance=Decimal("10000.00"),
            equity=Decimal("10050.00"),
            profit=Decimal("50.00"),
            margin=Decimal("100.00"),
            margin_free=Decimal("9900.00"),
            open_positions=1,
            total_volume=Decimal("0.1"),
            snapshot_time=datetime.now()
        )

        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_snapshot

        result = repo.get_latest_snapshot(session, 12345)

        assert result == mock_snapshot


class TestDailyPerformanceRepository:
    """Test DailyPerformanceRepository"""

    def test_create_or_update_new(self):
        """Test creating new daily performance"""
        repo = DailyPerformanceRepository()
        session = Mock()

        # Mock no existing record
        session.query.return_value.filter.return_value.first.return_value = None
        session.add = Mock()
        session.flush = Mock()

        today = date.today()
        perf = repo.create_or_update(
            session,
            target_date=today,
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            gross_profit=Decimal("500.00"),
            gross_loss=Decimal("150.00"),
            net_profit=Decimal("350.00")
        )

        session.add.assert_called_once()
        session.flush.assert_called_once()

        assert isinstance(perf, DailyPerformance)

    def test_create_or_update_existing(self):
        """Test updating existing daily performance"""
        repo = DailyPerformanceRepository()
        session = Mock()

        # Mock existing record
        today = date.today()
        existing_perf = DailyPerformance(
            date=datetime.combine(today, datetime.min.time()),
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            gross_profit=Decimal("200.00"),
            gross_loss=Decimal("100.00"),
            net_profit=Decimal("100.00")
        )

        session.query.return_value.filter.return_value.first.return_value = existing_perf
        session.flush = Mock()

        perf = repo.create_or_update(
            session,
            target_date=today,
            total_trades=10,
            net_profit=Decimal("350.00")
        )

        # Verify update
        assert perf.total_trades == 10
        assert perf.net_profit == Decimal("350.00")
        session.flush.assert_called_once()

    def test_get_by_date(self):
        """Test getting performance by date"""
        repo = DailyPerformanceRepository()
        session = Mock()

        today = date.today()
        mock_perf = DailyPerformance(
            date=datetime.combine(today, datetime.min.time()),
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            gross_profit=Decimal("500.00"),
            gross_loss=Decimal("150.00"),
            net_profit=Decimal("350.00")
        )

        session.query.return_value.filter.return_value.first.return_value = mock_perf

        result = repo.get_by_date(session, today)

        assert result == mock_perf

    def test_get_performance_summary_empty(self):
        """Test performance summary with no data"""
        repo = DailyPerformanceRepository()
        session = Mock()

        session.query.return_value.all.return_value = []

        summary = repo.get_performance_summary(session)

        assert summary == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
