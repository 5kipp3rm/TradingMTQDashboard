"""
Unit Tests for Database Models

Tests model validation, enums, and business logic
"""
import pytest
from datetime import datetime
from decimal import Decimal

from src.database.models import (
    Trade, Signal, AccountSnapshot, DailyPerformance,
    TradeStatus, SignalType
)


class TestTradeStatus:
    """Test TradeStatus enum"""

    def test_enum_values(self):
        """Test all enum values exist"""
        assert TradeStatus.PENDING.value == "pending"
        assert TradeStatus.OPEN.value == "open"
        assert TradeStatus.CLOSED.value == "closed"
        assert TradeStatus.CANCELLED.value == "cancelled"
        assert TradeStatus.FAILED.value == "failed"


class TestSignalType:
    """Test SignalType enum"""

    def test_enum_values(self):
        """Test all enum values exist"""
        assert SignalType.BUY.value == "buy"
        assert SignalType.SELL.value == "sell"
        assert SignalType.HOLD.value == "hold"


class TestTradeModel:
    """Test Trade model"""

    def test_trade_creation(self):
        """Test creating a Trade instance"""
        trade = Trade(
            ticket=123456,
            symbol="EURUSD",
            magic_number=0,
            trade_type="BUY",
            status="OPEN",
            entry_price=Decimal("1.0850"),
            entry_time=datetime.now(),
            volume=Decimal("0.1")
        )

        assert trade.ticket == 123456
        assert trade.symbol == "EURUSD"
        assert trade.trade_type == "BUY"
        assert trade.status == "OPEN"
        assert trade.entry_price == Decimal("1.0850")
        assert trade.volume == Decimal("0.1")

    def test_trade_to_dict(self):
        """Test Trade.to_dict() method"""
        now = datetime.now()
        trade = Trade(
            ticket=123456,
            symbol="EURUSD",
            trade_type="BUY",
            status="OPEN",
            entry_price=Decimal("1.0850"),
            entry_time=now,
            volume=Decimal("0.1"),
            profit=Decimal("50.00"),
            ml_enhanced=True,
            ai_approved=True
        )

        trade_dict = trade.to_dict()

        assert trade_dict['ticket'] == 123456
        assert trade_dict['symbol'] == "EURUSD"
        assert trade_dict['trade_type'] == "BUY"
        assert trade_dict['status'] == "OPEN"
        assert trade_dict['entry_price'] == 1.0850
        assert trade_dict['volume'] == 0.1
        assert trade_dict['profit'] == 50.00
        assert trade_dict['ml_enhanced'] is True
        assert trade_dict['ai_approved'] is True

    def test_trade_repr(self):
        """Test Trade.__repr__()"""
        trade = Trade(
            ticket=123456,
            symbol="EURUSD",
            trade_type="BUY",
            status="OPEN",
            entry_price=Decimal("1.0850"),
            entry_time=datetime.now(),
            volume=Decimal("0.1")
        )

        repr_str = repr(trade)
        assert "Trade" in repr_str
        assert "EURUSD" in repr_str
        assert "BUY" in repr_str


class TestSignalModel:
    """Test Signal model"""

    def test_signal_creation(self):
        """Test creating a Signal instance"""
        signal = Signal(
            symbol="EURUSD",
            signal_type="BUY",
            timestamp=datetime.now(),
            price=Decimal("1.0850"),
            confidence=0.85,
            strategy_name="TestStrategy",
            timeframe="M5"
        )

        assert signal.symbol == "EURUSD"
        assert signal.signal_type == "BUY"
        assert signal.confidence == 0.85
        assert signal.strategy_name == "TestStrategy"
        assert signal.timeframe == "M5"

    def test_signal_to_dict(self):
        """Test Signal.to_dict() method"""
        now = datetime.now()
        signal = Signal(
            symbol="EURUSD",
            signal_type="BUY",
            timestamp=now,
            price=Decimal("1.0850"),
            confidence=0.85,
            strategy_name="TestStrategy",
            timeframe="M5",
            ml_enhanced=True,
            executed=True
        )

        signal_dict = signal.to_dict()

        assert signal_dict['symbol'] == "EURUSD"
        assert signal_dict['signal_type'] == "BUY"
        assert signal_dict['price'] == 1.0850
        assert signal_dict['confidence'] == 0.85
        assert signal_dict['ml_enhanced'] is True
        assert signal_dict['executed'] is True

    def test_signal_repr(self):
        """Test Signal.__repr__()"""
        signal = Signal(
            symbol="EURUSD",
            signal_type="BUY",
            timestamp=datetime.now(),
            price=Decimal("1.0850"),
            confidence=0.85,
            strategy_name="TestStrategy",
            timeframe="M5"
        )

        repr_str = repr(signal)
        assert "Signal" in repr_str
        assert "EURUSD" in repr_str
        assert "BUY" in repr_str
        assert "0.85" in repr_str


class TestAccountSnapshotModel:
    """Test AccountSnapshot model"""

    def test_snapshot_creation(self):
        """Test creating an AccountSnapshot instance"""
        snapshot = AccountSnapshot(
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

        assert snapshot.account_number == 12345
        assert snapshot.server == "TestServer"
        assert snapshot.broker == "TestBroker"
        assert snapshot.balance == Decimal("10000.00")
        assert snapshot.equity == Decimal("10050.00")

    def test_snapshot_to_dict(self):
        """Test AccountSnapshot.to_dict() method"""
        now = datetime.now()
        snapshot = AccountSnapshot(
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
            snapshot_time=now
        )

        snapshot_dict = snapshot.to_dict()

        assert snapshot_dict['account_number'] == 12345
        assert snapshot_dict['balance'] == 10000.00
        assert snapshot_dict['equity'] == 10050.00
        assert snapshot_dict['open_positions'] == 1


class TestDailyPerformanceModel:
    """Test DailyPerformance model"""

    def test_performance_creation(self):
        """Test creating a DailyPerformance instance"""
        from datetime import date
        performance = DailyPerformance(
            date=datetime.combine(date.today(), datetime.min.time()),
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            gross_profit=Decimal("500.00"),
            gross_loss=Decimal("150.00"),
            net_profit=Decimal("350.00"),
            win_rate=Decimal("70.00"),
            profit_factor=Decimal("3.33")
        )

        assert performance.total_trades == 10
        assert performance.winning_trades == 7
        assert performance.losing_trades == 3
        assert performance.net_profit == Decimal("350.00")
        assert performance.win_rate == Decimal("70.00")

    def test_performance_to_dict(self):
        """Test DailyPerformance.to_dict() method"""
        from datetime import date
        today = date.today()
        performance = DailyPerformance(
            date=datetime.combine(today, datetime.min.time()),
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            gross_profit=Decimal("500.00"),
            gross_loss=Decimal("150.00"),
            net_profit=Decimal("350.00"),
            win_rate=Decimal("70.00")
        )

        perf_dict = performance.to_dict()

        assert perf_dict['date'] == today.isoformat()
        assert perf_dict['total_trades'] == 10
        assert perf_dict['winning_trades'] == 7
        assert perf_dict['net_profit'] == 350.00
        assert perf_dict['win_rate'] == 70.00
