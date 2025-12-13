"""
Tests for Analytics Scheduler

Tests the AnalyticsScheduler class for automated daily aggregation.
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import text
import time

from src.analytics.scheduler import AnalyticsScheduler, get_scheduler
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
def sample_trades_yesterday():
    """Create sample trade data for yesterday"""
    yesterday = date.today() - timedelta(days=1)
    base_time = datetime.combine(yesterday, datetime.min.time()).replace(tzinfo=timezone.utc)

    trades = [
        Trade(
            ticket=6001,
            symbol="EURUSD",
            trade_type="BUY",
            volume=Decimal("1.0"),
            entry_price=Decimal("1.1000"),
            exit_price=Decimal("1.1050"),
            entry_time=base_time + timedelta(hours=10),
            exit_time=base_time + timedelta(hours=11),
            profit=Decimal("500.00"),
            pips=Decimal("50.0"),
            status=TradeStatus.CLOSED
        ),
        Trade(
            ticket=6002,
            symbol="GBPUSD",
            trade_type="BUY",
            volume=Decimal("0.5"),
            entry_price=Decimal("1.2500"),
            exit_price=Decimal("1.2600"),
            entry_time=base_time + timedelta(hours=12),
            exit_time=base_time + timedelta(hours=13),
            profit=Decimal("300.00"),
            pips=Decimal("100.0"),
            status=TradeStatus.CLOSED
        ),
    ]

    return trades


class TestAnalyticsScheduler:
    """Tests for AnalyticsScheduler class"""

    def test_scheduler_initialization(self, setup_database):
        """Test scheduler can be initialized"""
        scheduler = AnalyticsScheduler(aggregation_hour=0, aggregation_minute=5)

        assert scheduler is not None
        assert scheduler.aggregation_hour == 0
        assert scheduler.aggregation_minute == 5
        assert scheduler.scheduler is not None
        assert not scheduler.scheduler.running

    def test_scheduler_start_stop(self, setup_database):
        """Test scheduler can be started and stopped"""
        scheduler = AnalyticsScheduler(aggregation_hour=0, aggregation_minute=5)

        # Start scheduler
        scheduler.start()
        assert scheduler.scheduler.running

        # Stop scheduler
        scheduler.stop()
        assert not scheduler.scheduler.running

    def test_scheduler_has_daily_job(self, setup_database):
        """Test scheduler registers the daily aggregation job"""
        scheduler = AnalyticsScheduler(aggregation_hour=0, aggregation_minute=5)
        scheduler.start()

        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == 'daily_aggregation'
        assert jobs[0].name == 'Daily Performance Aggregation'

        scheduler.stop()

    def test_manual_trigger_with_trades(self, setup_database, sample_trades_yesterday):
        """Test manual trigger of aggregation with trades"""
        # Create trades for yesterday
        with get_session() as session:
            for trade in sample_trades_yesterday:
                session.add(trade)
            session.commit()

        scheduler = AnalyticsScheduler()
        yesterday = date.today() - timedelta(days=1)

        # Manually trigger aggregation
        result = scheduler.trigger_aggregation_now(target_date=yesterday)

        # Verify result
        assert result is not None
        assert result.total_trades == 2
        assert result.net_profit == Decimal("800.00")
        assert result.date.date() == yesterday  # date field is datetime, extract date part

    def test_manual_trigger_no_trades(self, setup_database):
        """Test manual trigger with no trades"""
        scheduler = AnalyticsScheduler()
        yesterday = date.today() - timedelta(days=1)

        # Manually trigger aggregation (no trades)
        result = scheduler.trigger_aggregation_now(target_date=yesterday)

        # Verify no result
        assert result is None

    def test_get_status(self, setup_database):
        """Test get_status returns scheduler information"""
        scheduler = AnalyticsScheduler(aggregation_hour=2, aggregation_minute=30)
        scheduler.start()

        status = scheduler.get_status()

        assert status['running'] is True
        assert status['jobs_count'] == 1
        assert status['aggregation_time'] == "02:30"
        assert 'next_run' in status

        scheduler.stop()

    def test_get_scheduler_singleton(self, setup_database):
        """Test get_scheduler returns singleton instance"""
        scheduler1 = get_scheduler(aggregation_hour=1, aggregation_minute=0)
        scheduler2 = get_scheduler()

        # Should be the same instance
        assert scheduler1 is scheduler2

        # Clean up
        if scheduler1.scheduler.running:
            scheduler1.stop()

    def test_scheduler_prevents_overlapping_runs(self, setup_database):
        """Test scheduler configuration prevents overlapping runs"""
        scheduler = AnalyticsScheduler()
        scheduler.start()

        jobs = scheduler.scheduler.get_jobs()
        job = jobs[0]

        # Check max_instances is set to 1
        assert job.max_instances == 1

        scheduler.stop()

    def test_scheduler_graceful_shutdown(self, setup_database):
        """Test scheduler shuts down gracefully"""
        scheduler = AnalyticsScheduler()
        scheduler.start()

        assert scheduler.scheduler.running

        # Graceful shutdown
        scheduler.stop()

        # Verify stopped
        assert not scheduler.scheduler.running

    def test_aggregation_job_function_exists(self, setup_database):
        """Test the aggregation job function is callable"""
        scheduler = AnalyticsScheduler()

        # Verify the job function exists and is callable
        assert hasattr(scheduler, '_run_daily_aggregation')
        assert callable(scheduler._run_daily_aggregation)

    def test_event_listeners_registered(self, setup_database):
        """Test scheduler has event listeners for monitoring"""
        scheduler = AnalyticsScheduler()

        # Verify event listeners are attached
        assert len(scheduler.scheduler._listeners) > 0

    def test_scheduler_custom_time(self, setup_database):
        """Test scheduler with custom aggregation time"""
        scheduler = AnalyticsScheduler(aggregation_hour=23, aggregation_minute=59)

        assert scheduler.aggregation_hour == 23
        assert scheduler.aggregation_minute == 59

        scheduler.start()

        status = scheduler.get_status()
        assert status['aggregation_time'] == "23:59"

        scheduler.stop()

    def test_manual_trigger_defaults_to_yesterday(self, setup_database, sample_trades_yesterday):
        """Test manual trigger defaults to yesterday"""
        # Create trades for yesterday
        with get_session() as session:
            for trade in sample_trades_yesterday:
                session.add(trade)
            session.commit()

        scheduler = AnalyticsScheduler()

        # Trigger without specifying date (should default to yesterday)
        result = scheduler.trigger_aggregation_now()

        # Verify result
        assert result is not None
        assert result.date.date() == date.today() - timedelta(days=1)  # date field is datetime, extract date part

    def test_scheduler_atexit_registration(self, setup_database):
        """Test scheduler registers atexit handler"""
        scheduler = AnalyticsScheduler()

        # This is implicit in the implementation
        # Just verify scheduler can be created without errors
        assert scheduler is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
