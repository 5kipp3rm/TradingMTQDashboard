"""
ML-Enhanced Trading Strategy
Combines traditional technical analysis with machine learning predictions
"""
import numpy as np
from typing import Dict, Any, Optional
import pandas as pd

from src.strategies.base import BaseStrategy, Signal, SignalType
from src.ml import (
    FeatureEngineer, RandomForestClassifier, LSTMPricePredictor,
    RF_AVAILABLE, LSTM_AVAILABLE
)


class MLEnhancedStrategy(BaseStrategy):
    """
    ML-Enhanced trading strategy that combines:
    - Traditional technical indicators
    - Machine learning predictions
    - Confidence-based position sizing
    
    Uses both Random Forest for signal classification and
    LSTM for price prediction (optional).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ML-enhanced strategy
        
        Args:
            config: Strategy configuration
                - ml_model_path: Path to trained ML model
                - ml_model_type: 'random_forest' or 'lstm'
                - ml_confidence_threshold: Min confidence to trade (default: 0.6)
                - ml_weight: Weight of ML signal vs technical (default: 0.7)
                - use_position_sizing: Scale lots by confidence (default: True)
                - fallback_to_technical: Use technical signals if ML fails (default: True)
                - ... (plus standard strategy params)
        """
        super().__init__("ML-Enhanced", config)
        
        self.ml_confidence_threshold = config.get('ml_confidence_threshold', 0.6)
        self.ml_weight = config.get('ml_weight', 0.7)
        self.use_position_sizing = config.get('use_position_sizing', True)
        self.fallback_to_technical = config.get('fallback_to_technical', True)
        
        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer()
        
        # Load ML model
        self.ml_model = self._load_ml_model(config)
        
    def _load_ml_model(self, config: Dict[str, Any]):
        """Load trained ML model"""
        model_type = config.get('ml_model_type', 'random_forest')
        model_path = config.get('ml_model_path')
        
        if not model_path:
            print("⚠️  No ML model path provided, using technical signals only")
            return None
        
        try:
            if model_type == 'random_forest' and RF_AVAILABLE:
                model = RandomForestClassifier()
                if model.load(model_path):
                    print(f"✓ Loaded Random Forest model from {model_path}")
                    return model
            elif model_type == 'lstm' and LSTM_AVAILABLE:
                model = LSTMPricePredictor()
                if model.load(model_path):
                    print(f"✓ Loaded LSTM model from {model_path}")
                    return model
            else:
                print(f"⚠️  ML model type '{model_type}' not available")
                return None
        except Exception as e:
            print(f"⚠️  Failed to load ML model: {e}")
            return None
    
    def analyze(self, bars: pd.DataFrame) -> Optional[Signal]:
        """
        Analyze market with ML + technical indicators
        
        Args:
            bars: OHLC DataFrame
            
        Returns:
            Trading signal with ML-enhanced confidence
        """
        if len(bars) < 50:
            return None
        
        # 1. Get ML prediction
        ml_signal = None
        ml_confidence = 0.0
        
        if self.ml_model is not None:
            ml_signal, ml_confidence = self._get_ml_signal(bars)
        
        # 2. Get technical signal (fallback or combine)
        technical_signal = self._get_technical_signal(bars)
        
        # 3. Combine signals
        if ml_signal is not None and ml_confidence >= self.ml_confidence_threshold:
            # Use ML signal
            final_signal = ml_signal
            final_confidence = ml_confidence
            
            # Optionally blend with technical
            if technical_signal is not None and self.ml_weight < 1.0:
                if ml_signal != technical_signal.type:
                    # Signals disagree - reduce confidence
                    final_confidence *= self.ml_weight
        
        elif self.fallback_to_technical and technical_signal is not None:
            # Fall back to technical
            final_signal = technical_signal.type
            final_confidence = 0.5  # Default confidence for technical
        
        else:
            # No valid signal
            return None
        
        # 4. Calculate SL/TP
        current_price = bars['close'].iloc[-1]
        sl_pips = self.config.get('sl_pips', 30)
        tp_pips = self.config.get('tp_pips', 60)
        
        pip_value = 0.0001  # Simplified
        
        if final_signal == SignalType.BUY:
            stop_loss = current_price - (sl_pips * pip_value)
            take_profit = current_price + (tp_pips * pip_value)
        else:  # SELL
            stop_loss = current_price + (sl_pips * pip_value)
            take_profit = current_price - (tp_pips * pip_value)
        
        # 5. Create signal with confidence
        signal = Signal(
            type=final_signal,
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=final_confidence
        )
        
        # 6. Adjust position size by confidence if enabled
        if self.use_position_sizing:
            signal.metadata = {
                'ml_confidence': final_confidence,
                'suggested_lot_multiplier': final_confidence
            }
        
        return signal
    
    def _get_ml_signal(self, bars: pd.DataFrame) -> tuple:
        """Get ML model prediction"""
        try:
            # Generate features
            feature_set = self.feature_engineer.transform(bars)
            
            # Get latest features (last row)
            if len(feature_set.features) == 0:
                return None, 0.0
            
            X = feature_set.features.iloc[-1:].values
            
            # Predict
            prediction = self.ml_model.predict(X)
            
            # Convert to signal type
            if prediction.prediction > 0:
                signal_type = SignalType.BUY
            elif prediction.prediction < 0:
                signal_type = SignalType.SELL
            else:
                return None, 0.0  # HOLD
            
            return signal_type, prediction.confidence
        
        except Exception as e:
            print(f"⚠️  ML prediction error: {e}")
            return None, 0.0
    
    def _get_technical_signal(self, bars: pd.DataFrame) -> Optional[Signal]:
        """Get traditional technical signal (simple MA crossover)"""
        if len(bars) < 50:
            return None
        
        # Simple MA crossover as fallback
        from src.indicators import calculate_sma
        
        close = bars['close'].values
        fast_ma = calculate_sma(close, 20)
        slow_ma = calculate_sma(close, 50)
        
        if fast_ma is None or slow_ma is None:
            return None
        
        # Check crossover
        if fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2]:
            signal_type = SignalType.BUY
        elif fast_ma[-1] < slow_ma[-1] and fast_ma[-2] >= slow_ma[-2]:
            signal_type = SignalType.SELL
        else:
            return None
        
        current_price = bars['close'].iloc[-1]
        sl_pips = self.config.get('sl_pips', 30)
        tp_pips = self.config.get('tp_pips', 60)
        pip_value = 0.0001
        
        if signal_type == SignalType.BUY:
            stop_loss = current_price - (sl_pips * pip_value)
            take_profit = current_price + (tp_pips * pip_value)
        else:
            stop_loss = current_price + (sl_pips * pip_value)
            take_profit = current_price - (tp_pips * pip_value)
        
        return Signal(
            type=signal_type,
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=0.5
        )
