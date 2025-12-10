"""
Comprehensive tests for src.trading.position_manager module
Tests for PositionManager automatic SL/TP management
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.trading.position_manager import PositionManager
from src.connectors.base import Position, OrderType, SymbolInfo, TradeResult


class TestPositionManager:
    """Test suite for PositionManager"""
    
    @pytest.fixture
    def mock_connector(self):
        """Create mock connector"""
        connector = Mock()
        connector.get_positions.return_value = []
        return connector
    
    @pytest.fixture
    def position_manager(self, mock_connector):
        """Create position manager"""
        return PositionManager(mock_connector)
    
    @pytest.fixture
    def mock_symbol_info(self):
        """Create mock symbol info"""
        return SymbolInfo(
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
    
    def test_initialization(self, position_manager, mock_connector):
        """Test position manager initialization"""
        assert position_manager.connector == mock_connector
        assert position_manager.managed_positions == {}
    
    def test_add_position(self, position_manager):
        """Test adding position to management"""
        config = {'enable_breakeven': True, 'enable_trailing_stop': True}
        
        position_manager.add_position(123456, config)
        
        assert 123456 in position_manager.managed_positions
        assert position_manager.managed_positions[123456]['config'] == config
        assert position_manager.managed_positions[123456]['breakeven_set'] is False
        assert position_manager.managed_positions[123456]['partial_closed'] is False
    
    def test_remove_position(self, position_manager):
        """Test removing position from management"""
        position_manager.add_position(123456, {})
        
        position_manager.remove_position(123456)
        
        assert 123456 not in position_manager.managed_positions
    
    def test_get_managed_count(self, position_manager):
        """Test getting managed position count"""
        position_manager.add_position(123456, {})
        position_manager.add_position(123457, {})
        
        count = position_manager.get_managed_count()
        
        assert count == 2
    
    def test_get_position_state(self, position_manager):
        """Test getting position state"""
        config = {'test': 'value'}
        position_manager.add_position(123456, config)
        
        state = position_manager.get_position_state(123456)
        
        assert state is not None
        assert state['config'] == config
        assert 'added_time' in state
    
    def test_get_position_state_not_found(self, position_manager):
        """Test getting state for non-existent position"""
        state = position_manager.get_position_state(999999)
        
        assert state is None
    
    def test_cleanup_closed_positions(self, position_manager, mock_connector):
        """Test cleanup of closed positions"""
        # Add some positions
        position_manager.add_position(123456, {})
        position_manager.add_position(123457, {})
        position_manager.add_position(123458, {})
        
        # Mock only one position still open
        mock_position = Mock()
        mock_position.ticket = 123456
        mock_connector.get_positions.return_value = [mock_position]
        
        position_manager.cleanup_closed_positions()
        
        # Only the open position should remain
        assert 123456 in position_manager.managed_positions
        assert 123457 not in position_manager.managed_positions
        assert 123458 not in position_manager.managed_positions
    
    def test_process_all_positions_empty(self, position_manager, mock_connector):
        """Test processing when no positions"""
        mock_connector.get_positions.return_value = []
        
        config = {'enable_breakeven': True}
        position_manager.process_all_positions(config)
        
        # Should handle empty positions gracefully
        assert position_manager.get_managed_count() == 0
    
    def test_process_all_positions_auto_add(self, position_manager, mock_connector, mock_symbol_info):
        """Test auto-adding new positions"""
        mock_position = Position(
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
        )
        
        mock_connector.get_positions.return_value = [mock_position]
        mock_connector.get_symbol_info.return_value = mock_symbol_info
        
        config = {'enable_breakeven': False, 'enable_trailing_stop': False}
        position_manager.process_all_positions(config)
        
        # Position should be auto-added
        assert 123456 in position_manager.managed_positions
    
    @patch('src.trading.position_manager.mt5')
    def test_portfolio_target_close_all(self, mock_mt5, position_manager, mock_connector, mock_symbol_info):
        """Test portfolio target profit closes all positions"""
        mock_position1 = Position(
            ticket=123456,
            symbol="EURUSD",
            type=OrderType.BUY,
            volume=0.01,
            price_open=1.08500,
            price_current=1.08600,
            sl=1.08300,
            tp=1.08900,
            profit=60.0,
            time_open=datetime.now()
        )
        
        mock_position2 = Position(
            ticket=123457,
            symbol="GBPUSD",
            type=OrderType.SELL,
            volume=0.01,
            price_open=1.26800,
            price_current=1.26750,
            sl=1.27000,
            tp=1.26400,
            profit=45.0,
            time_open=datetime.now()
        )
        
        mock_connector.get_positions.return_value = [mock_position1, mock_position2]
        mock_connector.get_symbol_info.return_value = mock_symbol_info
        mock_connector.close_position.return_value = TradeResult(success=True)
        
        config = {
            'enable_portfolio_target': True,
            'portfolio_target_profit': 100.0,
            'portfolio_target_partial': False
        }
        
        position_manager.process_all_positions(config)
        
        # Should close all positions (total profit 105 >= 100)
        assert mock_connector.close_position.call_count == 2
    
    def test_breakeven_trigger(self, position_manager, mock_connector, mock_symbol_info):
        """Test breakeven SL adjustment"""
        # Add position to management
        position_manager.add_position(123456, {})
        
        # Create position with enough profit to trigger breakeven
        mock_position = Position(
            ticket=123456,
            symbol="EURUSD",
            type=OrderType.BUY,
            volume=0.01,
            price_open=1.08500,
            price_current=1.08700,  # 20 pips profit
            sl=1.08300,
            tp=1.08900,
            profit=20.0,
            time_open=datetime.now()
        )
        
        mock_connector.get_positions.return_value = [mock_position]
        mock_connector.get_symbol_info.return_value = mock_symbol_info
        mock_connector.modify_position.return_value = TradeResult(success=True)
        
        config = {
            'enable_breakeven': True,
            'breakeven_trigger_pips': 20,
            'breakeven_offset_pips': 2
        }
        
        position_manager.process_all_positions(config)
        
        # Should modify position to breakeven
        mock_connector.modify_position.assert_called_once()
        state = position_manager.get_position_state(123456)
        assert state['breakeven_set'] is True
    
    def test_trailing_stop_activation(self, position_manager, mock_connector, mock_symbol_info):
        """Test trailing stop activation"""
        position_manager.add_position(123456, {})
        
        # Position with enough profit to activate trailing
        mock_position = Position(
            ticket=123456,
            symbol="EURUSD",
            type=OrderType.BUY,
            volume=0.01,
            price_open=1.08500,
            price_current=1.08750,  # 25 pips profit
            sl=1.08300,
            tp=1.08900,
            profit=25.0,
            time_open=datetime.now()
        )
        
        mock_connector.get_positions.return_value = [mock_position]
        mock_connector.get_symbol_info.return_value = mock_symbol_info
        mock_connector.modify_position.return_value = TradeResult(success=True)
        
        config = {
            'enable_trailing_stop': True,
            'trailing_activation_pips': 20,
            'trailing_stop_pips': 15
        }
        
        position_manager.process_all_positions(config)
        
        state = position_manager.get_position_state(123456)
        assert state['trailing_active'] is True
    
    def test_no_processing_without_symbol_info(self, position_manager, mock_connector):
        """Test that processing skips positions without symbol info"""
        position_manager.add_position(123456, {})
        
        mock_position = Position(
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
        )
        
        mock_connector.get_positions.return_value = [mock_position]
        mock_connector.get_symbol_info.return_value = None  # No symbol info
        
        config = {'enable_breakeven': True}
        
        # Should not raise exception
        position_manager.process_all_positions(config)
    
    def test_highest_profit_tracking(self, position_manager, mock_connector, mock_symbol_info):
        """Test tracking of highest profit pips"""
        position_manager.add_position(123456, {})
        
        mock_position = Position(
            ticket=123456,
            symbol="EURUSD",
            type=OrderType.BUY,
            volume=0.01,
            price_open=1.08500,
            price_current=1.08600,  # 10 pips profit
            sl=1.08300,
            tp=1.08900,
            profit=10.0,
            time_open=datetime.now()
        )
        
        mock_connector.get_positions.return_value = [mock_position]
        mock_connector.get_symbol_info.return_value = mock_symbol_info
        
        config = {}
        position_manager.process_all_positions(config)
        
        state = position_manager.get_position_state(123456)
        assert state['highest_profit_pips'] > 0
    
    def test_sell_position_profit_calculation(self, position_manager, mock_connector, mock_symbol_info):
        """Test profit calculation for SELL positions"""
        position_manager.add_position(123456, {})
        
        # SELL position
        mock_position = Position(
            ticket=123456,
            symbol="EURUSD",
            type=OrderType.SELL,
            volume=0.01,
            price_open=1.08500,
            price_current=1.08400,  # Profit for SELL
            sl=1.08700,
            tp=1.08100,
            profit=10.0,
            time_open=datetime.now()
        )
        
        mock_connector.get_positions.return_value = [mock_position]
        mock_connector.get_symbol_info.return_value = mock_symbol_info
        
        config = {}
        position_manager.process_all_positions(config)
        
        # Should handle SELL position profit correctly
        state = position_manager.get_position_state(123456)
        assert state['highest_profit_pips'] > 0
