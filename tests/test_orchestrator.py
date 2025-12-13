"""
Tests for Multi-Currency Orchestrator
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.trading.orchestrator import MultiCurrencyOrchestrator
from src.trading.currency_trader import CurrencyTraderConfig
from src.connectors.base import Position, OrderType, SymbolInfo


class TestMultiCurrencyOrchestrator(unittest.TestCase):
    """Test MultiCurrencyOrchestrator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connector = Mock()
        self.orchestrator = MultiCurrencyOrchestrator(
            connector=self.mock_connector,
            max_concurrent_trades=10,
            portfolio_risk_percent=5.0,
            use_intelligent_manager=False  # Disable AI for simpler testing
        )
    
    def test_initialization(self):
        """Test orchestrator initialization"""
        self.assertEqual(self.orchestrator.connector, self.mock_connector)
        self.assertEqual(self.orchestrator.max_concurrent_trades, 10)
        self.assertEqual(self.orchestrator.portfolio_risk_percent, 5.0)
        self.assertEqual(len(self.orchestrator.traders), 0)
        self.assertIsNotNone(self.orchestrator.position_manager)
    
    def test_initialization_with_intelligent_manager(self):
        """Test initialization with intelligent manager enabled"""
        orch = MultiCurrencyOrchestrator(
            connector=self.mock_connector,
            use_intelligent_manager=True
        )
        
        self.assertIsNotNone(orch.intelligent_manager)
    
    def test_add_currency_success(self):
        """Test adding a currency pair"""
        from src.strategies.base import BaseStrategy
        
        mock_strategy = Mock(spec=BaseStrategy)
        mock_strategy.name = "TestStrategy"
        
        config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=mock_strategy,
            timeframe="M5",
            risk_percent=1.0
        )
        
        # Mock symbol info
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
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
        
        trader = self.orchestrator.add_currency(config)
        
        self.assertIsNotNone(trader)
        self.assertEqual(len(self.orchestrator.traders), 1)
        self.assertIn("EURUSD", self.orchestrator.traders)
    
    def test_add_currency_duplicate(self):
        """Test adding duplicate currency returns None"""
        from src.strategies.base import BaseStrategy
        
        mock_strategy = Mock(spec=BaseStrategy)
        mock_strategy.name = "TestStrategy"
        
        config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=mock_strategy,
            timeframe="M5"
        )
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        # Add first time
        self.orchestrator.add_currency(config)
        
        # Try to add again
        result = self.orchestrator.add_currency(config)
        
        self.assertIsNone(result)
        self.assertEqual(len(self.orchestrator.traders), 1)
    
    def test_remove_currency_success(self):
        """Test removing a currency pair"""
        from src.strategies.base import BaseStrategy
        
        mock_strategy = Mock(spec=BaseStrategy)
        mock_strategy.name = "TestStrategy"
        
        config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=mock_strategy,
            timeframe="M5"
        )
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        self.orchestrator.add_currency(config)
        
        result = self.orchestrator.remove_currency("EURUSD")
        
        self.assertTrue(result)
        self.assertEqual(len(self.orchestrator.traders), 0)
    
    def test_remove_currency_not_found(self):
        """Test removing non-existent currency returns False"""
        result = self.orchestrator.remove_currency("GBPUSD")
        
        self.assertFalse(result)
    
    def test_get_open_positions_count(self):
        """Test getting open positions count"""
        # Mock positions
        mock_positions = [
            Mock(ticket=1, symbol="EURUSD"),
            Mock(ticket=2, symbol="GBPUSD"),
            Mock(ticket=3, symbol="EURUSD")
        ]
        
        self.mock_connector.get_positions.return_value = mock_positions
        
        count = self.orchestrator.get_open_positions_count()
        
        self.assertEqual(count, 3)
    
    def test_get_open_positions_count_empty(self):
        """Test getting count when no positions"""
        self.mock_connector.get_positions.return_value = []
        
        count = self.orchestrator.get_open_positions_count()
        
        self.assertEqual(count, 0)
    
    def test_can_open_new_position_true(self):
        """Test can open position when under limit"""
        self.mock_connector.get_positions.return_value = [
            Mock(ticket=1),
            Mock(ticket=2)
        ]
        
        result = self.orchestrator.can_open_new_position()
        
        self.assertTrue(result)
    
    def test_can_open_new_position_false(self):
        """Test can open position when at limit"""
        # Create 10 mock positions (matching max_concurrent_trades)
        mock_positions = [Mock(ticket=i) for i in range(10)]
        self.mock_connector.get_positions.return_value = mock_positions
        
        result = self.orchestrator.can_open_new_position()
        
        self.assertFalse(result)
    
    def test_get_trader_exists(self):
        """Test getting existing trader"""
        from src.strategies.base import BaseStrategy
        
        mock_strategy = Mock(spec=BaseStrategy)
        mock_strategy.name = "TestStrategy"
        
        config = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=mock_strategy,
            timeframe="M5"
        )
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )
        
        self.orchestrator.add_currency(config)
        
        trader = self.orchestrator.get_trader("EURUSD")
        
        self.assertIsNotNone(trader)
    
    def test_get_trader_not_exists(self):
        """Test getting non-existent trader returns None"""
        trader = self.orchestrator.get_trader("GBPUSD")
        
        self.assertIsNone(trader)
    
    def test_len_operator(self):
        """Test __len__ returns trader count"""
        from src.strategies.base import BaseStrategy
        
        mock_strategy = Mock(spec=BaseStrategy)
        mock_strategy.name = "TestStrategy"
        
        self.mock_connector.get_symbol_info.return_value = SymbolInfo(
            name="EURUSD", description="", base_currency="EUR",
            quote_currency="USD", digits=5, point=0.00001,
            volume_min=0.01, volume_max=100.0, volume_step=0.01,
            contract_size=100000.0, bid=1.08500, ask=1.08520,
            spread=0.00020, trade_allowed=True
        )

        config1 = CurrencyTraderConfig(
            symbol="EURUSD",
            strategy=mock_strategy,
            timeframe="M5"
        )
        
        config2 = CurrencyTraderConfig(
            symbol="GBPUSD",
            strategy=mock_strategy,
            timeframe="M5"
        )

        self.orchestrator.add_currency(config1)
        self.assertEqual(len(self.orchestrator), 1)

        self.orchestrator.add_currency(config2)
        self.assertEqual(len(self.orchestrator), 2)
    
    def test_repr(self):
        """Test __repr__ returns string representation"""
        repr_str = repr(self.orchestrator)

        self.assertIsInstance(repr_str, str)
        self.assertIn("MultiCurrencyOrchestrator", repr_str)
        self.assertIn("cycles=0", repr_str)
        self.assertIn("currencies=[]", repr_str)
    
    def test_get_all_statistics(self):
        """Test getting all statistics"""
        stats = self.orchestrator.get_all_statistics()
        
        # With no traders, should return empty dict
        self.assertIsInstance(stats, dict)
        self.assertEqual(len(stats), 0)


if __name__ == '__main__':
    unittest.main()
