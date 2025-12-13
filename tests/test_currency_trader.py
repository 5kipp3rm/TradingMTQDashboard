"""
Tests for CurrencyTrader module
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.trading.currency_trader import CurrencyTrader, CurrencyTraderConfig
from src.connectors.base import BaseMetaTraderConnector, OrderType, TradeRequest, TradeResult, SymbolInfo
from src.strategies.base import BaseStrategy, Signal, SignalType


class TestCurrencyTraderConfig(unittest.TestCase):
    """Test CurrencyTraderConfig dataclass"""
    
    def test_config_creation_with_defaults(self):
        """Test creating config with required params only"""
        mock_strategy = Mock(spec=BaseStrategy)
        
        config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=mock_strategy
        )
        
        self.assertEqual(config.symbol, "EURUSD")
        self.assertEqual(config.strategy, mock_strategy)
        self.assertEqual(config.risk_percent, 1.0)
        self.assertEqual(config.timeframe, 'M5')
        self.assertEqual(config.cooldown_seconds, 60)
        self.assertEqual(config.max_position_size, 1.0)
        self.assertEqual(config.min_position_size, 0.01)
    
    def test_config_creation_with_custom_values(self):
        """Test creating config with custom parameters"""
        mock_strategy = Mock(spec=BaseStrategy)
        
        config = CurrencyTraderConfig(
            symbol="GBPUSD",
            strategy=mock_strategy,
            risk_percent=2.0,
            timeframe='M15',
            cooldown_seconds=120,
            max_position_size=2.0,
            min_position_size=0.05
        )
        
        self.assertEqual(config.symbol, "GBPUSD")
        self.assertEqual(config.risk_percent, 2.0)
        self.assertEqual(config.timeframe, 'M15')
        self.assertEqual(config.cooldown_seconds, 120)


class TestCurrencyTraderInitialization(unittest.TestCase):
    """Test CurrencyTrader initialization"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connector = Mock(spec=BaseMetaTraderConnector)
        self.mock_strategy = Mock(spec=BaseStrategy)
        self.mock_strategy.name = "TestStrategy"
        
        self.config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=self.mock_strategy
        )
    
    def test_initialization_success(self):
        """Test successful trader initialization"""
        # Mock symbol info
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        trader = CurrencyTrader(self.config, self.mock_connector)
        
        self.assertEqual(trader.config, self.config)
        self.assertEqual(trader.connector, self.mock_connector)
        self.assertTrue(trader.is_valid)
        self.assertIsNone(trader.last_signal)
        self.assertIsNone(trader.last_trade_time)
        self.assertIsNone(trader.last_signal_type)
        self.assertEqual(trader.total_trades, 0)
        self.assertEqual(trader.successful_trades, 0)
        self.assertEqual(trader.failed_trades, 0)
    
    def test_initialization_invalid_symbol(self):
        """Test initialization with invalid symbol"""
        self.mock_connector.get_symbol_info.return_value = None
        
        trader = CurrencyTrader(self.config, self.mock_connector)
        
        self.assertFalse(trader.is_valid)
    
    def test_initialization_with_intelligent_manager(self):
        """Test initialization with intelligent manager"""
        mock_manager = Mock()
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        trader = CurrencyTrader(self.config, self.mock_connector, mock_manager)
        
        self.assertEqual(trader.intelligent_manager, mock_manager)


class TestCurrencyTraderCanTrade(unittest.TestCase):
    """Test can_trade cooldown logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connector = Mock(spec=BaseMetaTraderConnector)
        self.mock_strategy = Mock(spec=BaseStrategy)
        self.mock_strategy.name = "TestStrategy"
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        self.config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=self.mock_strategy,
            cooldown_seconds=60
        )
        
        self.trader = CurrencyTrader(self.config, self.mock_connector)
    
    def test_can_trade_no_previous_trade(self):
        """Test can_trade returns True when no previous trade"""
        self.assertTrue(self.trader.can_trade())
    
    def test_can_trade_cooldown_active(self):
        """Test can_trade returns False during cooldown"""
        self.trader.last_trade_time = datetime.now() - timedelta(seconds=30)
        
        self.assertFalse(self.trader.can_trade())
    
    def test_can_trade_cooldown_expired(self):
        """Test can_trade returns True after cooldown"""
        self.trader.last_trade_time = datetime.now() - timedelta(seconds=70)
        
        self.assertTrue(self.trader.can_trade())


class TestCurrencyTraderAnalyzeMarket(unittest.TestCase):
    """Test analyze_market method"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connector = Mock(spec=BaseMetaTraderConnector)
        self.mock_strategy = Mock(spec=BaseStrategy)
        self.mock_strategy.name = "TestStrategy"
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        self.config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=self.mock_strategy,
            use_position_trading=False  # Use strategy-based
        )
        
        self.trader = CurrencyTrader(self.config, self.mock_connector)
    
    def test_analyze_market_no_bars(self):
        """Test analyze_market returns None when no bars"""
        self.mock_connector.get_bars.return_value = None
        
        result = self.trader.analyze_market()
        
        self.assertIsNone(result)
    
    def test_analyze_market_with_strategy(self):
        """Test analyze_market using strategy"""
        # Mock bars
        mock_bars = [Mock(close=1.085, open=1.084, high=1.086, low=1.083) for _ in range(100)]
        self.mock_connector.get_bars.return_value = mock_bars
        
        # Mock strategy signal
        mock_signal = Signal(
            type=SignalType.BUY,
            symbol="EURUSD",
            timestamp=datetime.now(),
            price=1.085,
            stop_loss=1.075,
            take_profit=1.095,
            confidence=0.8,
            reason="Test signal"
        )
        self.mock_strategy.analyze.return_value = mock_signal
        
        result = self.trader.analyze_market()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.type, SignalType.BUY)
        self.mock_strategy.analyze.assert_called_once()


class TestCurrencyTraderShouldExecuteSignal(unittest.TestCase):
    """Test should_execute_signal logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connector = Mock(spec=BaseMetaTraderConnector)
        self.mock_strategy = Mock(spec=BaseStrategy)
        self.mock_strategy.name = "TestStrategy"
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        self.config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=self.mock_strategy
        )
        
        self.trader = CurrencyTrader(self.config, self.mock_connector)
        self.mock_connector.get_positions.return_value = []
    
    def test_should_execute_hold_signal(self):
        """Test HOLD signals are not executed"""
        signal = Signal(
            type=SignalType.HOLD,
            symbol="EURUSD",
            timestamp=datetime.now(),
            price=1.085,
            confidence=0.0,
            reason="Hold"
        )
        
        result = self.trader.should_execute_signal(signal)
        
        self.assertFalse(result)
    
    def test_should_execute_during_cooldown(self):
        """Test signals rejected during cooldown"""
        self.trader.last_trade_time = datetime.now() - timedelta(seconds=30)
        
        signal = Signal(
            type=SignalType.BUY,
            symbol="EURUSD",
            timestamp=datetime.now(),
            price=1.085,
            stop_loss=1.075,
            take_profit=1.095,
            confidence=0.8,
            reason="Test"
        )
        
        result = self.trader.should_execute_signal(signal)
        
        self.assertFalse(result)
    
    def test_should_execute_valid_signal(self):
        """Test valid signal is approved"""
        signal = Signal(
            type=SignalType.BUY,
            symbol="EURUSD",
            timestamp=datetime.now(),
            price=1.085,
            stop_loss=1.075,
            take_profit=1.095,
            confidence=0.8,
            reason="Test"
        )
        
        result = self.trader.should_execute_signal(signal)
        
        self.assertTrue(result)


class TestCurrencyTraderExecuteTrade(unittest.TestCase):
    """Test execute_trade method"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connector = Mock(spec=BaseMetaTraderConnector)
        self.mock_strategy = Mock(spec=BaseStrategy)
        self.mock_strategy.name = "TestStrategy"
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        self.config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=self.mock_strategy
        )
        
        self.trader = CurrencyTrader(self.config, self.mock_connector)
    
    @patch('src.connectors.account_utils.AccountUtils.risk_based_lot_size')
    def test_execute_trade_success(self, mock_lot_calc):
        """Test successful trade execution"""
        mock_lot_calc.return_value = 0.1
        
        signal = Signal(
            type=SignalType.BUY,
            symbol="EURUSD",
            timestamp=datetime.now(),
            price=1.085,
            stop_loss=1.075,
            take_profit=1.095,
            confidence=0.8,
            reason="Test"
        )
        
        # Mock successful trade result
        self.mock_connector.send_order.return_value = TradeResult(
            success=True,
            order_ticket=12345,
            price=1.085,
            error_message=""
        )
        
        result = self.trader.execute_trade(signal)
        
        self.assertTrue(result)
        self.assertEqual(self.trader.total_trades, 1)
        self.assertEqual(self.trader.successful_trades, 1)
        self.assertIsNotNone(self.trader.last_trade_time)
    
    @patch('src.connectors.account_utils.AccountUtils.risk_based_lot_size')
    def test_execute_trade_failure(self, mock_lot_calc):
        """Test failed trade execution"""
        mock_lot_calc.return_value = 0.1
        
        signal = Signal(
            type=SignalType.BUY,
            symbol="EURUSD",
            timestamp=datetime.now(),
            price=1.085,
            stop_loss=1.075,
            take_profit=1.095,
            confidence=0.8,
            reason="Test"
        )
        
        # Mock failed trade result
        self.mock_connector.send_order.return_value = TradeResult(
            success=False,
            order_ticket=0,
            price=0.0,
            error_message="Insufficient margin"
        )
        
        result = self.trader.execute_trade(signal)
        
        self.assertFalse(result)
        self.assertEqual(self.trader.failed_trades, 1)


class TestCurrencyTraderGetStatistics(unittest.TestCase):
    """Test get_statistics method"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connector = Mock(spec=BaseMetaTraderConnector)
        self.mock_strategy = Mock(spec=BaseStrategy)
        self.mock_strategy.name = "TestStrategy"
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        self.config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=self.mock_strategy
        )
        
        self.trader = CurrencyTrader(self.config, self.mock_connector)
    
    def test_get_statistics_no_trades(self):
        """Test statistics with no trades"""
        stats = self.trader.get_statistics()
        
        self.assertEqual(stats['symbol'], 'EURUSD')
        self.assertEqual(stats['total_trades'], 0)
        self.assertEqual(stats['successful'], 0)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['win_rate'], 0.0)
        self.assertIsNone(stats['last_trade'])
    
    def test_get_statistics_with_trades(self):
        """Test statistics with trades"""
        self.trader.total_trades = 10
        self.trader.successful_trades = 7
        self.trader.failed_trades = 3
        self.trader.last_trade_time = datetime.now()
        self.trader.last_signal_type = SignalType.BUY
        
        stats = self.trader.get_statistics()
        
        self.assertEqual(stats['total_trades'], 10)
        self.assertEqual(stats['successful'], 7)
        self.assertEqual(stats['failed'], 3)
        self.assertEqual(stats['win_rate'], 70.0)
        self.assertIsNotNone(stats['last_trade'])
        self.assertEqual(stats['last_signal_type'], 'BUY')


class TestCurrencyTraderRepr(unittest.TestCase):
    """Test __repr__ method"""
    
    def test_repr(self):
        """Test string representation"""
        mock_connector = Mock(spec=BaseMetaTraderConnector)
        mock_strategy = Mock(spec=BaseStrategy)
        mock_strategy.name = "TestStrategy"
        
        mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=mock_strategy
        )
        
        trader = CurrencyTrader(config, mock_connector)
        trader.total_trades = 5
        
        repr_str = repr(trader)
        
        self.assertIn("CurrencyTrader", repr_str)
        self.assertIn("EURUSD", repr_str)
        self.assertIn("TestStrategy", repr_str)
        self.assertIn("trades=5", repr_str)


if __name__ == '__main__':
    unittest.main()
