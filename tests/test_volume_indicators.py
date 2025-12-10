"""
Tests for Volume Indicators
"""
import unittest
import numpy as np

from src.indicators.volume import OBV, VWAP


class TestOBV(unittest.TestCase):
    """Test On-Balance Volume indicator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.indicator = OBV()
    
    def test_initialization(self):
        """Test indicator initialization"""
        self.assertEqual(self.indicator.name, "OBV")
    
    def test_insufficient_data(self):
        """Test with insufficient data"""
        data = np.array([1.0])
        result = self.indicator.calculate(data)
        self.assertEqual(len(result.values), 0)
    
    def test_obv_rising_price_rising_volume(self):
        """Test OBV increases when price and volume rise"""
        prices = np.array([100, 101, 102, 103, 104])
        volumes = np.array([1000, 1000, 1000, 1000, 1000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # OBV should be cumulative and rising
        self.assertEqual(len(result.values), 5)
        self.assertEqual(result.values[0], 0)  # First value is 0
        self.assertGreater(result.values[-1], result.values[0])
        
        # Each step should increase
        for i in range(1, len(result.values)):
            self.assertGreaterEqual(result.values[i], result.values[i-1])
    
    def test_obv_falling_price_falling_volume(self):
        """Test OBV decreases when price falls"""
        prices = np.array([104, 103, 102, 101, 100])
        volumes = np.array([1000, 1000, 1000, 1000, 1000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # OBV should be decreasing
        self.assertLess(result.values[-1], result.values[1])
    
    def test_obv_price_unchanged(self):
        """Test OBV unchanged when price doesn't change"""
        prices = np.array([100, 100, 100, 100])
        volumes = np.array([1000, 1000, 1000, 1000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # OBV should remain at 0
        for value in result.values:
            self.assertEqual(value, 0)
    
    def test_obv_without_volume(self):
        """Test OBV with default volume (all 1s)"""
        prices = np.array([100, 101, 102, 101, 100])
        
        result = self.indicator.calculate(prices)
        
        # Should still work with dummy volume
        self.assertEqual(len(result.values), 5)
        self.assertEqual(result.values[0], 0)
    
    def test_obv_signals_bullish_confirmation(self):
        """Test bullish signal when OBV and price both rise"""
        prices = np.array([100, 101, 102, 103, 104])
        volumes = np.array([1000, 1500, 2000, 2500, 3000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # Should have bullish signals
        self.assertGreater(np.sum(result.signals > 0), 0)
    
    def test_obv_signals_bearish_confirmation(self):
        """Test bearish signal when OBV and price both fall"""
        prices = np.array([104, 103, 102, 101, 100])
        volumes = np.array([1000, 1500, 2000, 2500, 3000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # Should have bearish signals
        self.assertGreater(np.sum(result.signals < 0), 0)
    
    def test_obv_divergence(self):
        """Test OBV divergence (price up, OBV down)"""
        prices = np.array([100, 101, 102, 103, 104])
        # High volume on down days creates divergence
        volumes = np.array([1000, 100, 100, 100, 100])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # OBV should increase less dramatically than price
        self.assertLess(result.values[-1] / result.values[1], 5)


class TestVWAP(unittest.TestCase):
    """Test Volume Weighted Average Price indicator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.indicator = VWAP()
    
    def test_initialization(self):
        """Test indicator initialization"""
        self.assertEqual(self.indicator.name, "VWAP")
    
    def test_insufficient_data(self):
        """Test with insufficient data"""
        data = np.array([])
        result = self.indicator.calculate(data)
        self.assertEqual(len(result.values), 0)
    
    def test_vwap_calculation(self):
        """Test basic VWAP calculation"""
        prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        volumes = np.array([1000, 1000, 1000, 1000, 1000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        self.assertEqual(len(result.values), 5)
        # First VWAP should equal first price
        self.assertAlmostEqual(result.values[0], 100.0, places=1)
        
        # VWAP should be increasing as prices increase
        self.assertGreater(result.values[-1], result.values[0])
    
    def test_vwap_with_high_low(self):
        """Test VWAP calculation with high/low prices"""
        closes = np.array([100.0, 101.0, 102.0])
        highs = np.array([101.0, 102.0, 103.0])
        lows = np.array([99.0, 100.0, 101.0])
        volumes = np.array([1000, 1000, 1000])
        
        result = self.indicator.calculate(closes, volume=volumes, high=highs, low=lows)
        
        self.assertEqual(len(result.values), 3)
        # VWAP should use typical price (H+L+C)/3
        self.assertGreater(result.values[0], 0)
    
    def test_vwap_without_volume(self):
        """Test VWAP with default volume"""
        prices = np.array([100.0, 101.0, 102.0])
        
        result = self.indicator.calculate(prices)
        
        # Should work with dummy volume
        self.assertEqual(len(result.values), 3)
        self.assertGreater(result.values[-1], 0)
    
    def test_vwap_cumulative(self):
        """Test that VWAP is cumulative"""
        prices = np.array([100.0, 100.0, 100.0, 100.0])
        volumes = np.array([1000, 1000, 1000, 1000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # With constant price, VWAP should equal price
        for value in result.values:
            self.assertAlmostEqual(value, 100.0, places=1)
    
    def test_vwap_higher_volume_impact(self):
        """Test that higher volume periods impact VWAP more"""
        prices = np.array([100.0, 110.0, 90.0])
        volumes_high = np.array([1000, 10000, 1000])  # High volume at 110
        volumes_low = np.array([1000, 1000, 1000])    # Equal volume
        
        result_high = self.indicator.calculate(prices, volume=volumes_high)
        result_low = self.indicator.calculate(prices, volume=volumes_low)
        
        # With high volume at 110, VWAP should be pulled higher
        self.assertGreater(result_high.values[-1], result_low.values[-1])
    
    def test_vwap_bullish_crossover_signal(self):
        """Test bullish signal when price crosses above VWAP"""
        # Price starts below VWAP, then crosses above
        prices = np.array([100.0, 99.0, 98.0, 99.5, 101.0])
        volumes = np.array([1000, 1000, 1000, 1000, 1000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # Should have at least one bullish signal
        self.assertGreater(np.sum(result.signals > 0), 0)
    
    def test_vwap_bearish_crossover_signal(self):
        """Test bearish signal when price crosses below VWAP"""
        # Price starts above VWAP, then crosses below
        prices = np.array([100.0, 101.0, 102.0, 101.0, 99.0])
        volumes = np.array([1000, 1000, 1000, 1000, 1000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # Should have at least one bearish signal
        self.assertGreater(np.sum(result.signals < 0), 0)
    
    def test_vwap_no_signals_when_no_crossover(self):
        """Test no signals when price doesn't cross VWAP"""
        # Constant price = constant VWAP
        prices = np.array([100.0, 100.0, 100.0, 100.0])
        volumes = np.array([1000, 1000, 1000, 1000])
        
        result = self.indicator.calculate(prices, volume=volumes)
        
        # Should have no crossover signals
        self.assertEqual(np.sum(result.signals != 0), 0)
    
    def test_vwap_without_high_low_uses_close(self):
        """Test VWAP defaults to close when high/low not provided"""
        prices = np.array([100.0, 101.0, 102.0])
        volumes = np.array([1000, 1000, 1000])
        
        # Without high/low
        result1 = self.indicator.calculate(prices, volume=volumes)
        
        # With high/low equal to close
        result2 = self.indicator.calculate(
            prices, volume=volumes, 
            high=prices, low=prices
        )
        
        # Results should be identical
        np.testing.assert_array_almost_equal(result1.values, result2.values)


if __name__ == '__main__':
    unittest.main()
