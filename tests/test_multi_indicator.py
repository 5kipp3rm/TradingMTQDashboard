"""
Tests for Multi-Indicator Strategy
"""
import unittest
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timedelta

from src.strategies.multi_indicator import MultiIndicatorStrategy
from src.strategies.base import SignalType
from src.connectors.base import OHLCBar


class TestMultiIndicatorStrategy(unittest.TestCase):
    """Test Multi-Indicator Strategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.symbol = "EURUSD"
        self.strategy = MultiIndicatorStrategy(
            symbol=self.symbol,
            timeframe="M5",
            ema_period=50,
            min_confirmations=3,
            sl_pips=25,
            tp_pips=50
        )
    
    def _create_bars(self, num_bars: int, base_price: float = 1.1000) -> list:
        """Helper to create test bars"""
        bars = []
        now = datetime.now()
        
        for i in range(num_bars):
            price = base_price + (i * 0.00001)
            
            bar = OHLCBar(
                symbol=self.symbol,
                timeframe="M5",
                time=now - timedelta(minutes=(num_bars - i) * 5),
                open=price - 0.00005,
                high=price + 0.00010,
                low=price - 0.00010,
                close=price,
                tick_volume=1000
            )
            bars.append(bar)
        
        return bars
    
    def test_initialization(self):
        """Test strategy initialization"""
        self.assertEqual(self.strategy.symbol, "EURUSD")
        self.assertEqual(self.strategy.ema_period, 50)
        self.assertEqual(self.strategy.min_confirmations, 3)
        self.assertEqual(self.strategy.sl_pips, 25)
        self.assertEqual(self.strategy.tp_pips, 50)
        self.assertTrue(self.strategy.enabled)
        self.assertIn("MultiIndicator", self.strategy.name)
    
    def test_insufficient_data(self):
        """Test with insufficient bars"""
        bars = self._create_bars(50)  # Less than ema_period + 30
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    def test_disabled_strategy(self):
        """Test disabled strategy returns None"""
        self.strategy.enabled = False
        bars = self._create_bars(100)
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    def test_buy_signal_with_confirmations(self):
        """Test BUY signal when enough bullish confirmations"""
        bars = self._create_bars(100, base_price=1.1000)
        
        # Mock all indicators to give bullish signals
        # MACD bullish
        self.strategy.macd.calculate = Mock(return_value=Mock(
            values=np.full(100, 0.0001),
            metadata={'histogram': np.full(100, 0.0001)}
        ))
        
        # RSI oversold
        self.strategy.rsi.calculate = Mock(return_value=Mock(
            values=np.full(100, 35.0)
        ))
        
        # Stochastic oversold
        self.strategy.stoch.calculate = Mock(return_value=Mock(
            values=np.full(100, 15.0)
        ))
        
        # EMA below price (uptrend)
        self.strategy.ema.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.0990)
        ))
        
        # BB at lower band
        self.strategy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000),
            metadata={
                'upper_band': np.full(100, 1.1020),
                'lower_band': np.full(100, 1.1005)
            }
        ))
        
        bars[-1].close = 1.1005
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, SignalType.BUY)
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertLess(signal.stop_loss, signal.price)
        self.assertGreater(signal.take_profit, signal.price)
        self.assertGreaterEqual(signal.confidence, 0.5)
        self.assertIn("bullish", signal.reason)
    
    def test_sell_signal_with_confirmations(self):
        """Test SELL signal when enough bearish confirmations"""
        bars = self._create_bars(100, base_price=1.1000)
        
        # Mock all indicators to give bearish signals
        # MACD bearish
        self.strategy.macd.calculate = Mock(return_value=Mock(
            values=np.full(100, -0.0001),
            metadata={'histogram': np.full(100, -0.0001)}
        ))
        
        # RSI overbought
        self.strategy.rsi.calculate = Mock(return_value=Mock(
            values=np.full(100, 75.0)
        ))
        
        # Stochastic overbought
        self.strategy.stoch.calculate = Mock(return_value=Mock(
            values=np.full(100, 85.0)
        ))
        
        # EMA above price (downtrend)
        self.strategy.ema.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1010)
        ))
        
        # BB at upper band
        self.strategy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000),
            metadata={
                'upper_band': np.full(100, 1.0995),
                'lower_band': np.full(100, 1.0980)
            }
        ))
        
        bars[-1].close = 1.0995
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, SignalType.SELL)
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertGreater(signal.stop_loss, signal.price)
        self.assertLess(signal.take_profit, signal.price)
        self.assertGreaterEqual(signal.confidence, 0.5)
        self.assertIn("bearish", signal.reason)
    
    def test_no_signal_insufficient_confirmations(self):
        """Test no signal when not enough confirmations"""
        bars = self._create_bars(100)
        
        # Only 2 bullish signals (need 3)
        self.strategy.macd.calculate = Mock(return_value=Mock(
            values=np.full(100, 0.0001),
            metadata={'histogram': np.full(100, 0.0001)}
        ))
        
        self.strategy.rsi.calculate = Mock(return_value=Mock(
            values=np.full(100, 35.0)
        ))
        
        # Rest neutral
        self.strategy.stoch.calculate = Mock(return_value=Mock(
            values=np.full(100, 50.0)
        ))
        
        self.strategy.ema.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000)
        ))
        
        self.strategy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000),
            metadata={
                'upper_band': np.full(100, 1.1020),
                'lower_band': np.full(100, 1.0980)
            }
        ))
        
        bars[-1].close = 1.1000
        
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    def test_no_signal_mixed_signals(self):
        """Test no signal when bullish and bearish signals are equal"""
        bars = self._create_bars(100)
        
        # Equal bullish and bearish
        self.strategy.macd.calculate = Mock(return_value=Mock(
            values=np.full(100, 0.0001),
            metadata={'histogram': np.full(100, 0.0001)}  # Bullish
        ))
        
        self.strategy.rsi.calculate = Mock(return_value=Mock(
            values=np.full(100, 75.0)  # Bearish (overbought)
        ))
        
        self.strategy.stoch.calculate = Mock(return_value=Mock(
            values=np.full(100, 15.0)  # Bullish (oversold)
        ))
        
        self.strategy.ema.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1010)  # Bearish (price below)
        ))
        
        self.strategy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000),
            metadata={
                'upper_band': np.full(100, 1.1020),
                'lower_band': np.full(100, 1.0980)
            }
        ))
        
        bars[-1].close = 1.1000
        
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    def test_no_signal_with_nan_values(self):
        """Test no signal when indicators return NaN"""
        bars = self._create_bars(100)
        
        # Return NaN
        self.strategy.macd.calculate = Mock(return_value=Mock(
            values=np.full(100, np.nan),
            metadata={'histogram': np.full(100, np.nan)}
        ))
        
        self.strategy.rsi.calculate = Mock(return_value=Mock(
            values=np.full(100, 35.0)
        ))
        
        self.strategy.stoch.calculate = Mock(return_value=Mock(
            values=np.full(100, 15.0)
        ))
        
        self.strategy.ema.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.0990)
        ))
        
        self.strategy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000),
            metadata={
                'upper_band': np.full(100, 1.1020),
                'lower_band': np.full(100, 1.0980)
            }
        ))
        
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    def test_sl_tp_calculation_eurusd(self):
        """Test SL/TP calculation for EURUSD"""
        bars = self._create_bars(100, base_price=1.1000)
        
        # Setup bullish confirmations
        self.strategy.macd.calculate = Mock(return_value=Mock(
            values=np.full(100, 0.0001),
            metadata={'histogram': np.full(100, 0.0001)}
        ))
        
        self.strategy.rsi.calculate = Mock(return_value=Mock(
            values=np.full(100, 35.0)
        ))
        
        self.strategy.stoch.calculate = Mock(return_value=Mock(
            values=np.full(100, 15.0)
        ))
        
        self.strategy.ema.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.0990)
        ))
        
        self.strategy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000),
            metadata={
                'upper_band': np.full(100, 1.1020),
                'lower_band': np.full(100, 1.0980)
            }
        ))
        
        bars[-1].close = 1.1000
        
        signal = self.strategy.analyze(bars)
        
        # EURUSD pip = 0.0001
        # SL = 25 pips = 0.0025
        # TP = 50 pips = 0.0050
        self.assertAlmostEqual(signal.price - signal.stop_loss, 0.0025, places=4)
        self.assertAlmostEqual(signal.take_profit - signal.price, 0.0050, places=4)
    
    def test_sl_tp_calculation_jpypair(self):
        """Test SL/TP calculation for JPY pairs"""
        strategy_jpy = MultiIndicatorStrategy(
            symbol="USDJPY",
            timeframe="M5",
            ema_period=50,
            min_confirmations=3,
            sl_pips=25,
            tp_pips=50
        )
        
        bars = self._create_bars(100, base_price=150.00)
        for bar in bars:
            bar.symbol = "USDJPY"
        
        # Setup bullish confirmations
        strategy_jpy.macd.calculate = Mock(return_value=Mock(
            values=np.full(100, 0.01),
            metadata={'histogram': np.full(100, 0.01)}
        ))
        
        strategy_jpy.rsi.calculate = Mock(return_value=Mock(
            values=np.full(100, 35.0)
        ))
        
        strategy_jpy.stoch.calculate = Mock(return_value=Mock(
            values=np.full(100, 15.0)
        ))
        
        strategy_jpy.ema.calculate = Mock(return_value=Mock(
            values=np.full(100, 149.00)
        ))
        
        strategy_jpy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 150.00),
            metadata={
                'upper_band': np.full(100, 151.00),
                'lower_band': np.full(100, 149.00)
            }
        ))
        
        bars[-1].close = 150.00
        
        signal = strategy_jpy.analyze(bars)
        
        # JPY pip = 0.01
        # SL = 25 pips = 0.25
        # TP = 50 pips = 0.50
        self.assertAlmostEqual(signal.price - signal.stop_loss, 0.25, places=2)
        self.assertAlmostEqual(signal.take_profit - signal.price, 0.50, places=2)
    
    def test_confidence_increases_with_confirmations(self):
        """Test confidence increases with more confirmations"""
        bars = self._create_bars(100)
        
        # Test with 3 confirmations
        self.strategy.min_confirmations = 3
        self.strategy.macd.calculate = Mock(return_value=Mock(
            values=np.full(100, 0.0001),
            metadata={'histogram': np.full(100, 0.0001)}
        ))
        self.strategy.rsi.calculate = Mock(return_value=Mock(values=np.full(100, 35.0)))
        self.strategy.stoch.calculate = Mock(return_value=Mock(values=np.full(100, 15.0)))
        self.strategy.ema.calculate = Mock(return_value=Mock(values=np.full(100, 1.0990)))
        self.strategy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000),
            metadata={'upper_band': np.full(100, 1.1020), 'lower_band': np.full(100, 1.0980)}
        ))
        bars[-1].close = 1.1000
        
        signal_3 = self.strategy.analyze(bars)
        
        # All 5 confirmations bullish
        bars[-1].close = 1.1005
        self.strategy.bb.calculate = Mock(return_value=Mock(
            values=np.full(100, 1.1000),
            metadata={'upper_band': np.full(100, 1.1020), 'lower_band': np.full(100, 1.1005)}
        ))
        
        signal_5 = self.strategy.analyze(bars)
        
        self.assertGreater(signal_5.confidence, signal_3.confidence)
    
    def test_strategy_name(self):
        """Test strategy name generation"""
        self.assertIn("MultiIndicator", self.strategy.name)
        self.assertIn("3conf", self.strategy.name)


if __name__ == '__main__':
    unittest.main()
