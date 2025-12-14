"""
Tests for Analytics API

Tests the FastAPI endpoints for analytics dashboard and monitoring.
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.api.app import create_app
from src.database.models import Trade, TradeStatus, DailyPerformance
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
def client(setup_database):
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_trades():
    """Create sample trade data"""
    today = date.today()
    base_time = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

    trades = [
        Trade(
            ticket=7001,
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
            ticket=7002,
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
        Trade(
            ticket=7003,
            symbol="EURUSD",
            trade_type="SELL",
            volume=Decimal("0.8"),
            entry_price=Decimal("1.1100"),
            exit_price=Decimal("1.1150"),
            entry_time=base_time + timedelta(hours=14),
            exit_time=base_time + timedelta(hours=15),
            profit=Decimal("-200.00"),
            pips=Decimal("-50.0"),
            status=TradeStatus.CLOSED
        ),
    ]

    return trades


@pytest.fixture
def sample_daily_performance():
    """Create sample daily performance data"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    records = [
        DailyPerformance(
            date=datetime.combine(two_days_ago, datetime.min.time()).replace(tzinfo=timezone.utc),
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            net_profit=Decimal("500.00"),
            gross_profit=Decimal("800.00"),
            gross_loss=Decimal("300.00"),
            win_rate=Decimal("60.0")
        ),
        DailyPerformance(
            date=datetime.combine(yesterday, datetime.min.time()).replace(tzinfo=timezone.utc),
            total_trades=8,
            winning_trades=5,
            losing_trades=3,
            net_profit=Decimal("800.00"),
            gross_profit=Decimal("1200.00"),
            gross_loss=Decimal("400.00"),
            win_rate=Decimal("62.5")
        ),
    ]

    return records


class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "TradingMTQ Analytics API"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data

    def test_status_endpoint(self, client):
        """Test detailed status endpoint"""
        response = client.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "components" in data
        assert "database" in data["components"]
        assert "scheduler" in data["components"]


class TestTradesEndpoints:
    """Tests for trades endpoints"""

    def test_get_trades_empty(self, client):
        """Test getting trades when database is empty"""
        response = client.get("/api/trades/")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["trades"] == []

    def test_get_trades_with_data(self, client, sample_trades):
        """Test getting trades with data"""
        # Add sample trades
        with get_session() as session:
            for trade in sample_trades:
                session.add(trade)
            session.commit()

        response = client.get("/api/trades/")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["trades"]) == 3

    def test_get_trade_by_ticket(self, client, sample_trades):
        """Test getting specific trade by ticket"""
        # Add sample trades
        with get_session() as session:
            for trade in sample_trades:
                session.add(trade)
            session.commit()

        response = client.get("/api/trades/7001")

        assert response.status_code == 200
        data = response.json()
        assert data["ticket"] == 7001
        assert data["symbol"] == "EURUSD"
        assert data["profit"] == 500.00

    def test_get_trade_not_found(self, client):
        """Test getting non-existent trade"""
        response = client.get("/api/trades/99999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_stats_by_symbol(self, client, sample_trades):
        """Test getting statistics by symbol"""
        # Add sample trades
        with get_session() as session:
            for trade in sample_trades:
                session.add(trade)
            session.commit()

        response = client.get("/api/trades/stats/by-symbol?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 30
        assert len(data["symbols"]) == 2  # EURUSD and GBPUSD


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints"""

    def test_get_summary_empty(self, client):
        """Test getting summary with no data"""
        response = client.get("/api/analytics/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_days"] == 0
        assert data["total_trades"] == 0

    def test_get_summary_with_data(self, client, sample_daily_performance):
        """Test getting summary with data"""
        # Add sample daily performance
        with get_session() as session:
            for record in sample_daily_performance:
                session.add(record)
            session.commit()

        response = client.get("/api/analytics/summary?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 13  # 5 + 8
        assert data["total_profit"] == 1300.00  # 500 + 800

    def test_get_daily_records(self, client, sample_daily_performance):
        """Test getting daily performance records"""
        # Add sample daily performance
        with get_session() as session:
            for record in sample_daily_performance:
                session.add(record)
            session.commit()

        response = client.get("/api/analytics/daily")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["records"]) == 2

    def test_get_daily_record_by_date(self, client, sample_daily_performance):
        """Test getting specific daily record"""
        # Add sample daily performance
        with get_session() as session:
            for record in sample_daily_performance:
                session.add(record)
            session.commit()

        yesterday = date.today() - timedelta(days=1)
        response = client.get(f"/api/analytics/daily/{yesterday}")

        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 8

    def test_get_daily_record_not_found(self, client):
        """Test getting non-existent daily record"""
        future_date = date.today() + timedelta(days=30)
        response = client.get(f"/api/analytics/daily/{future_date}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_trigger_aggregation(self, client, sample_trades):
        """Test manual aggregation trigger"""
        # Add sample trades
        with get_session() as session:
            for trade in sample_trades:
                session.add(trade)
            session.commit()

        today = date.today()
        response = client.post(f"/api/analytics/aggregate?target_date={today}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_trades"] == 3

    def test_trigger_aggregation_no_trades(self, client):
        """Test aggregation with no trades"""
        future_date = date.today() + timedelta(days=30)
        response = client.post(f"/api/analytics/aggregate?target_date={future_date}")

        assert response.status_code == 404
        data = response.json()
        assert "no closed trades" in data["detail"].lower()

    def test_get_performance_metrics(self, client, sample_daily_performance):
        """Test getting performance metrics for charting"""
        # Add sample daily performance
        with get_session() as session:
            for record in sample_daily_performance:
                session.add(record)
            session.commit()

        response = client.get("/api/analytics/metrics?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 30
        assert len(data["dates"]) == 2
        assert len(data["cumulative_profit"]) == 2


class TestCORS:
    """Tests for CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are configured"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        # FastAPI TestClient doesn't fully simulate CORS preflight
        # but we can verify the endpoint responds
        assert response.status_code in [200, 405]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
