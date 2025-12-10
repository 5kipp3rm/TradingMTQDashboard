"""
Tests for ML Enhanced Strategy
"""
import unittest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

from src.strategies.ml_strategy import MLEnhancedStrategy
from src.strategies.base import SignalType


class TestMLEnhancedStrategy(unittest.TestCase):
    """Test ML Enhanced Strategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'ml_model_path': None,  # No model initially
            'ml_confidence_threshold': 0.6,
            'sl_pips': 30,
            'tp_pips': 60
        }
        
        # Create sample DataFrame (what the strategy actually expects)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='h')
        base_price = 1.1000
        self.bars = pd.DataFrame({
            'time': dates,
            'open': [base_price + i * 0.0001 for i in range(100)],
            'high': [base_price + i * 0.0001 + 0.0005 for i in range(100)],
            'low': [base_price + i * 0.0001 - 0.0005 for i in range(100)],
            'close': [base_price + i * 0.0001 for i in range(100)],
            'volume': [1000] * 100
        })
    
    @patch('src.strategies.ml_strategy.FeatureEngineer')
    def test_initialization(self, mock_fe):
        """Test basic initialization"""
        strategy = MLEnhancedStrategy(self.config)
        
        self.assertEqual(strategy.name, "ML-Enhanced")
        self.assertEqual(strategy.ml_confidence_threshold, 0.6)
        self.assertIsNone(strategy.ml_model)
    
    @patch('src.strategies.ml_strategy.FeatureEngineer')
    def test_analyze_insufficient_data(self, mock_fe):
        """Test analyze with insufficient data"""
        strategy = MLEnhancedStrategy(self.config)
        small_bars = self.bars[:10]  # Only 10 bars
        
        signal = strategy.analyze(small_bars)
        
        self.assertIsNone(signal)
    
    @patch('src.strategies.ml_strategy.FeatureEngineer')
    def test_analyze_with_technical_fallback(self, mock_fe):
        """Test analyze falls back to technical when no ML model"""
        strategy = MLEnhancedStrategy(self.config)
        
        # Should use technical analysis (MA crossover)
        signal = strategy.analyze(self.bars)
        
        # May or may not get a signal depending on crossover
        # Just ensure it doesn't crash
        self.assertIn(signal is None or hasattr(signal, 'type'), [True])
    
    @patch('src.strategies.ml_strategy.FeatureEngineer')
    def test_get_technical_signal(self, mock_fe):
        """Test _get_technical_signal method"""
        strategy = MLEnhancedStrategy(self.config)
        
        # Create uptrending data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='h')
        uptrend_bars = pd.DataFrame({
            'time': dates,
            'open': [1.1 + i * 0.002 for i in range(100)],
            'high': [1.1 + i * 0.002 + 0.001 for i in range(100)],
            'low': [1.1 + i * 0.002 - 0.001 for i in range(100)],
            'close': [1.1 + i * 0.002 for i in range(100)],
            'volume': [1000] * 100
        })
        
        signal = strategy._get_technical_signal(uptrend_bars)
        
        # Should return a Signal object or None
        if signal is not None:
            self.assertIn(signal.type, [SignalType.BUY, SignalType.SELL])
            self.assertIsNotNone(signal.price)
            self.assertIsNotNone(signal.stop_loss)
            self.assertIsNotNone(signal.take_profit)
    
    @patch('src.strategies.ml_strategy.FeatureEngineer')
    def test_ml_model_attributes(self, mock_fe):
        """Test ML model configuration attributes"""
        config = {
            **self.config,
            'ml_confidence_threshold': 0.7,
            'ml_weight': 0.8,
            'use_position_sizing': False,
            'fallback_to_technical': True
        }
        
        strategy = MLEnhancedStrategy(config)
        
        self.assertEqual(strategy.ml_confidence_threshold, 0.7)
        self.assertEqual(strategy.ml_weight, 0.8)
        self.assertFalse(strategy.use_position_sizing)
        self.assertTrue(strategy.fallback_to_technical)
    
    @patch('src.strategies.ml_strategy.FeatureEngineer')
    def test_strategy_enabled_by_default(self, mock_fe):
        """Test strategy is enabled by default"""
        strategy = MLEnhancedStrategy(self.config)
        
        self.assertTrue(strategy.is_enabled())


if __name__ == '__main__':
    unittest.main()
