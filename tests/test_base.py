"""
Tests for base connector classes
"""
import pytest
from datetime import datetime
from src.connectors.base import (
    BaseMetaTraderConnector, PlatformType, OrderType,
    ConnectionStatus, TickData, Position, AccountInfo,
    OHLCBar, SymbolInfo, TradeRequest, TradeResult
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
    """Test all ConnectionStatus enum values"""
    assert ConnectionStatus.DISCONNECTED.value == "DISCONNECTED"
    assert ConnectionStatus.CONNECTING.value == "CONNECTING"
    assert ConnectionStatus.CONNECTED.value == "CONNECTED"
    assert ConnectionStatus.ERROR.value == "ERROR"


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


def test_ohlc_bar():
    """Test OHLCBar dataclass"""
    bar = OHLCBar(
        symbol="EURUSD",
        timeframe="M5",
        time=datetime.now(),
        open=1.0850,
        high=1.0860,
        low=1.0840,
        close=1.0855,
        tick_volume=1000,
        real_volume=100000.0,
        spread=2
    )
    
    assert bar.symbol == "EURUSD"
    assert bar.timeframe == "M5"
    assert bar.open == 1.0850
    assert bar.close == 1.0855


def test_symbol_info():
    """Test SymbolInfo dataclass"""
    info = SymbolInfo(
        name="EURUSD",
        description="Euro vs US Dollar",
        base_currency="EUR",
        quote_currency="USD",
        digits=5,
        point=0.00001,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        contract_size=100000,
        bid=1.0850,
        ask=1.0852,
        spread=0.0002,
        trade_allowed=True
    )
    
    assert info.name == "EURUSD"
    assert info.base_currency == "EUR"
    assert info.quote_currency == "USD"


def test_trade_request():
    """Test TradeRequest dataclass"""
    request = TradeRequest(
        symbol="EURUSD",
        action=OrderType.BUY,
        volume=0.01,
        price=1.0850,
        sl=1.0840,
        tp=1.0900,
        deviation=20,
        magic=234000,
        comment="Test trade"
    )
    
    assert request.symbol == "EURUSD"
    assert request.action == OrderType.BUY
    assert request.volume == 0.01
    assert request.sl == 1.0840


def test_trade_result():
    """Test TradeResult dataclass"""
    result = TradeResult(
        success=True,
        order_ticket=123456,
        deal_ticket=123457,
        volume=0.01,
        price=1.0850,
        comment="Order executed",
        error_code=0,
        error_message=""
    )
    
    assert result.success is True
    assert result.order_ticket == 123456
    assert result.volume == 0.01


# Create a concrete implementation for testing abstract class
class ConcreteConnector(BaseMetaTraderConnector):
    """Concrete connector for testing"""
    
    def connect(self, login: int, password: str, server: str, **kwargs) -> bool:
        self.status = ConnectionStatus.CONNECTED
        self._connection_params = {
            'login': login,
            'password': password,
            'server': server
        }
        return True
    
    def disconnect(self) -> None:
        self.status = ConnectionStatus.DISCONNECTED
    
    def is_connected(self) -> bool:
        return self.status == ConnectionStatus.CONNECTED
    
    def reconnect(self) -> bool:
        if self._connection_params:
            return self.connect(**self._connection_params)
        return False
    
    def get_account_info(self):
        return None
    
    def get_symbols(self, group: str = "*"):
        return []
    
    def get_symbol_info(self, symbol: str):
        return None
    
    def select_symbol(self, symbol: str, enable: bool = True) -> bool:
        return True
    
    def get_tick(self, symbol: str):
        return None
    
    def get_bars(self, symbol: str, timeframe: str, count: int, start_pos: int = 0):
        return []
    
    def send_order(self, request):
        return TradeResult(success=False)
    
    def close_position(self, ticket: int):
        return TradeResult(success=False)
    
    def modify_position(self, ticket: int, sl=None, tp=None):
        return TradeResult(success=False)
    
    def get_positions(self, symbol=None):
        return []
    
    def get_position_by_ticket(self, ticket: int):
        return None


def test_base_connector_initialization():
    """Test BaseMetaTraderConnector initialization"""
    connector = ConcreteConnector(instance_id="test1", platform=PlatformType.MT5)
    
    assert connector.instance_id == "test1"
    assert connector.platform == PlatformType.MT5
    assert connector.status == ConnectionStatus.DISCONNECTED
    assert connector._connection_params == {}


def test_base_connector_utility_methods():
    """Test utility methods of BaseMetaTraderConnector"""
    connector = ConcreteConnector(instance_id="test1", platform=PlatformType.MT5)
    
    # Test get_platform_type
    assert connector.get_platform_type() == PlatformType.MT5
    
    # Test get_instance_id
    assert connector.get_instance_id() == "test1"
    
    # Test get_status
    assert connector.get_status() == ConnectionStatus.DISCONNECTED
    
    # Change status and check again
    connector.status = ConnectionStatus.CONNECTED
    assert connector.get_status() == ConnectionStatus.CONNECTED


def test_base_connector_str_repr():
    """Test __str__ and __repr__ methods"""
    connector = ConcreteConnector(instance_id="test1", platform=PlatformType.MT5)
    
    str_repr = str(connector)
    assert "MT5Connector" in str_repr
    assert "instance=test1" in str_repr
    assert "status=DISCONNECTED" in str_repr
    
    # __repr__ should return the same as __str__
    assert repr(connector) == str(connector)


def test_base_connector_mt4_platform():
    """Test connector with MT4 platform"""
    connector = ConcreteConnector(instance_id="mt4_test", platform=PlatformType.MT4)
    
    assert connector.get_platform_type() == PlatformType.MT4
    assert "MT4Connector" in str(connector)
