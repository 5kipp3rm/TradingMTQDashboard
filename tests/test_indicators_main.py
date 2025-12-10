"""
Tests for main indicators module (indicators.py)
"""
import unittest
import numpy as np
from datetime import datetime, timedelta

from src.indicators.indicators import (
    calculate_sma, calculate_ema, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_atr, calculate_stochastic,
    calculate_adx, calculate_cci, calculate_williams_r,
    calculate_roc, calculate_obv
)
from src.connectors.base import OHLCBar


class TestSMA(unittest.TestCase):
    """Test Simple Moving Average"""
    
    def test_sma_basic(self):
        """Test basic SMA calculation"""
        closes = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        sma = calculate_sma(closes, 3)
        
        # First 2 should be NaN
        self.assertTrue(np.isnan(sma[0]))
        self.assertTrue(np.isnan(sma[1]))
        
        # Third should be (1+2+3)/3 = 2
        self.assertAlmostEqual(sma[2], 2.0)
        
        # Last should be (8+9+10)/3 = 9
        self.assertAlmostEqual(sma[9], 9.0)
    
    def test_sma_insufficient_data(self):
        """Test SMA with insufficient data"""
        closes = np.array([1, 2])
        sma = calculate_sma(closes, 5)
        
        # All should be NaN
        self.assertTrue(np.all(np.isnan(sma)))


class TestEMA(unittest.TestCase):
    """Test Exponential Moving Average"""
    
    def test_ema_basic(self):
        """Test basic EMA calculation"""
        closes = np.array([22, 24, 23, 25, 27, 26, 28, 30, 29, 31])
        ema = calculate_ema(closes, 5)
        
        # First 4 should be NaN
        for i in range(4):
            self.assertTrue(np.isnan(ema[i]))
        
        # 5th value should be SMA
        self.assertAlmostEqual(ema[4], np.mean(closes[:5]))
        
        # Rest should be calculated
        self.assertFalse(np.isnan(ema[9]))


class TestRSI(unittest.TestCase):
    """Test Relative Strength Index"""
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        # Trending up data
        closes = np.array([44, 44.5, 45, 45.5, 46, 46.5, 47, 47.5, 48, 48.5,
                          49, 49.5, 50, 50.5, 51, 51.5, 52])
        rsi = calculate_rsi(closes, 14)
        
        # RSI should be > 50 for uptrend
        self.assertGreater(rsi[-1], 50)
    
    def test_rsi_bounds(self):
        """Test RSI stays within 0-100"""
        closes = np.random.random(50) * 100
        rsi = calculate_rsi(closes, 14)
        
        valid_rsi = rsi[~np.isnan(rsi)]
        self.assertTrue(np.all(valid_rsi >= 0))
        self.assertTrue(np.all(valid_rsi <= 100))


class TestMACD(unittest.TestCase):
    """Test MACD"""
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        closes = np.linspace(100, 110, 50)
        macd_line, signal_line, histogram = calculate_macd(closes)
        
        self.assertEqual(len(macd_line), 50)
        self.assertEqual(len(signal_line), 50)
        self.assertEqual(len(histogram), 50)
    
    def test_macd_trending_up(self):
        """Test MACD with uptrend"""
        closes = np.linspace(100, 120, 50)
        macd_line, signal_line, histogram = calculate_macd(closes)
        
        # MACD should be positive in uptrend
        valid_macd = macd_line[~np.isnan(macd_line)]
        self.assertGreater(valid_macd[-1], 0)


class TestBollingerBands(unittest.TestCase):
    """Test Bollinger Bands"""
    
    def test_bb_calculation(self):
        """Test Bollinger Bands calculation"""
        closes = np.array([100 + i * 0.1 for i in range(30)])
        upper, middle, lower = calculate_bollinger_bands(closes, 20, 2.0)
        
        self.assertEqual(len(upper), 30)
        self.assertEqual(len(middle), 30)
        self.assertEqual(len(lower), 30)
    
    def test_bb_relationship(self):
        """Test upper > middle > lower"""
        closes = np.random.random(30) * 100 + 50
        upper, middle, lower = calculate_bollinger_bands(closes, 20, 2.0)
        
        # Where valid, upper > middle > lower
        valid_idx = ~np.isnan(middle)
        self.assertTrue(np.all(upper[valid_idx] >= middle[valid_idx]))
        self.assertTrue(np.all(middle[valid_idx] >= lower[valid_idx]))


class TestATR(unittest.TestCase):
    """Test Average True Range"""
    
    def _create_bars(self, n):
        """Helper to create bars"""
        bars = []
        for i in range(n):
            bar = OHLCBar(
                symbol="TEST",
                timeframe="M5",
                time=datetime.now() - timedelta(minutes=(n-i)*5),
                open=100 + i,
                high=102 + i,
                low=99 + i,
                close=101 + i,
                tick_volume=1000
            )
            bars.append(bar)
        return bars
    
    def test_atr_calculation(self):
        """Test ATR calculation"""
        bars = self._create_bars(30)
        atr = calculate_atr(bars, 14)
        
        self.assertEqual(len(atr), 30)
        
        # ATR should be positive
        valid_atr = atr[~np.isnan(atr)]
        self.assertTrue(np.all(valid_atr > 0))


class TestStochastic(unittest.TestCase):
    """Test Stochastic Oscillator"""
    
    def _create_bars(self, n):
        """Helper to create bars"""
        bars = []
        for i in range(n):
            bar = OHLCBar(
                symbol="TEST",
                timeframe="M5",
                time=datetime.now() - timedelta(minutes=(n-i)*5),
                open=100 + np.sin(i) * 10,
                high=105 + np.sin(i) * 10,
                low=95 + np.sin(i) * 10,
                close=100 + np.sin(i) * 10,
                tick_volume=1000
            )
            bars.append(bar)
        return bars
    
    def test_stochastic_calculation(self):
        """Test Stochastic calculation"""
        bars = self._create_bars(30)
        k, d = calculate_stochastic(bars, 14, 3)
        
        self.assertEqual(len(k), 30)
        self.assertEqual(len(d), 30)
    
    def test_stochastic_bounds(self):
        """Test Stochastic stays within 0-100"""
        bars = self._create_bars(30)
        k, d = calculate_stochastic(bars, 14, 3)
        
        valid_k = k[~np.isnan(k)]
        self.assertTrue(np.all(valid_k >= 0))
        self.assertTrue(np.all(valid_k <= 100))


class TestADX(unittest.TestCase):
    """Test Average Directional Index"""
    
    def _create_bars(self, n):
        """Helper to create bars"""
        bars = []
        for i in range(n):
            bar = OHLCBar(
                symbol="TEST",
                timeframe="M5",
                time=datetime.now() - timedelta(minutes=(n-i)*5),
                open=100 + i * 0.1,
                high=102 + i * 0.1,
                low=99 + i * 0.1,
                close=101 + i * 0.1,
                tick_volume=1000
            )
            bars.append(bar)
        return bars
    
    def test_adx_calculation(self):
        """Test ADX calculation"""
        bars = self._create_bars(50)
        adx, plus_di, minus_di = calculate_adx(bars, 14)
        
        self.assertEqual(len(adx), 50)
        self.assertEqual(len(plus_di), 50)
        self.assertEqual(len(minus_di), 50)


class TestCCI(unittest.TestCase):
    """Test Commodity Channel Index"""
    
    def _create_bars(self, n):
        """Helper to create bars"""
        bars = []
        for i in range(n):
            bar = OHLCBar(
                symbol="TEST",
                timeframe="M5",
                time=datetime.now() - timedelta(minutes=(n-i)*5),
                open=100,
                high=101,
                low=99,
                close=100,
                tick_volume=1000
            )
            bars.append(bar)
        return bars
    
    def test_cci_calculation(self):
        """Test CCI calculation"""
        bars = self._create_bars(30)
        cci = calculate_cci(bars, 20)
        
        self.assertEqual(len(cci), 30)


class TestWilliamsR(unittest.TestCase):
    """Test Williams %R"""
    
    def _create_bars(self, n):
        """Helper to create bars"""
        bars = []
        for i in range(n):
            bar = OHLCBar(
                symbol="TEST",
                timeframe="M5",
                time=datetime.now() - timedelta(minutes=(n-i)*5),
                open=100 + i,
                high=105 + i,
                low=95 + i,
                close=100 + i,
                tick_volume=1000
            )
            bars.append(bar)
        return bars
    
    def test_williams_r_calculation(self):
        """Test Williams %R calculation"""
        bars = self._create_bars(30)
        wr = calculate_williams_r(bars, 14)
        
        self.assertEqual(len(wr), 30)
    
    def test_williams_r_bounds(self):
        """Test Williams %R stays within -100 to 0"""
        bars = self._create_bars(30)
        wr = calculate_williams_r(bars, 14)
        
        valid_wr = wr[~np.isnan(wr)]
        self.assertTrue(np.all(valid_wr >= -100))
        self.assertTrue(np.all(valid_wr <= 0))


class TestROC(unittest.TestCase):
    """Test Rate of Change"""
    
    def test_roc_calculation(self):
        """Test ROC calculation"""
        closes = np.array([100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
                          120, 122, 124, 126, 128])
        roc = calculate_roc(closes, 12)
        
        self.assertEqual(len(roc), 15)
        
        # ROC should be positive for uptrend
        self.assertGreater(roc[-1], 0)


class TestOBV(unittest.TestCase):
    """Test On-Balance Volume"""
    
    def _create_bars(self, n, trend='up'):
        """Helper to create bars"""
        bars = []
        for i in range(n):
            if trend == 'up':
                close = 100 + i
            elif trend == 'down':
                close = 100 - i
            else:
                close = 100
            
            bar = OHLCBar(
                symbol="TEST",
                timeframe="M5",
                time=datetime.now() - timedelta(minutes=(n-i)*5),
                open=close - 0.5,
                high=close + 0.5,
                low=close - 1,
                close=close,
                tick_volume=1000
            )
            bars.append(bar)
        return bars
    
    def test_obv_uptrend(self):
        """Test OBV in uptrend"""
        bars = self._create_bars(20, 'up')
        obv = calculate_obv(bars)
        
        # OBV should increase in uptrend
        self.assertGreater(obv[-1], obv[0])
    
    def test_obv_downtrend(self):
        """Test OBV in downtrend"""
        bars = self._create_bars(20, 'down')
        obv = calculate_obv(bars)
        
        # OBV should decrease in downtrend
        self.assertLess(obv[-1], obv[0])


if __name__ == '__main__':
    unittest.main()
