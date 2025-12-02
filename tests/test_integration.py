"""
Integration Tests
Test complete workflows end-to-end
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.connectors.factory import ConnectorFactory
from src.connectors.base import PlatformType, OrderType, AccountInfo, Position
from src.trading.controller import TradingController
from src.strategies.simple_ma import SimpleMovingAverageStrategy


class TestIntegration:
    """Integration test suite"""
    
    def teardown_method(self):
        """Cleanup after each test"""
        ConnectorFactory.disconnect_all()
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_full_trading_workflow(self, mock_mt5):
        """Test complete trading workflow from connection to trade execution"""
        # Mock MT5 constants
        mock_mt5.TRADE_ACTION_DEAL = 1
        mock_mt5.ORDER_TYPE_BUY = 0
        mock_mt5.ORDER_FILLING_IOC = 2
        mock_mt5.TRADE_RETCODE_DONE = 10009
        mock_mt5.SYMBOL_TRADE_MODE_FULL = 4
        
        # Setup mocks
        mock_mt5.initialize.return_value = True
        
        mock_account = MagicMock()
        mock_account.login = 12345
        mock_account.server = "Demo"
        mock_account.name = "Test"
        mock_account.company = "Broker"
        mock_account.currency = "USD"
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.profit = 0.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.leverage = 100
        mock_account.trade_allowed = True
        
        mock_mt5.account_info.return_value = mock_account
        
        mock_symbol = MagicMock()
        mock_symbol.name = "EURUSD"
        mock_symbol.ask = 1.08520
        mock_symbol.bid = 1.08500
        mock_symbol.volume_min = 0.01
        mock_symbol.volume_max = 100.0
        mock_symbol.filling_mode = 1
        mock_symbol.description = "Euro vs US Dollar"
        mock_symbol.currency_base = "EUR"
        mock_symbol.currency_profit = "USD"
        mock_symbol.digits = 5
        mock_symbol.point = 0.00001
        mock_symbol.volume_step = 0.01
        mock_symbol.trade_contract_size = 100000.0
        mock_symbol.spread = 2
        mock_symbol.trade_mode = 4  # SYMBOL_TRADE_MODE_FULL
        
        mock_mt5.symbol_info.return_value = mock_symbol
        
        # Mock symbol_info_tick for price fetching
        mock_tick = Mock()
        mock_tick.bid = 1.08500
        mock_tick.ask = 1.08520
        mock_mt5.symbol_info_tick.return_value = mock_tick
        
        mock_result = MagicMock()
        mock_result.retcode = 10009
        mock_result.order = 123456
        mock_result.volume = 0.01
        mock_result.price = 1.08520
        mock_result.comment = "Success"
        mock_result.deal = 123457
        
        mock_mt5.order_send.return_value = mock_result
        mock_mt5.positions_get.return_value = []
        
        # 1. Create connector
        connector = ConnectorFactory.create_connector(PlatformType.MT5, "test")
        assert connector is not None
        
        # 2. Connect
        success = connector.connect(login=12345, password="test", server="demo")
        assert success is True
        
        # 3. Get account info
        account = connector.get_account_info()
        assert account is not None
        assert account.balance == 10000.0
        
        # 4. Create trading controller
        controller = TradingController(connector)
        
        # 5. Execute trade
        result = controller.execute_trade(
            symbol="EURUSD",
            action=OrderType.BUY,
            volume=0.01,
            sl=1.08320,
            tp=1.08920
        )
        
        assert result.success is True
        assert result.order_ticket == 123456
        
        # 6. Get positions
        positions = controller.get_open_positions()
        assert isinstance(positions, list)
        
        # 7. Disconnect
        connector.disconnect()
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_strategy_integration(self, mock_mt5):
        """Test strategy integration with connector"""
        # Setup connector mock
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        
        # Create connector
        connector = ConnectorFactory.create_connector(PlatformType.MT5, "strategy_test")
        connector.connect(login=12345, password="test", server="demo")
        
        # Create strategy
        strategy = SimpleMovingAverageStrategy()
        
        assert strategy.get_name() == "Simple MA Crossover"
        assert strategy.is_enabled() is True
        
        # Create controller
        controller = TradingController(connector)
        
        # Verify integration
        assert controller.connector == connector
        
        connector.disconnect()
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_multi_instance_integration(self, mock_mt5):
        """Test multiple connector instances"""
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        
        # Create multiple connectors
        conn1 = ConnectorFactory.create_connector(PlatformType.MT5, "instance1")
        conn2 = ConnectorFactory.create_connector(PlatformType.MT5, "instance2")
        
        assert conn1.get_instance_id() == "instance1"
        assert conn2.get_instance_id() == "instance2"
        assert conn1 is not conn2
        
        # Connect both
        conn1.connect(login=12345, password="test1", server="demo1")
        conn2.connect(login=67890, password="test2", server="demo2")
        
        # Create separate controllers
        controller1 = TradingController(conn1)
        controller2 = TradingController(conn2)
        
        assert controller1.connector != controller2.connector
        
        # Cleanup
        ConnectorFactory.disconnect_all()
        assert ConnectorFactory.get_instance_count() == 0
    
    @patch('src.connectors.mt5_connector.mt5')
    def test_error_recovery(self, mock_mt5):
        """Test error handling and recovery"""
        # Simulate connection failure
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (1, "Init failed")
        
        connector = ConnectorFactory.create_connector(PlatformType.MT5, "error_test")
        
        # Should handle connection failure gracefully
        success = connector.connect(login=12345, password="test", server="demo")
        assert success is False
        
        # Now simulate successful connection
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        
        # Retry connection
        success = connector.connect(login=12345, password="test", server="demo")
        assert success is True
        
        connector.disconnect()
    
    def test_configuration_integration(self):
        """Test configuration loading and usage"""
        from src.utils.config import Config
        
        config = Config()
        
        # Test getting values
        value = config.get('nonexistent', 'default')
        assert value == 'default'
        
        # Test MT5 credentials (should use defaults if not set)
        credentials = config.get_mt5_credentials()
        assert 'login' in credentials
        assert 'password' in credentials
        assert 'server' in credentials
