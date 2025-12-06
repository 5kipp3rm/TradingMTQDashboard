"""
Machine Learning Module for TradingMTQ
Provides ML models for price prediction and signal classification
"""

from .base import BaseMLModel, ModelType, MLPrediction
from .feature_engineer import FeatureEngineer, FeatureSet

# Optional imports (require additional dependencies)
try:
    from .lstm_model import LSTMPricePredictor
    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False
    LSTMPricePredictor = None

try:
    from .random_forest import RandomForestClassifier
    RF_AVAILABLE = True
except ImportError:
    RF_AVAILABLE = False
    RandomForestClassifier = None

__all__ = [
    'BaseMLModel',
    'ModelType',
    'MLPrediction',
    'FeatureEngineer',
    'FeatureSet',
    'LSTMPricePredictor',
    'RandomForestClassifier',
    'LSTM_AVAILABLE',
    'RF_AVAILABLE',
]
