"""
Tests for Trading Controller
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.trading.controller import TradingController
from src.connectors.base import (
    OrderType, AccountInfo, Position, SymbolInfo, 
    TradeResult, ConnectionStatus
)


class TestTradingController:
    """Test suite for TradingController"""
    
    @pytest.fixture
    def mock_connector(self):
        """Create mock connector"""
        connector = Mock()
        connector.is_connected.return_value = True
        connector.get_connection_status.return_value = ConnectionStatus.CONNECTED
        return connector
    
    @pytest.fixture
    def controller(self, mock_connector):
        """Create controller with mock connector"""
        return TradingController(mock_connector)
    
    def test_initialization(self, controller, mock_connector):
        """Test controller initialization"""
        assert controller.connector == mock_connector
    
    def test_execute_trade_success(self, controller, mock_connector):
        """Test successful trade execution"""
        # Setup mocks - SymbolInfo fields based on dataclass: name, description, base_currency, etc
        mock_symbol = SymbolInfo(
            name="EURUSD",
            description="Euro vs US Dollar",
            base_currency="EUR",
            quote_currency="USD",
            digits=5,
            point=0.00001,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            contract_size=100000.0,
            bid=1.08500,
            ask=1.08520,
            spread=0.00020,
            trade_allowed=True
        )
        
        mock_connector.get_symbol_info.return_value = mock_symbol
        
        # Mock account info for margin check
        mock_account = Mock()
        mock_account.margin_free = 5000.0
        mock_connector.get_account_info.return_value = mock_account
        
        mock_result = TradeResult(
            success=True,
            order_ticket=123456,
            volume=0.01,
            price=1.08520,
            error_code=0,
            error_message=""
        )
        
        mock_connector.send_order.return_value = mock_result
        
        # Test
        result = controller.execute_trade(
            symbol="EURUSD",
            action=OrderType.BUY,
            volume=0.01,
            sl=1.08320,
            tp=1.08920
        )
        
        assert result.success is True
        assert result.order_ticket == 123456
        mock_connector.send_order.assert_called_once()
    
    def test_execute_trade_not_connected(self, controller, mock_connector):
        """Test trade execution when not connected"""
        mock_connector.is_connected.return_value = False
        
        result = controller.execute_trade(
            symbol="EURUSD",
            action=OrderType.BUY,
            volume=0.01
        )
        
        assert result.success is False
        assert "not connected" in result.error_message.lower()
    
    def test_execute_trade_symbol_not_found(self, controller, mock_connector):
        """Test trade execution with invalid symbol"""
        mock_connector.get_symbol_info.return_value = None
        
        result = controller.execute_trade(
            symbol="INVALID",
            action=OrderType.BUY,
            volume=0.01
        )
        
        assert result.success is False
        assert "not found" in result.error_message.lower()
    
    def test_execute_trade_invalid_volume(self, controller, mock_connector):
        """Test trade execution with invalid volume"""
        mock_symbol = SymbolInfo(
            name="EURUSD",
            description="",
            base_currency="EUR",
            quote_currency="USD",
            digits=5,
            point=0.00001,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            contract_size=100000.0,
            bid=1.08500,
            ask=1.08520,
            spread=0.00020,
            trade_allowed=True
        )
        
        mock_connector.get_symbol_info.return_value = mock_symbol
        
        # Test volume too small
        result = controller.execute_trade(
            symbol="EURUSD",
            action=OrderType.BUY,
            volume=0.001  # Too small
        )
        
        assert result.success is False
        assert "volume" in result.error_message.lower()
    
    def test_close_trade_success(self, controller, mock_connector):
        """Test successful trade closure"""
        mock_result = TradeResult(
            success=True,
            order_ticket=123457,
            volume=0.01,
            price=1.08550,
            error_code=0,
            error_message=""
        )
        
        mock_connector.close_position.return_value = mock_result
        
        # close_trade only takes ticket parameter
        result = controller.close_trade(ticket=123456)
        
        assert result.success is True
        mock_connector.close_position.assert_called_once_with(123456)
    
    def test_get_open_positions(self, controller, mock_connector):
        """Test getting open positions"""
        mock_positions = [
            Position(
                ticket=123456,
                symbol="EURUSD",
                type=OrderType.BUY,
                volume=0.01,
                price_open=1.08500,
                price_current=1.08550,
                sl=1.08300,
                tp=1.08900,
                profit=5.0,
                time_open=datetime.now()
            ),
            Position(
                ticket=123457,
                symbol="GBPUSD",
                type=OrderType.SELL,
                volume=0.01,
                price_open=1.26800,
                price_current=1.26750,
                sl=1.27000,
                tp=1.26400,
                profit=5.0,
                time_open=datetime.now()
            )
        ]
        
        mock_connector.get_positions.return_value = mock_positions
        
        positions = controller.get_open_positions()
        
        assert len(positions) == 2
        assert positions[0].symbol == "EURUSD"
        assert positions[1].symbol == "GBPUSD"
    
    def test_get_account_summary(self, controller, mock_connector):
        """Test getting account summary"""
        mock_positions = [
            Position(
                ticket=123456,
                symbol="EURUSD",
                type=OrderType.BUY,
                volume=0.01,
                price_open=1.08500,
                price_current=1.08550,
                sl=1.08300,
                tp=1.08900,
                profit=5.0,
                time_open=datetime.now()
            ),
            Position(
                ticket=123457,
                symbol="GBPUSD",
                type=OrderType.SELL,
                volume=0.02,
                price_open=1.26800,
                price_current=1.26750,
                sl=1.27000,
                tp=1.26400,
                profit=10.0,
                time_open=datetime.now()
            )
        ]
        
        mock_connector.get_positions.return_value = mock_positions
        
        # Mock account info
        mock_account = Mock()
        mock_account.balance = 10000.0
        mock_account.equity = 10015.0
        mock_account.profit = 15.0
        mock_account.margin = 100.0
        mock_account.margin_free = 9915.0
        mock_account.margin_level = 10015.0
        mock_connector.get_account_info.return_value = mock_account
        
        summary = controller.get_account_summary()
        
        assert summary['open_positions'] == 2
        assert summary['total_volume'] == 0.03
        assert summary['balance'] == 10000.0
        assert summary['equity'] == 10015.0
        assert summary['profit'] == 15.0
    
    def test_close_all_positions(self, controller, mock_connector):
        """Test closing all positions"""
        mock_positions = [
            Position(
                ticket=123456,
                symbol="EURUSD",
                type=OrderType.BUY,
                volume=0.01,
                price_open=1.08500,
                price_current=1.08550,
                sl=1.08300,
                tp=1.08900,
                profit=5.0,
                time_open=datetime.now()
            ),
            Position(
                ticket=123457,
                symbol="GBPUSD",
                type=OrderType.SELL,
                volume=0.01,
                price_open=1.26800,
                price_current=1.26750,
                sl=1.27000,
                tp=1.26400,
                profit=5.0,
                time_open=datetime.now()
            )
        ]
        
        mock_connector.get_positions.return_value = mock_positions
        
        mock_result_success = TradeResult(
            success=True,
            order_ticket=123458,
            volume=0.01,
            price=1.08550,
            error_code=0,
            error_message=""
        )
        
        mock_connector.close_position.return_value = mock_result_success
        
        results = controller.close_all_positions()
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert mock_connector.close_position.call_count == 2
