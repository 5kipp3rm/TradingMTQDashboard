"""
Tests for MT5 Connector
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.connectors.mt5_connector import MT5Connector
from src.connectors.base import (
    OrderType, ConnectionStatus, TradeRequest, 
    AccountInfo, Position, SymbolInfo, OHLCBar
)


class TestMT5Connector:
    """Test suite for MT5Connector"""
    
    @pytest.fixture
    def connector(self):
        """Create connector instance"""
        return MT5Connector("test")
    
    def test_initialization(self, connector):
        """Test connector initialization"""
        assert connector.instance_id == "test"
        assert connector.status == ConnectionStatus.DISCONNECTED
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_connect_success(self, mock_mt5, connector):
        """Test successful connection"""
        mock_mt5.initialize.return_value = True
        
        # Mock account_info for verification
        mock_account = Mock()
        mock_account.login = 12345
        mock_mt5.account_info.return_value = mock_account
        
        result = connector.connect(login=12345, password="test", server="demo")
        
        assert result is True
        assert connector.status == ConnectionStatus.CONNECTED
        mock_mt5.initialize.assert_called_once()
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_connect_failure(self, mock_mt5, connector):
        """Test connection failure"""
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (1, "Init failed")
        
        result = connector.connect(login=12345, password="test", server="demo")
        
        assert result is False
        assert connector.status == ConnectionStatus.ERROR
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_disconnect(self, mock_mt5, connector):
        """Test disconnect"""
        # First connect
        mock_mt5.initialize.return_value = True
        mock_account = Mock()
        mock_account.login = 12345
        mock_mt5.account_info.return_value = mock_account
        connector.connect(login=12345, password="test", server="demo")
        
        # Then disconnect
        connector.disconnect()
        
        assert connector.status == ConnectionStatus.DISCONNECTED
        mock_mt5.shutdown.assert_called_once()
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_get_account_info(self, mock_mt5, connector):
        """Test getting account info"""
        # Setup mock
        mock_account = MagicMock()
        mock_account.login = 12345
        mock_account.server = "Demo-Server"
        mock_account.name = "Test Account"
        mock_account.company = "Test Broker"
        mock_account.currency = "USD"
        mock_account.balance = 10000.0
        mock_account.equity = 10050.0
        mock_account.profit = 50.0
        mock_account.margin = 100.0
        mock_account.margin_free = 9950.0
        mock_account.margin_level = 10050.0
        mock_account.leverage = 100
        mock_account.trade_allowed = True
        
        mock_mt5.account_info.return_value = mock_account
        
        # Test
        account = connector.get_account_info()
        
        assert account is not None
        assert account.login == 12345
        assert account.balance == 10000.0
        assert account.equity == 10050.0
        assert account.leverage == 100
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_get_symbol_info(self, mock_mt5, connector):
        """Test getting symbol info"""
        # Setup mock
        mock_symbol = MagicMock()
        mock_symbol.name = "EURUSD"
        mock_symbol.description = "Euro vs US Dollar"
        mock_symbol.currency_base = "EUR"
        mock_symbol.currency_profit = "USD"
        mock_symbol.digits = 5
        mock_symbol.point = 0.00001
        mock_symbol.volume_min = 0.01
        mock_symbol.volume_max = 100.0
        mock_symbol.volume_step = 0.01
        mock_symbol.trade_contract_size = 100000.0
        mock_symbol.bid = 1.08500
        mock_symbol.ask = 1.08520
        mock_symbol.spread = 2
        mock_symbol.trade_mode = 4  # SYMBOL_TRADE_MODE_FULL
        
        mock_mt5.symbol_info.return_value = mock_symbol
        
        # Test
        symbol = connector.get_symbol_info("EURUSD")
        
        assert symbol is not None
        assert symbol.name == "EURUSD"  # Field is 'name', not 'symbol'
        assert symbol.bid == 1.08500
        assert symbol.ask == 1.08520
        assert symbol.volume_min == 0.01
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_get_bars(self, mock_mt5, connector):
        """Test getting historical bars"""
        # Setup mock rates
        mock_rates = [
            {
                'time': 1700000000,
                'open': 1.08500,
                'high': 1.08550,
                'low': 1.08450,
                'close': 1.08520,
                'tick_volume': 1000,
                'real_volume': 100000,
                'spread': 2
            },
            {
                'time': 1700000060,
                'open': 1.08520,
                'high': 1.08580,
                'low': 1.08510,
                'close': 1.08560,
                'tick_volume': 1200,
                'real_volume': 120000,
                'spread': 2
            }
        ]
        
        mock_mt5.copy_rates_from_pos.return_value = mock_rates
        
        # Test
        bars = connector.get_bars("EURUSD", "M5", 2)
        
        assert len(bars) == 2
        assert bars[0].symbol == "EURUSD"
        assert bars[0].open == 1.08500
        assert bars[0].close == 1.08520
        assert bars[1].close == 1.08560
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_send_order_success(self, mock_mt5, connector):
        """Test successful order execution"""
        # Mock constants
        mock_mt5.TRADE_ACTION_DEAL = 1
        mock_mt5.ORDER_TYPE_BUY = 0
        mock_mt5.ORDER_FILLING_IOC = 2
        mock_mt5.TRADE_RETCODE_DONE = 10009
        mock_mt5.SYMBOL_TRADE_MODE_FULL = 4
        
        # Setup mocks for symbol_info and symbol_info_tick
        mock_symbol = MagicMock()
        mock_symbol.name = "EURUSD"
        mock_symbol.ask = 1.08520
        mock_symbol.bid = 1.08500
        mock_symbol.volume_min = 0.01
        mock_symbol.volume_max = 100.0
        mock_symbol.filling_mode = 1  # IOC
        mock_symbol.description = "Euro vs US Dollar"
        mock_symbol.currency_base = "EUR"
        mock_symbol.currency_profit = "USD"
        mock_symbol.digits = 5
        mock_symbol.point = 0.00001
        mock_symbol.volume_step = 0.01
        mock_symbol.trade_contract_size = 100000.0
        mock_symbol.spread = 2
        mock_symbol.trade_mode = 4
        
        mock_mt5.symbol_info.return_value = mock_symbol
        
        # Mock symbol_info_tick for price fetching
        mock_tick = Mock()
        mock_tick.bid = 1.08500
        mock_tick.ask = 1.08520
        mock_mt5.symbol_info_tick.return_value = mock_tick
        
        mock_result = MagicMock()
        mock_result.retcode = 10009  # TRADE_RETCODE_DONE
        mock_result.order = 123456
        mock_result.volume = 0.01
        mock_result.price = 1.08520
        mock_result.comment = "Success"
        mock_result.deal = 123457
        
        mock_mt5.order_send.return_value = mock_result
        
        # Test
        request = TradeRequest(
            symbol="EURUSD",
            action=OrderType.BUY,
            volume=0.01,
            sl=1.08320,
            tp=1.08920
        )
        
        result = connector.send_order(request)
        
        assert result.success is True
        assert result.order_ticket == 123456
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_send_order_invalid_volume(self, mock_mt5, connector):
        """Test order with invalid volume"""
        # Setup mock
        mock_symbol = MagicMock()
        mock_symbol.name = "EURUSD"
        mock_symbol.volume_min = 0.01
        mock_symbol.volume_max = 100.0
        
        mock_mt5.symbol_info.return_value = mock_symbol
        
        # Test with volume too small
        request = TradeRequest(
            symbol="EURUSD",
            action=OrderType.BUY,
            volume=0.001  # Too small
        )
        
        result = connector.send_order(request)
        
        assert result.success is False
        assert "Invalid volume" in result.error_message
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_get_positions(self, mock_mt5, connector):
        """Test getting open positions"""
        # Mock ORDER_TYPE constants
        mock_mt5.ORDER_TYPE_BUY = 0
        mock_mt5.ORDER_TYPE_SELL = 1
        
        # Setup mock positions
        mock_pos1 = MagicMock()
        mock_pos1.ticket = 123456
        mock_pos1.symbol = "EURUSD"
        mock_pos1.type = 0  # BUY
        mock_pos1.volume = 0.01
        mock_pos1.price_open = 1.08500
        mock_pos1.price_current = 1.08550
        mock_pos1.sl = 1.08300
        mock_pos1.tp = 1.08900
        mock_pos1.profit = 5.0
        mock_pos1.swap = 0.0
        mock_pos1.commission = -0.5
        mock_pos1.magic = 234000
        mock_pos1.comment = "Test"
        mock_pos1.time = 1700000000
        
        mock_mt5.positions_get.return_value = [mock_pos1]
        
        # Test
        positions = connector.get_positions()
        
        assert len(positions) == 1
        assert positions[0].ticket == 123456
        assert positions[0].symbol == "EURUSD"
        assert positions[0].profit == 5.0
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_close_position(self, mock_mt5, connector):
        """Test closing a position"""
        # Mock constants
        mock_mt5.ORDER_TYPE_BUY = 0
        mock_mt5.ORDER_TYPE_SELL = 1
        mock_mt5.TRADE_ACTION_DEAL = 1
        mock_mt5.TRADE_RETCODE_DONE = 10009
        
        # Mock positions_get to return position
        mock_pos = Mock()
        mock_pos.ticket = 123456
        mock_pos.symbol = "EURUSD"
        mock_pos.type = 0  # Buy
        mock_pos.volume = 0.01
        
        mock_mt5.positions_get.return_value = [mock_pos]
        
        # Mock symbol_info_tick for price
        mock_tick = Mock()
        mock_tick.bid = 1.08500
        mock_tick.ask = 1.08520
        mock_mt5.symbol_info_tick.return_value = mock_tick
        
        # Mock order_send result
        mock_result = MagicMock()
        mock_result.retcode = 10009
        mock_result.order = 123457
        
        mock_mt5.order_send.return_value = mock_result
        
        # Test - close_position only takes ticket parameter
        result = connector.close_position(ticket=123456)
        
        assert result.success is True
