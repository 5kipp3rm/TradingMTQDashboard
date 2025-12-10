"""
Tests for RSI Strategy
"""
import unittest
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timedelta

from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.base import SignalType
from src.connectors.base import OHLCBar


class TestRSIStrategy(unittest.TestCase):
    """Test RSI Strategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.symbol = "EURUSD"
        self.strategy = RSIStrategy(
            symbol=self.symbol,
            timeframe="M5",
            rsi_period=14,
            oversold=30,
            overbought=70,
            sl_atr_multiplier=2.0
        )
    
    def _create_bars(self, num_bars: int, base_price: float = 1.1000, volatility: float = 0.0010) -> list:
        """Helper to create test bars"""
        bars = []
        now = datetime.now()
        
        for i in range(num_bars):
            price = base_price + np.sin(i / 5) * volatility
            
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
        self.assertEqual(self.strategy.rsi_period, 14)
        self.assertEqual(self.strategy.oversold, 30)
        self.assertEqual(self.strategy.overbought, 70)
        self.assertEqual(self.strategy.sl_atr_multiplier, 2.0)
        self.assertTrue(self.strategy.enabled)
    
    def test_insufficient_data(self):
        """Test with insufficient bars"""
        bars = self._create_bars(10)  # Not enough
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    def test_disabled_strategy(self):
        """Test disabled strategy returns None"""
        self.strategy.enabled = False
        bars = self._create_bars(50)
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    @patch('src.strategies.rsi_strategy.RSI')
    def test_buy_signal_oversold_crossover(self, mock_rsi_class):
        """Test BUY signal when RSI crosses above oversold"""
        bars = self._create_bars(50)
        
        # Mock RSI indicator
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 35.0)
        rsi_result.values[-1] = 32.0  # Current RSI
        rsi_result.signals = np.zeros(50)
        rsi_result.signals[-1] = 1  # Bullish signal (crossed above oversold)
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, SignalType.BUY)
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertLess(signal.sl, signal.price)
        self.assertGreater(signal.tp, signal.price)
        self.assertIn("crossed above", signal.reason)
        self.assertGreaterEqual(signal.confidence, 0.5)
    
    @patch('src.strategies.rsi_strategy.RSI')
    def test_sell_signal_overbought_crossover(self, mock_rsi_class):
        """Test SELL signal when RSI crosses below overbought"""
        bars = self._create_bars(50)
        
        # Mock RSI indicator
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 65.0)
        rsi_result.values[-1] = 72.0  # Current RSI
        rsi_result.signals = np.zeros(50)
        rsi_result.signals[-1] = -1  # Bearish signal (crossed below overbought)
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, SignalType.SELL)
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertGreater(signal.sl, signal.price)
        self.assertLess(signal.tp, signal.price)
        self.assertIn("crossed below", signal.reason)
        self.assertGreaterEqual(signal.confidence, 0.5)
    
    @patch('src.strategies.rsi_strategy.RSI')
    def test_no_signal_when_rsi_neutral(self, mock_rsi_class):
        """Test no signal when RSI is neutral"""
        bars = self._create_bars(50)
        
        # Mock RSI - no signal
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 50.0)
        rsi_result.signals = np.zeros(50)  # No signal
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNone(signal)
    
    @patch('src.strategies.rsi_strategy.RSI')
    def test_no_signal_when_nan_rsi(self, mock_rsi_class):
        """Test no signal when RSI is NaN"""
        bars = self._create_bars(50)
        
        # Mock RSI with NaN
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, np.nan)
        rsi_result.signals = np.zeros(50)
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNone(signal)
    
    @patch('src.strategies.rsi_strategy.RSI')
    def test_atr_calculation_for_sl_tp(self, mock_rsi_class):
        """Test ATR-based stop loss and take profit calculation"""
        bars = self._create_bars(50, base_price=1.1000)
        
        # Set varying high/low for ATR calculation
        for i, bar in enumerate(bars):
            bar.high = bar.close + 0.0010
            bar.low = bar.close - 0.0010
        
        # Mock RSI
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 35.0)
        rsi_result.signals = np.zeros(50)
        rsi_result.signals[-1] = 1  # Buy signal
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        # Verify SL/TP are set based on ATR
        self.assertIsNotNone(signal.sl)
        self.assertIsNotNone(signal.tp)
        # TP should be 1.5x SL distance (1.5:1 R:R)
        sl_distance = signal.price - signal.sl
        tp_distance = signal.tp - signal.price
        self.assertAlmostEqual(tp_distance / sl_distance, 1.5, places=1)
    
    def test_calculate_confidence_buy_deep_oversold(self):
        """Test confidence for deeply oversold BUY signal"""
        # Very low RSI = higher confidence
        confidence = self.strategy._calculate_confidence(rsi=20.0, direction="BUY")
        self.assertGreater(confidence, 0.7)
        
        # Barely oversold = lower confidence
        confidence2 = self.strategy._calculate_confidence(rsi=29.0, direction="BUY")
        self.assertGreater(confidence, confidence2)
    
    def test_calculate_confidence_sell_deep_overbought(self):
        """Test confidence for deeply overbought SELL signal"""
        # Very high RSI = higher confidence
        confidence = self.strategy._calculate_confidence(rsi=80.0, direction="SELL")
        self.assertGreater(confidence, 0.7)
        
        # Barely overbought = lower confidence
        confidence2 = self.strategy._calculate_confidence(rsi=71.0, direction="SELL")
        self.assertGreater(confidence, confidence2)
    
    def test_confidence_bounds(self):
        """Test confidence stays within 0.5-1.0"""
        # Extreme cases
        conf1 = self.strategy._calculate_confidence(rsi=0.0, direction="BUY")
        self.assertGreaterEqual(conf1, 0.5)
        self.assertLessEqual(conf1, 1.0)
        
        conf2 = self.strategy._calculate_confidence(rsi=100.0, direction="SELL")
        self.assertGreaterEqual(conf2, 0.5)
        self.assertLessEqual(conf2, 1.0)
    
    @patch('src.strategies.rsi_strategy.RSI')
    def test_default_atr_when_insufficient_data(self, mock_rsi_class):
        """Test fallback to default ATR when insufficient bars"""
        bars = self._create_bars(15)  # Just enough for RSI, not for ATR
        
        # Mock RSI
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(15, 35.0)
        rsi_result.signals = np.zeros(15)
        rsi_result.signals[-1] = 1  # Buy signal
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        signal = self.strategy.analyze(bars)
        
        # Should still generate signal with default ATR
        self.assertIsNotNone(signal)
        self.assertIsNotNone(signal.sl)
        self.assertIsNotNone(signal.tp)
    
    def test_strategy_name(self):
        """Test strategy name generation"""
        self.assertIn("RSI", self.strategy.name)
        self.assertIn("14", self.strategy.name)
        self.assertIn("30", self.strategy.name)
        self.assertIn("70", self.strategy.name)


if __name__ == '__main__':
    unittest.main()
