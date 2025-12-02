"""
Tests for base connector classes
"""
import pytest
from src.connectors.base import (
    BaseMetaTraderConnector, PlatformType, OrderType,
    ConnectionStatus, TickData, Position, AccountInfo
)


def test_order_type_enum():
    """Test OrderType enum"""
    assert OrderType.BUY.value == "BUY"
    assert OrderType.SELL.value == "SELL"
    assert OrderType.BUY_LIMIT.value == "BUY_LIMIT"


def test_platform_type_enum():
    """Test PlatformType enum"""
    assert PlatformType.MT4.value == "MT4"
    assert PlatformType.MT5.value == "MT5"


def test_connection_status_enum():
    """Test ConnectionStatus enum"""
    assert ConnectionStatus.DISCONNECTED.value == "DISCONNECTED"
    assert ConnectionStatus.CONNECTED.value == "CONNECTED"


def test_tick_data():
    """Test TickData dataclass"""
    from datetime import datetime
    
    tick = TickData(
        symbol="EURUSD",
        time=datetime.now(),
        bid=1.0850,
        ask=1.0852,
        last=1.0851,
        volume=100,
        spread=0.0002
    )
    
    assert tick.symbol == "EURUSD"
    assert tick.bid == 1.0850
    assert tick.ask == 1.0852
    assert tick.mid_price == 1.0851


def test_position_pnl_calculation():
    """Test Position P&L calculation"""
    from datetime import datetime
    
    # Buy position with profit
    buy_pos = Position(
        ticket=123456,
        symbol="EURUSD",
        type=OrderType.BUY,
        volume=0.01,
        price_open=1.0850,
        price_current=1.0860,
        sl=1.0840,
        tp=1.0900,
        profit=10.0,
        time_open=datetime.now()
    )
    
    assert buy_pos.pnl_pips == pytest.approx(10.0, rel=1e-6)  # 0.0010 * 10000
    
    # Sell position with profit
    sell_pos = Position(
        ticket=123457,
        symbol="EURUSD",
        type=OrderType.SELL,
        volume=0.01,
        price_open=1.0860,
        price_current=1.0850,
        sl=1.0870,
        tp=1.0800,
        profit=10.0
    )
    
    assert sell_pos.pnl_pips == pytest.approx(10.0, rel=1e-6)


def test_account_info():
    """Test AccountInfo dataclass"""
    account = AccountInfo(
        login=12345,
        server="Test-Server",
        name="Test Account",
        company="Test Broker",
        currency="USD",
        balance=10000.0,
        equity=10050.0,
        profit=50.0,
        margin=100.0,
        margin_free=9950.0,
        margin_level=10050.0,
        leverage=100,
        trade_allowed=True
    )
    
    assert account.margin_used_percent == pytest.approx(0.995, rel=0.01)
    assert account.available_for_trading == 9950.0
