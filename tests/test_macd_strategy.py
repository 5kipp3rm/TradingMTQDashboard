"""
Tests for MACD Strategy
"""
import unittest
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timedelta

from src.strategies.macd_strategy import MACDStrategy
from src.strategies.base import SignalType
from src.connectors.base import OHLCBar


class TestMACDStrategy(unittest.TestCase):
    """Test MACD Strategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.symbol = "EURUSD"
        self.strategy = MACDStrategy(
            symbol=self.symbol,
            timeframe="M5",
            fast_period=12,
            slow_period=26,
            signal_period=9,
            sl_pips=20,
            tp_pips=40
        )
    
    def _create_bars(self, num_bars: int, base_price: float = 1.1000, trend: str = "neutral") -> list:
        """Helper to create test bars with trend"""
        bars = []
        now = datetime.now()
        
        for i in range(num_bars):
            if trend == "up":
                price = base_price + (i * 0.00005)
            elif trend == "down":
                price = base_price - (i * 0.00005)
            else:
                price = base_price + np.sin(i / 5) * 0.0010
            
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
        self.assertEqual(self.strategy.fast_period, 12)
        self.assertEqual(self.strategy.slow_period, 26)
        self.assertEqual(self.strategy.signal_period, 9)
        self.assertEqual(self.strategy.sl_pips, 20)
        self.assertEqual(self.strategy.tp_pips, 40)
        self.assertTrue(self.strategy.enabled)
    
    def test_insufficient_data(self):
        """Test with insufficient bars"""
        bars = self._create_bars(20)  # Not enough
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    def test_disabled_strategy(self):
        """Test disabled strategy returns None"""
        self.strategy.enabled = False
        bars = self._create_bars(50)
        signal = self.strategy.analyze(bars)
        self.assertIsNone(signal)
    
    @patch('src.strategies.macd_strategy.MACD')
    def test_buy_signal_bullish_crossover(self, mock_macd_class):
        """Test BUY signal on bullish MACD crossover"""
        bars = self._create_bars(50, trend="up")
        
        # Mock MACD indicator
        mock_macd = Mock()
        macd_result = Mock()
        macd_result.values = np.linspace(-0.0002, 0.0002, 50)  # MACD line
        macd_result.signals = np.zeros(50)
        macd_result.signals[-1] = 1  # Bullish crossover
        macd_result.metadata = {
            'histogram': np.linspace(-0.0001, 0.0001, 50),
            'signal_line': np.linspace(-0.00015, 0.00015, 50)
        }
        mock_macd.calculate.return_value = macd_result
        self.strategy.macd_indicator = mock_macd
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, SignalType.BUY)
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertLess(signal.stop_loss, signal.price)
        self.assertGreater(signal.take_profit, signal.price)
        self.assertIn("bullish crossover", signal.reason)
        self.assertIn("Histogram", signal.reason)
    
    @patch('src.strategies.macd_strategy.MACD')
    def test_sell_signal_bearish_crossover(self, mock_macd_class):
        """Test SELL signal on bearish MACD crossover"""
        bars = self._create_bars(50, trend="down")
        
        # Mock MACD indicator
        mock_macd = Mock()
        macd_result = Mock()
        macd_result.values = np.linspace(0.0002, -0.0002, 50)  # MACD line
        macd_result.signals = np.zeros(50)
        macd_result.signals[-1] = -1  # Bearish crossover
        macd_result.metadata = {
            'histogram': np.linspace(0.0001, -0.0001, 50),
            'signal_line': np.linspace(0.00015, -0.00015, 50)
        }
        mock_macd.calculate.return_value = macd_result
        self.strategy.macd_indicator = mock_macd
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, SignalType.SELL)
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertGreater(signal.stop_loss, signal.price)
        self.assertLess(signal.take_profit, signal.price)
        self.assertIn("bearish crossover", signal.reason)
    
    @patch('src.strategies.macd_strategy.MACD')
    def test_no_signal_when_no_crossover(self, mock_macd_class):
        """Test no signal when no crossover occurs"""
        bars = self._create_bars(50)
        
        # Mock MACD - no signal
        mock_macd = Mock()
        macd_result = Mock()
        macd_result.values = np.full(50, 0.0001)
        macd_result.signals = np.zeros(50)  # No signal
        macd_result.metadata = {
            'histogram': np.full(50, 0.00005),
            'signal_line': np.full(50, 0.00005)
        }
        mock_macd.calculate.return_value = macd_result
        self.strategy.macd_indicator = mock_macd
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNone(signal)
    
    @patch('src.strategies.macd_strategy.MACD')
    def test_no_signal_when_nan_histogram(self, mock_macd_class):
        """Test no signal when histogram is NaN"""
        bars = self._create_bars(50)
        
        # Mock MACD with NaN
        mock_macd = Mock()
        macd_result = Mock()
        macd_result.values = np.full(50, 0.0001)
        macd_result.signals = np.zeros(50)
        macd_result.signals[-1] = 1
        macd_result.metadata = {
            'histogram': np.full(50, np.nan),  # NaN histogram
            'signal_line': np.full(50, 0.00005)
        }
        mock_macd.calculate.return_value = macd_result
        self.strategy.macd_indicator = mock_macd
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNone(signal)
    
    @patch('src.strategies.macd_strategy.MACD')
    def test_sl_tp_calculation_eurusd(self, mock_macd_class):
        """Test SL/TP calculation for EURUSD"""
        bars = self._create_bars(50, base_price=1.1000)
        
        # Mock MACD
        mock_macd = Mock()
        macd_result = Mock()
        macd_result.values = np.full(50, 0.0001)
        macd_result.signals = np.zeros(50)
        macd_result.signals[-1] = 1
        macd_result.metadata = {
            'histogram': np.full(50, 0.00005),
            'signal_line': np.full(50, 0.00003)
        }
        mock_macd.calculate.return_value = macd_result
        self.strategy.macd_indicator = mock_macd
        
        signal = self.strategy.analyze(bars)
        
        # For EURUSD, pip = 0.0001
        # SL should be 20 pips below
        # TP should be 40 pips above
        expected_sl_distance = 20 * 0.0001
        expected_tp_distance = 40 * 0.0001
        
        self.assertAlmostEqual(signal.price - signal.stop_loss, expected_sl_distance, places=5)
        self.assertAlmostEqual(signal.take_profit - signal.price, expected_tp_distance, places=5)
    
    @patch('src.strategies.macd_strategy.MACD')
    def test_sl_tp_calculation_jpypair(self, mock_macd_class):
        """Test SL/TP calculation for JPY pairs"""
        strategy_jpy = MACDStrategy(
            symbol="USDJPY",
            sl_pips=20,
            tp_pips=40
        )
        
        bars = self._create_bars(50, base_price=150.00)
        for bar in bars:
            bar.symbol = "USDJPY"
        
        # Mock MACD
        mock_macd = Mock()
        macd_result = Mock()
        macd_result.values = np.full(50, 0.0001)
        macd_result.signals = np.zeros(50)
        macd_result.signals[-1] = 1
        macd_result.metadata = {
            'histogram': np.full(50, 0.00005),
            'signal_line': np.full(50, 0.00003)
        }
        mock_macd.calculate.return_value = macd_result
        strategy_jpy.macd_indicator = mock_macd
        
        signal = strategy_jpy.analyze(bars)
        
        # For JPY, pip = 0.01
        expected_sl_distance = 20 * 0.01
        expected_tp_distance = 40 * 0.01
        
        self.assertAlmostEqual(signal.price - signal.stop_loss, expected_sl_distance, places=2)
        self.assertAlmostEqual(signal.take_profit - signal.price, expected_tp_distance, places=2)
    
    def test_calculate_confidence_with_momentum(self):
        """Test confidence calculation with positive momentum"""
        histogram = np.array([0.00001, 0.00002, 0.00003, 0.00004, 0.00005])
        
        confidence = self.strategy._calculate_confidence(
            current_hist=0.00005,
            recent_hist=histogram,
            direction="BUY"
        )
        
        # Positive momentum should give higher confidence
        self.assertGreaterEqual(confidence, 0.6)
        self.assertLessEqual(confidence, 1.0)
    
    def test_calculate_confidence_without_momentum(self):
        """Test confidence calculation with negative momentum"""
        histogram = np.array([0.00005, 0.00004, 0.00003, 0.00002, 0.00001])
        
        confidence = self.strategy._calculate_confidence(
            current_hist=0.00001,
            recent_hist=histogram,
            direction="BUY"
        )
        
        # Negative momentum should reduce confidence
        self.assertLess(confidence, 0.9)
    
    def test_calculate_confidence_with_nan_values(self):
        """Test confidence with NaN in recent histogram"""
        histogram = np.array([np.nan, np.nan, 0.00003, 0.00004, 0.00005])
        
        confidence = self.strategy._calculate_confidence(
            current_hist=0.00005,
            recent_hist=histogram,
            direction="BUY"
        )
        
        # Should filter NaN and still calculate
        self.assertGreaterEqual(confidence, 0.6)
    
    def test_calculate_confidence_insufficient_data(self):
        """Test confidence with insufficient recent data"""
        histogram = np.array([0.00005])
        
        confidence = self.strategy._calculate_confidence(
            current_hist=0.00005,
            recent_hist=histogram,
            direction="BUY"
        )
        
        # Should return default confidence
        self.assertEqual(confidence, 0.6)
    
    def test_strategy_name(self):
        """Test strategy name generation"""
        self.assertIn("MACD", self.strategy.name)
        self.assertIn("12", self.strategy.name)
        self.assertIn("26", self.strategy.name)
        self.assertIn("9", self.strategy.name)


if __name__ == '__main__':
    unittest.main()
