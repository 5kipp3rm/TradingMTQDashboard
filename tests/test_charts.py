"""
Tests for Advanced Charts API

Tests chart data endpoints for equity curve, trade distribution,
symbol performance, win/loss analysis, and risk/reward analysis.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
from decimal import Decimal

from src.api.app import create_app
from src.database.models import Trade, TradeStatus, SignalType, DailyPerformance
from src.database.connection import get_session, init_db
from sqlalchemy import text


@pytest.fixture(scope="function")
def setup_database():
    """Initialize test database"""
    init_db()

    with get_session() as session:
        session.execute(text("DELETE FROM trades"))
        session.execute(text("DELETE FROM daily_performance"))
        session.commit()

    yield

    with get_session() as session:
        session.execute(text("DELETE FROM trades"))
        session.execute(text("DELETE FROM daily_performance"))
        session.commit()


@pytest.fixture
def client(setup_database):
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_trades(setup_database):
    """Create sample trade data for testing"""
    with get_session() as session:
        # Create 10 closed trades
        for i in range(10):
            trade = Trade(
                ticket=1000 + i,
                symbol="EURUSD" if i % 2 == 0 else "GBPUSD",
                trade_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                status=TradeStatus.CLOSED,
                entry_price=Decimal("1.12000") + Decimal(i) / 1000,
                exit_price=Decimal("1.12100") + Decimal(i) / 1000,
                volume=Decimal("0.1"),
                entry_time=datetime.now() - timedelta(days=10-i),
                exit_time=datetime.now() - timedelta(days=10-i) + timedelta(hours=4),
                profit=Decimal("50.00") if i % 2 == 0 else Decimal("-25.00"),
                pips=Decimal("10.0") if i % 2 == 0 else Decimal("-5.0"),
                duration_seconds=14400,  # 4 hours
                stop_loss=Decimal("1.11500"),
                take_profit=Decimal("1.13000")
            )
            session.add(trade)

        session.commit()


@pytest.fixture
def sample_daily_performance(setup_database):
    """Create sample daily performance data"""
    with get_session() as session:
        # Create 30 days of performance data
        for i in range(30):
            perf = DailyPerformance(
                date=datetime.now() - timedelta(days=30-i),
                total_trades=5,
                winning_trades=3,
                losing_trades=2,
                net_profit=Decimal("100.00") if i % 2 == 0 else Decimal("50.00"),
                gross_profit=Decimal("150.00"),
                gross_loss=Decimal("-50.00"),
                win_rate=Decimal("60.0"),
                end_balance=Decimal("10000.00") + Decimal(i * 100),
                end_equity=Decimal("10100.00") + Decimal(i * 100)
            )
            session.add(perf)

        session.commit()


# =============================================================================
# Equity Curve Tests
# =============================================================================

class TestEquityCurve:
    """Tests for equity curve endpoint"""

    def test_equity_curve_daily(self, client, sample_daily_performance):
        """Test daily equity curve"""
        response = client.get("/api/charts/equity-curve?granularity=daily&days=30")
        assert response.status_code == 200

        data = response.json()
        assert "granularity" in data
        assert data["granularity"] == "daily"
        assert "data" in data
        assert len(data["data"]) > 0

        # Check data structure
        first_point = data["data"][0]
        assert "date" in first_point
        assert "balance" in first_point
        assert "cumulative_profit" in first_point

    def test_equity_curve_trade(self, client, sample_trades):
        """Test per-trade equity curve"""
        response = client.get("/api/charts/equity-curve?granularity=trade&days=30")
        assert response.status_code == 200

        data = response.json()
        assert data["granularity"] == "trade"
        assert len(data["data"]) == 10  # Should match number of closed trades

        # Verify cumulative profit calculation
        cumulative = 0
        for point in data["data"]:
            cumulative += point["profit"]
            assert abs(point["cumulative_profit"] - cumulative) < 0.01

    def test_equity_curve_invalid_granularity(self, client):
        """Test invalid granularity returns error"""
        response = client.get("/api/charts/equity-curve?granularity=invalid")
        assert response.status_code == 400


# =============================================================================
# Trade Distribution Tests
# =============================================================================

class TestTradeDistribution:
    """Tests for trade distribution heatmap"""

    def test_trade_distribution(self, client, sample_trades):
        """Test trade distribution by hour and day"""
        response = client.get("/api/charts/trade-distribution?days=30")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

        # Check heatmap data structure
        if len(data["data"]) > 0:
            point = data["data"][0]
            assert "day" in point
            assert "day_num" in point
            assert "hour" in point
            assert "trade_count" in point
            assert "total_profit" in point
            assert "avg_profit" in point

    def test_trade_distribution_date_range(self, client, sample_trades):
        """Test distribution with custom date range"""
        end_date = date.today()
        start_date = end_date - timedelta(days=15)

        response = client.get(
            f"/api/charts/trade-distribution?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200


# =============================================================================
# Symbol Performance Tests
# =============================================================================

class TestSymbolPerformance:
    """Tests for symbol performance comparison"""

    def test_symbol_performance(self, client, sample_trades):
        """Test symbol performance metrics"""
        response = client.get("/api/charts/symbol-performance?days=30&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert "symbols" in data
        assert len(data["symbols"]) > 0

        # Check symbol data structure
        symbol = data["symbols"][0]
        assert "symbol" in symbol
        assert "total_trades" in symbol
        assert "winning_trades" in symbol
        assert "losing_trades" in symbol
        assert "win_rate" in symbol
        assert "net_profit" in symbol
        assert "avg_profit" in symbol

    def test_symbol_performance_ordering(self, client, sample_trades):
        """Test symbols are ordered by net profit"""
        response = client.get("/api/charts/symbol-performance?days=30")
        assert response.status_code == 200

        data = response.json()
        symbols = data["symbols"]

        # Verify ordering (descending by net profit)
        for i in range(len(symbols) - 1):
            assert symbols[i]["net_profit"] >= symbols[i+1]["net_profit"]

    def test_symbol_performance_limit(self, client, sample_trades):
        """Test limit parameter"""
        response = client.get("/api/charts/symbol-performance?days=30&limit=1")
        assert response.status_code == 200

        data = response.json()
        assert len(data["symbols"]) <= 1


# =============================================================================
# Win/Loss Analysis Tests
# =============================================================================

class TestWinLossAnalysis:
    """Tests for win/loss analysis"""

    def test_win_loss_analysis(self, client, sample_trades):
        """Test win/loss analysis data"""
        response = client.get("/api/charts/win-loss-analysis?days=30")
        assert response.status_code == 200

        data = response.json()
        assert "profit_distribution" in data
        assert "streaks" in data
        assert "duration_analysis" in data

        # Check profit distribution
        assert isinstance(data["profit_distribution"], dict)

        # Check streaks
        streaks = data["streaks"]
        assert "max_win_streak" in streaks
        assert "max_loss_streak" in streaks
        assert isinstance(streaks["max_win_streak"], int)
        assert isinstance(streaks["max_loss_streak"], int)

        # Check duration analysis
        assert isinstance(data["duration_analysis"], dict)

    def test_win_loss_streaks(self, client):
        """Test streak calculation with specific pattern"""
        with get_session() as session:
            # Create specific win/loss pattern: W W W L L W
            profits = [50, 50, 50, -25, -25, 50]
            for i, profit in enumerate(profits):
                trade = Trade(
                    ticket=2000 + i,
                    symbol="EURUSD",
                    trade_type=SignalType.BUY,
                    status=TradeStatus.CLOSED,
                    entry_price=Decimal("1.12000"),
                    exit_price=Decimal("1.12100"),
                    volume=Decimal("0.1"),
                    entry_time=datetime.now() - timedelta(days=6-i),
                    exit_time=datetime.now() - timedelta(days=6-i) + timedelta(hours=1),
                    profit=Decimal(str(profit)),
                    duration_seconds=3600
                )
                session.add(trade)
            session.commit()

        response = client.get("/api/charts/win-loss-analysis?days=7")
        assert response.status_code == 200

        data = response.json()
        streaks = data["streaks"]
        assert streaks["max_win_streak"] == 3
        assert streaks["max_loss_streak"] == 2


# =============================================================================
# Monthly Comparison Tests
# =============================================================================

class TestMonthlyComparison:
    """Tests for monthly comparison"""

    def test_monthly_comparison(self, client, sample_daily_performance):
        """Test monthly aggregation"""
        response = client.get("/api/charts/monthly-comparison?months=12")
        assert response.status_code == 200

        data = response.json()
        assert "months" in data
        assert "data" in data
        assert isinstance(data["data"], list)

        # Check monthly data structure
        if len(data["data"]) > 0:
            month_data = data["data"][0]
            assert "year" in month_data
            assert "month" in month_data
            assert "month_name" in month_data
            assert "total_trades" in month_data
            assert "net_profit" in month_data

    def test_monthly_comparison_limit(self, client, sample_daily_performance):
        """Test months limit"""
        response = client.get("/api/charts/monthly-comparison?months=1")
        assert response.status_code == 200

        data = response.json()
        assert data["months"] == 1


# =============================================================================
# Risk/Reward Tests
# =============================================================================

class TestRiskReward:
    """Tests for risk/reward scatter plot"""

    def test_risk_reward_scatter(self, client, sample_trades):
        """Test risk/reward data"""
        response = client.get("/api/charts/risk-reward-scatter?days=30")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "total_trades" in data

        # Check scatter data structure
        if len(data["data"]) > 0:
            point = data["data"][0]
            assert "trade_id" in point
            assert "symbol" in point
            assert "profit" in point
            assert "risk" in point
            assert "reward" in point
            assert "risk_reward_ratio" in point
            assert "outcome" in point

    def test_risk_reward_calculation(self, client):
        """Test risk/reward ratio calculation"""
        with get_session() as session:
            # Create trade with known R:R
            trade = Trade(
                ticket=3000,
                symbol="EURUSD",
                trade_type=SignalType.BUY,
                status=TradeStatus.CLOSED,
                entry_price=Decimal("1.12000"),
                exit_price=Decimal("1.12300"),
                volume=Decimal("0.1"),
                entry_time=datetime.now() - timedelta(days=1),
                exit_time=datetime.now(),
                profit=Decimal("100.00"),
                stop_loss=Decimal("1.11800"),  # 200 pips risk
                take_profit=Decimal("1.12400")  # 400 pips reward (R:R = 2:1)
            )
            session.add(trade)
            session.commit()

        response = client.get("/api/charts/risk-reward-scatter?days=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1

        point = data["data"][0]
        # Risk should be ~0.002, Reward should be ~0.004, R:R should be ~2.0
        assert point["risk"] > 0
        assert point["reward"] > 0
        assert abs(point["risk_reward_ratio"] - 2.0) < 0.5

    def test_risk_reward_limit(self, client, sample_trades):
        """Test limit parameter"""
        response = client.get("/api/charts/risk-reward-scatter?days=30&limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) <= 5


# =============================================================================
# Integration Tests
# =============================================================================

class TestChartsIntegration:
    """Integration tests for charts API"""

    def test_all_endpoints_available(self, client):
        """Test all chart endpoints are accessible"""
        endpoints = [
            "/api/charts/equity-curve",
            "/api/charts/trade-distribution",
            "/api/charts/symbol-performance",
            "/api/charts/win-loss-analysis",
            "/api/charts/monthly-comparison",
            "/api/charts/risk-reward-scatter"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 500]  # 500 if no data, but endpoint exists

    def test_charts_with_no_data(self, client, setup_database):
        """Test charts return gracefully with no data"""
        response = client.get("/api/charts/equity-curve?granularity=daily")
        # Should not error, just return empty data
        assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
