"""
LSTM Neural Network for Price Prediction
Predicts future price movements using deep learning
"""
import numpy as np
import pickle
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    keras = None
    layers = None
    tf = None

from .base import BaseMLModel, ModelType, MLPrediction


# Dummy class when TensorFlow not available
class _DummyLSTM:
    def __init__(self, *args, **kwargs):
        raise ImportError(
            "TensorFlow not installed. LSTM models require TensorFlow.\n"
            "Install with: pip install tensorflow"
        )


if TENSORFLOW_AVAILABLE:
    class LSTMPricePredictor(BaseMLModel):
        """
        LSTM-based price prediction model
        Uses sequence of historical prices to predict future direction
        """
        
        def __init__(self, lookback: int = 60, name: str = "lstm_predictor"):
            """
            Args:
                lookback: Number of time steps to look back
                name: Model name
            """
            super().__init__(model_type=ModelType.NEURAL_NETWORK, name=name)
            self.lookback = lookback
            self.model: Optional[keras.Model] = None
            self.scaler = None
            
        def _build_model(self, input_shape: Tuple[int, int]) -> keras.Model:
            """Build LSTM architecture"""
            model = keras.Sequential([
                layers.LSTM(50, return_sequences=True, input_shape=input_shape),
                layers.Dropout(0.2),
                layers.LSTM(50, return_sequences=True),
                layers.Dropout(0.2),
                layers.LSTM(50),
                layers.Dropout(0.2),
                layers.Dense(25, activation='relu'),
                layers.Dense(3, activation='softmax')  # BUY, SELL, HOLD
            ])
            
            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
            return model
            
        def train(self, X_train: np.ndarray, y_train: np.ndarray, 
                 validation_data: Optional[Tuple] = None) -> Dict[str, Any]:
            """
            Train LSTM model
            
            Args:
                X_train: Training sequences [samples, lookback, features]
                y_train: Labels (0=SELL, 1=HOLD, 2=BUY)
                validation_data: Optional validation set
            """
            if not self._is_trained:
                # Build model on first training
                input_shape = (X_train.shape[1], X_train.shape[2])
                self.model = self._build_model(input_shape)
            
            # Train
            history = self.model.fit(
                X_train, y_train,
                epochs=50,
                batch_size=32,
                validation_data=validation_data,
                verbose=0
            )
            
            self._is_trained = True
            self._last_training = np.datetime64('now')
            
            return {
                'final_loss': history.history['loss'][-1],
                'final_accuracy': history.history['accuracy'][-1],
                'epochs': len(history.history['loss'])
            }
            
        def predict(self, X: np.ndarray) -> MLPrediction:
            """
            Make prediction
            
            Args:
                X: Input sequence [lookback, features]
            """
            if not self._is_trained:
                raise ValueError("Model not trained")
            
            # Reshape for prediction
            X_reshaped = X.reshape(1, X.shape[0], X.shape[1])
            
            # Get probabilities
            probs = self.model.predict(X_reshaped, verbose=0)[0]
            
            # Get prediction
            pred_class = np.argmax(probs)
            signal_map = {0: -1, 1: 0, 2: 1}  # SELL, HOLD, BUY
            signal = signal_map[pred_class]
            
            return MLPrediction(
                signal=signal,
                confidence=float(probs[pred_class]),
                probabilities={'sell': float(probs[0]), 
                             'hold': float(probs[1]), 
                             'buy': float(probs[2])},
                model_type=self.model_type,
                features_used=X.shape[1]
            )
            
        def save(self, path: Path) -> None:
            """Save model"""
            if not self._is_trained:
                raise ValueError("Cannot save untrained model")
            
            # Save Keras model
            model_path = path / f"{self.name}_model.h5"
            self.model.save(model_path)
            
            # Save metadata
            metadata = {
                'name': self.name,
                'model_type': self.model_type.value,
                'lookback': self.lookback,
                'is_trained': self._is_trained,
                'last_training': str(self._last_training),
                'performance': self._performance
            }
            
            metadata_path = path / f"{self.name}_metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
                
        def load(self, path: Path) -> None:
            """Load model"""
            # Load Keras model
            model_path = path / f"{self.name}_model.h5"
            self.model = keras.models.load_model(model_path)
            
            # Load metadata
            metadata_path = path / f"{self.name}_metadata.pkl"
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.lookback = metadata['lookback']
            self._is_trained = metadata['is_trained']
            self._last_training = np.datetime64(metadata['last_training'])
            self._performance = metadata['performance']
else:
    # Use dummy class when TensorFlow not available
    LSTMPricePredictor = _DummyLSTM
