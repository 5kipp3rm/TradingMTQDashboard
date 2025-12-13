"""
Tests for Analytics Module - Daily Aggregation

Tests the DailyAggregator class for calculating daily performance metrics.
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import text

from src.analytics.daily_aggregator import DailyAggregator
from src.database.models import Trade, TradeStatus, DailyPerformance
from src.database.repository import TradeRepository, DailyPerformanceRepository
from src.database.connection import get_session, init_db


@pytest.fixture(scope="function")
def setup_database():
    """Initialize test database before each test"""
    init_db()

    # Clean up any existing data before test
    with get_session() as session:
        session.execute(text("DELETE FROM daily_performance"))
        session.execute(text("DELETE FROM trades"))
        session.commit()

    yield

    # Cleanup after test
    with get_session() as session:
        session.execute(text("DELETE FROM daily_performance"))
        session.execute(text("DELETE FROM trades"))
        session.commit()


@pytest.fixture
def sample_trades():
    """Create sample trade data for testing"""
    base_time = datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc)

    trades = [
        # Winning trade 1
        Trade(
            ticket=1001,
            symbol="EURUSD",
            trade_type="BUY",
            volume=Decimal("1.0"),
            entry_price=Decimal("1.1000"),
            exit_price=Decimal("1.1050"),
            entry_time=base_time,
            exit_time=base_time + timedelta(hours=1),
            profit=Decimal("500.00"),
            pips=Decimal("50.0"),
            status=TradeStatus.CLOSED
        ),
        # Winning trade 2
        Trade(
            ticket=1002,
            symbol="GBPUSD",
            trade_type="BUY",
            volume=Decimal("0.5"),
            entry_price=Decimal("1.2500"),
            exit_price=Decimal("1.2600"),
            entry_time=base_time + timedelta(hours=2),
            exit_time=base_time + timedelta(hours=3),
            profit=Decimal("300.00"),
            pips=Decimal("100.0"),
            status=TradeStatus.CLOSED
        ),
        # Losing trade
        Trade(
            ticket=1003,
            symbol="USDJPY",
            trade_type="SELL",
            volume=Decimal("1.0"),
            entry_price=Decimal("110.00"),
            exit_price=Decimal("110.50"),
            entry_time=base_time + timedelta(hours=4),
            exit_time=base_time + timedelta(hours=5),
            profit=Decimal("-200.00"),
            pips=Decimal("-50.0"),
            status=TradeStatus.CLOSED
        ),
        # Breakeven trade
        Trade(
            ticket=1004,
            symbol="AUDUSD",
            trade_type="BUY",
            volume=Decimal("0.5"),
            entry_price=Decimal("0.7500"),
            exit_price=Decimal("0.7500"),
            entry_time=base_time + timedelta(hours=6),
            exit_time=base_time + timedelta(hours=7),
            profit=Decimal("0.00"),
            pips=Decimal("0.0"),
            status=TradeStatus.CLOSED
        ),
    ]

    return trades


class TestDailyAggregator:
    """Tests for DailyAggregator class"""

    def test_aggregate_day_with_trades(self, setup_database, sample_trades):
        """Test aggregation of a day with trades"""
        # Arrange
        with get_session() as session:
            for trade in sample_trades:
                session.add(trade)
            session.commit()

        aggregator = DailyAggregator()
        target_date = date(2025, 12, 13)

        # Act
        result = aggregator.aggregate_day(target_date)

        # Assert
        assert result is not None
        assert result.total_trades == 4
        assert result.winning_trades == 2
        assert result.losing_trades == 1
        assert result.net_profit == Decimal("600.00")  # 500 + 300 - 200 + 0
        assert result.gross_profit == Decimal("800.00")  # 500 + 300
        assert result.gross_loss == Decimal("200.00")
        assert result.win_rate == Decimal("50.0")  # 2/4 * 100
        assert result.profit_factor == Decimal("4.0")  # 800/200

    def test_aggregate_day_no_trades(self, setup_database):
        """Test aggregation of a day with no trades"""
        # Arrange
        aggregator = DailyAggregator()
        target_date = date(2025, 12, 13)

        # Act
        result = aggregator.aggregate_day(target_date)

        # Assert
        assert result is None

    def test_calculate_metrics(self, setup_database, sample_trades):
        """Test metric calculation logic"""
        # Arrange
        aggregator = DailyAggregator()
        target_date = date(2025, 12, 13)

        # Act
        metrics = aggregator._calculate_metrics(sample_trades, target_date)

        # Assert
        assert metrics["total_trades"] == 4
        assert metrics["winning_trades"] == 2
        assert metrics["losing_trades"] == 1
        assert metrics["net_profit"] == Decimal("600.00")
        assert metrics["gross_profit"] == Decimal("800.00")
        assert metrics["gross_loss"] == Decimal("200.00")
        assert metrics["win_rate"] == Decimal("50.0")
        assert metrics["profit_factor"] == Decimal("4.0")
        assert metrics["average_win"] == Decimal("400.00")  # 800/2
        assert metrics["average_loss"] == Decimal("200.00")  # 200/1
        assert metrics["largest_win"] == Decimal("500.00")
        assert metrics["largest_loss"] == Decimal("-200.00")

    def test_max_consecutive_wins(self, setup_database):
        """Test calculation of maximum consecutive wins"""
        # Arrange
        base_time = datetime(2025, 12, 14, 10, 0, 0, tzinfo=timezone.utc)  # Use different date
        trades = [
            Trade(ticket=5001, symbol="EURUSD", trade_type="BUY", volume=Decimal("1.0"),
                  entry_price=Decimal("1.1000"), entry_time=base_time,
                  exit_price=Decimal("1.1100"), exit_time=base_time + timedelta(hours=1),
                  profit=Decimal("100.00"), status=TradeStatus.CLOSED),
            Trade(ticket=5002, symbol="GBPUSD", trade_type="BUY", volume=Decimal("1.0"),
                  entry_price=Decimal("1.2500"), entry_time=base_time + timedelta(hours=2),
                  exit_price=Decimal("1.2650"), exit_time=base_time + timedelta(hours=3),
                  profit=Decimal("150.00"), status=TradeStatus.CLOSED),
            Trade(ticket=5003, symbol="USDJPY", trade_type="SELL", volume=Decimal("1.0"),
                  entry_price=Decimal("110.00"), entry_time=base_time + timedelta(hours=4),
                  exit_price=Decimal("110.50"), exit_time=base_time + timedelta(hours=5),
                  profit=Decimal("-50.00"), status=TradeStatus.CLOSED),
            Trade(ticket=5004, symbol="AUDUSD", trade_type="BUY", volume=Decimal("1.0"),
                  entry_price=Decimal("0.7500"), entry_time=base_time + timedelta(hours=6),
                  exit_price=Decimal("0.7700"), exit_time=base_time + timedelta(hours=7),
                  profit=Decimal("200.00"), status=TradeStatus.CLOSED),
        ]

        aggregator = DailyAggregator()

        # Act
        max_wins = aggregator._calculate_max_consecutive(trades, winning=True)
        max_losses = aggregator._calculate_max_consecutive(trades, winning=False)

        # Assert
        assert max_wins == 2  # First two trades
        assert max_losses == 1  # One losing trade

    def test_aggregate_range(self, setup_database):
        """Test aggregation of a date range"""
        # Arrange
        with get_session() as session:
            # Create trades across multiple days
            for day in range(3):
                trade_date = datetime(2025, 12, 10 + day, 10, 0, 0, tzinfo=timezone.utc)
                for i in range(2):
                    trade = Trade(
                        ticket=2000 + day * 10 + i,  # Use 2000+ range to avoid conflicts
                        symbol="EURUSD",
                        trade_type="BUY",
                        volume=Decimal("1.0"),
                        entry_price=Decimal("1.1000"),
                        entry_time=trade_date + timedelta(hours=i),
                        exit_price=Decimal("1.1100"),
                        exit_time=trade_date + timedelta(hours=i+1),
                        profit=Decimal("100.00"),
                        status=TradeStatus.CLOSED
                    )
                    session.add(trade)
            session.commit()

        aggregator = DailyAggregator()
        start_date = date(2025, 12, 10)
        end_date = date(2025, 12, 12)

        # Act
        results = aggregator.aggregate_range(start_date, end_date)

        # Assert
        assert len(results) == 3
        assert all(r.total_trades == 2 for r in results)
        assert all(r.net_profit == Decimal("200.00") for r in results)

    def test_backfill_no_trades(self, setup_database):
        """Test backfill with no trade data"""
        # Arrange
        aggregator = DailyAggregator()

        # Act
        results = aggregator.backfill()

        # Assert
        assert results == []

    def test_backfill_with_trades(self, setup_database):
        """Test backfill with historical trade data"""
        # Arrange
        with get_session() as session:
            # Create trades across 3 historical days
            for day in range(3):
                trade_date = datetime(2025, 12, 10 + day, 10, 0, 0, tzinfo=timezone.utc)
                trade = Trade(
                    ticket=3000 + day,  # Use 3000+ range to avoid conflicts
                    symbol="EURUSD",
                    trade_type="BUY",
                    volume=Decimal("1.0"),
                    entry_price=Decimal("1.1000"),
                    entry_time=trade_date,
                    exit_price=Decimal("1.1100"),
                    exit_time=trade_date + timedelta(hours=1),
                    profit=Decimal("100.00"),
                    status=TradeStatus.CLOSED
                )
                session.add(trade)
            session.commit()

        aggregator = DailyAggregator()

        # Act
        results = aggregator.backfill()

        # Assert
        assert len(results) >= 3  # At least the 3 days with trades
        assert all(isinstance(r, DailyPerformance) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
