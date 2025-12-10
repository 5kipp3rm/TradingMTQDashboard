"""
Tests for Bollinger Bands Strategy
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from datetime import datetime, timedelta

from src.strategies.bb_strategy import BollingerBandsStrategy
from src.strategies.base import SignalType
from src.connectors.base import OHLCBar


class TestBollingerBandsStrategy(unittest.TestCase):
    """Test Bollinger Bands Strategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.symbol = "EURUSD"
        self.strategy = BollingerBandsStrategy(
            symbol=self.symbol,
            timeframe="M5",
            bb_period=20,
            bb_std=2.0,
            rsi_period=14,
            rsi_oversold=35,
            rsi_overbought=65
        )
    
    def _create_bars(self, num_bars: int, base_price: float = 1.1000, volatility: float = 0.0010) -> list:
        """Helper to create test bars"""
        bars = []
        now = datetime.now()
        
        for i in range(num_bars):
            # Create price movement
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
        self.assertEqual(self.strategy.bb_period, 20)
        self.assertEqual(self.strategy.bb_std, 2.0)
        self.assertEqual(self.strategy.rsi_period, 14)
        self.assertEqual(self.strategy.rsi_oversold, 35)
        self.assertEqual(self.strategy.rsi_overbought, 65)
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
    
    def test_buy_signal_lower_band_touch(self):
        """Test BUY signal when price touches lower band with oversold RSI"""
        bars = self._create_bars(50, base_price=1.1000)
        
        # Mock Bollinger Bands on strategy instance
        mock_bb = Mock()
        bb_result = Mock()
        bb_result.values = np.full(50, 1.1000)  # Middle band
        bb_result.metadata = {
            'upper_band': np.full(50, 1.1020),  # Upper band
            'lower_band': np.full(50, 1.0980)   # Lower band
        }
        # Simulate price touching lower band on last bar
        bb_result.metadata['lower_band'][-1] = 1.0995
        bb_result.metadata['lower_band'][-2] = 1.0980
        mock_bb.calculate.return_value = bb_result
        self.strategy.bb_indicator = mock_bb
        
        # Mock RSI - oversold
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 30.0)  # Oversold
        mock_rsi.calculate.return_value = rsi_result
        self.strategy.rsi_indicator = mock_rsi
        
        # Set last bar price below lower band
        bars[-1].close = 1.0994
        bars[-2].close = 1.0985
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, SignalType.BUY)
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertLess(signal.sl, signal.price)
        self.assertGreater(signal.tp, signal.price)
        self.assertIn("lower BB", signal.reason)
        self.assertIn("RSI oversold", signal.reason)
    
    @patch('src.strategies.bb_strategy.BollingerBands')
    @patch('src.strategies.bb_strategy.RSI')
    def test_sell_signal_upper_band_touch(self, mock_rsi_class, mock_bb_class):
        """Test SELL signal when price touches upper band with overbought RSI"""
        bars = self._create_bars(50, base_price=1.1000)
        
        # Mock Bollinger Bands
        mock_bb = Mock()
        bb_result = Mock()
        bb_result.values = np.full(50, 1.1000)  # Middle band
        bb_result.metadata = {
            'upper_band': np.full(50, 1.1020),  # Upper band
            'lower_band': np.full(50, 1.0980)   # Lower band
        }
        # Simulate price touching upper band on last bar
        bb_result.metadata['upper_band'][-1] = 1.1015
        bb_result.metadata['upper_band'][-2] = 1.1020
        mock_bb.calculate.return_value = bb_result
        mock_bb_class.return_value = mock_bb
        
        # Mock RSI - overbought
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 70.0)  # Overbought
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        # Set last bar price above upper band
        bars[-1].close = 1.1016
        bars[-2].close = 1.1012
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.type, SignalType.SELL)
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertGreater(signal.sl, signal.price)
        self.assertLess(signal.tp, signal.price)
        self.assertIn("upper BB", signal.reason)
        self.assertIn("RSI overbought", signal.reason)
    
    @patch('src.strategies.bb_strategy.BollingerBands')
    @patch('src.strategies.bb_strategy.RSI')
    def test_no_signal_price_at_band_but_rsi_neutral(self, mock_rsi_class, mock_bb_class):
        """Test no signal when price at band but RSI is neutral"""
        bars = self._create_bars(50)
        
        # Mock Bollinger Bands
        mock_bb = Mock()
        bb_result = Mock()
        bb_result.values = np.full(50, 1.1000)
        bb_result.metadata = {
            'upper_band': np.full(50, 1.1020),
            'lower_band': np.full(50, 1.0980)
        }
        bb_result.metadata['lower_band'][-1] = 1.0995
        mock_bb.calculate.return_value = bb_result
        mock_bb_class.return_value = mock_bb
        
        # Mock RSI - neutral (not oversold/overbought)
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 50.0)  # Neutral RSI
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        bars[-1].close = 1.0994
        bars[-2].close = 1.0985
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNone(signal)
    
    @patch('src.strategies.bb_strategy.BollingerBands')
    @patch('src.strategies.bb_strategy.RSI')
    def test_no_signal_when_nan_values(self, mock_rsi_class, mock_bb_class):
        """Test no signal when indicators return NaN"""
        bars = self._create_bars(50)
        
        # Mock Bollinger Bands with NaN
        mock_bb = Mock()
        bb_result = Mock()
        bb_result.values = np.full(50, np.nan)
        bb_result.metadata = {
            'upper_band': np.full(50, np.nan),
            'lower_band': np.full(50, np.nan)
        }
        mock_bb.calculate.return_value = bb_result
        mock_bb_class.return_value = mock_bb
        
        # Mock RSI
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 50.0)
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        signal = self.strategy.analyze(bars)
        
        self.assertIsNone(signal)
    
    def test_calculate_confidence_buy(self):
        """Test confidence calculation for BUY signal"""
        # Deeper penetration and more extreme RSI = higher confidence
        confidence = self.strategy._calculate_confidence(
            price=1.0970,
            band=1.0980,
            middle=1.1000,
            rsi=25.0,
            direction="BUY"
        )
        
        self.assertGreater(confidence, 0.6)
        self.assertLessEqual(confidence, 0.95)
    
    def test_calculate_confidence_sell(self):
        """Test confidence calculation for SELL signal"""
        confidence = self.strategy._calculate_confidence(
            price=1.1030,
            band=1.1020,
            middle=1.1000,
            rsi=75.0,
            direction="SELL"
        )
        
        self.assertGreater(confidence, 0.6)
        self.assertLessEqual(confidence, 0.95)
    
    @patch('src.strategies.bb_strategy.BollingerBands')
    @patch('src.strategies.bb_strategy.RSI')
    def test_sl_tp_calculation(self, mock_rsi_class, mock_bb_class):
        """Test stop loss and take profit calculation"""
        bars = self._create_bars(50)
        
        # Mock indicators
        mock_bb = Mock()
        bb_result = Mock()
        bb_result.values = np.full(50, 1.1000)
        bb_result.metadata = {
            'upper_band': np.full(50, 1.1020),
            'lower_band': np.full(50, 1.0980)
        }
        bb_result.metadata['lower_band'][-1] = 1.0995
        bb_result.metadata['lower_band'][-2] = 1.0980
        mock_bb.calculate.return_value = bb_result
        mock_bb_class.return_value = mock_bb
        
        mock_rsi = Mock()
        rsi_result = Mock()
        rsi_result.values = np.full(50, 30.0)
        mock_rsi.calculate.return_value = rsi_result
        mock_rsi_class.return_value = mock_rsi
        
        bars[-1].close = 1.0994
        bars[-2].close = 1.0985
        
        signal = self.strategy.analyze(bars)
        
        # Verify SL/TP are set and reasonable
        band_width = 1.1020 - 1.0980  # 0.0040
        self.assertIsNotNone(signal.sl)
        self.assertIsNotNone(signal.tp)
        self.assertLess(signal.sl, signal.price)
        self.assertGreater(signal.tp, signal.price)
    
    def test_strategy_name(self):
        """Test strategy name generation"""
        self.assertIn("BB", self.strategy.name)
        self.assertIn("20", self.strategy.name)
        self.assertIn("RSI", self.strategy.name)
        self.assertIn("14", self.strategy.name)


if __name__ == '__main__':
    unittest.main()
