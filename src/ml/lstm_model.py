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

from .base import BaseMLModel, ModelType, MLPrediction


class LSTMPricePredictor(BaseMLModel):
    """
    LSTM neural network for price prediction
    
    Predicts future price movements using sequential deep learning.
    Can predict next N candles or directional movement.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LSTM model
        
        Args:
            config: Model configuration
                - sequence_length: Number of historical candles to use (default: 50)
                - lstm_units: List of LSTM layer sizes (default: [128, 64])
                - dropout_rate: Dropout rate (default: 0.2)
                - learning_rate: Learning rate (default: 0.001)
                - batch_size: Training batch size (default: 32)
                - epochs: Training epochs (default: 50)
                - output_type: 'regression' or 'classification' (default: 'regression')
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM model. Install with: pip install tensorflow")
        
        default_config = {
            'sequence_length': 50,
            'lstm_units': [128, 64],
            'dropout_rate': 0.2,
            'learning_rate': 0.001,
            'batch_size': 32,
            'epochs': 50,
            'output_type': 'regression',  # or 'classification'
            'patience': 10,  # Early stopping patience
        }
        
        config = {**default_config, **(config or {})}
        super().__init__(ModelType.LSTM, config)
        
        self.sequence_length = config['sequence_length']
        self.scaler_X = None
        self.scaler_y = None
    
    def _build_model(self, n_features: int) -> keras.Model:
        """Build LSTM architecture"""
        model = keras.Sequential()
        
        # Input layer
        model.add(layers.Input(shape=(self.sequence_length, n_features)))
        
        # LSTM layers
        lstm_units = self.config['lstm_units']
        for i, units in enumerate(lstm_units):
            return_sequences = (i < len(lstm_units) - 1)  # Last layer doesn't return sequences
            model.add(layers.LSTM(units, return_sequences=return_sequences))
            model.add(layers.Dropout(self.config['dropout_rate']))
        
        # Output layer
        if self.config['output_type'] == 'regression':
            model.add(layers.Dense(1, activation='linear'))
            loss = 'mse'
            metrics = ['mae']
        else:  # classification
            model.add(layers.Dense(3, activation='softmax'))  # BUY, HOLD, SELL
            loss = 'sparse_categorical_crossentropy'
            metrics = ['accuracy']
        
        # Compile
        optimizer = keras.optimizers.Adam(learning_rate=self.config['learning_rate'])
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        
        return model
    
    def _prepare_sequences(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> Tuple:
        """
        Convert flat features into sequences for LSTM
        
        Args:
            X: Features (n_samples, n_features)
            y: Labels (n_samples,) - optional
            
        Returns:
            (X_seq, y_seq) or just X_seq if y is None
        """
        n_samples = len(X) - self.sequence_length
        n_features = X.shape[1]
        
        X_seq = np.zeros((n_samples, self.sequence_length, n_features))
        
        for i in range(n_samples):
            X_seq[i] = X[i:i + self.sequence_length]
        
        if y is not None:
            y_seq = y[self.sequence_length:]
            return X_seq, y_seq
        
        return X_seq
    
    def _scale_data(self, X: np.ndarray, y: Optional[np.ndarray] = None, 
                   fit: bool = False) -> Tuple:
        """Scale data using standardization"""
        from sklearn.preprocessing import StandardScaler
        
        if fit or self.scaler_X is None:
            self.scaler_X = StandardScaler()
            X_scaled = self.scaler_X.fit_transform(X)
        else:
            X_scaled = self.scaler_X.transform(X)
        
        if y is not None:
            if fit or self.scaler_y is None:
                self.scaler_y = StandardScaler()
                y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
            else:
                y_scaled = self.scaler_y.transform(y.reshape(-1, 1)).ravel()
            return X_scaled, y_scaled
        
        return X_scaled
    
    def train(self, X: np.ndarray, y: np.ndarray,
             validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> Dict[str, Any]:
        """
        Train LSTM model
        
        Args:
            X: Training features (n_samples, n_features)
            y: Training labels (n_samples,)
            validation_data: Optional (X_val, y_val)
            
        Returns:
            Training history
        """
        # Scale data
        X_scaled, y_scaled = self._scale_data(X, y, fit=True)
        
        # Convert to sequences
        X_seq, y_seq = self._prepare_sequences(X_scaled, y_scaled)
        
        # Build model
        n_features = X.shape[1]
        self.model = self._build_model(n_features)
        
        # Prepare validation data
        val_data = None
        if validation_data is not None:
            X_val, y_val = validation_data
            X_val_scaled, y_val_scaled = self._scale_data(X_val, y_val, fit=False)
            X_val_seq, y_val_seq = self._prepare_sequences(X_val_scaled, y_val_scaled)
            val_data = (X_val_seq, y_val_seq)
        
        # Early stopping callback
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if val_data else 'loss',
                patience=self.config['patience'],
                restore_best_weights=True
            )
        ]
        
        # Train
        history = self.model.fit(
            X_seq, y_seq,
            batch_size=self.config['batch_size'],
            epochs=self.config['epochs'],
            validation_data=val_data,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        
        return {
            'loss': history.history['loss'][-1],
            'epochs_trained': len(history.history['loss']),
            'history': history.history
        }
    
    def predict(self, X: np.ndarray) -> MLPrediction:
        """
        Make predictions
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            MLPrediction with results
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Scale and sequence
        X_scaled = self._scale_data(X, fit=False)
        X_seq = self._prepare_sequences(X_scaled)
        
        # Predict
        predictions = self.model.predict(X_seq, verbose=0)
        
        if self.config['output_type'] == 'regression':
            # Inverse scale
            predictions = self.scaler_y.inverse_transform(predictions)
            prediction = predictions[-1, 0]  # Last prediction
            confidence = 0.5  # Default confidence for regression
            probabilities = None
        else:  # classification
            probabilities = predictions[-1]
            prediction = np.argmax(probabilities) - 1  # Convert to -1, 0, 1
            confidence = np.max(probabilities)
        
        return MLPrediction(
            prediction=prediction,
            confidence=confidence,
            probabilities=probabilities,
            metadata={
                'model_type': 'LSTM',
                'sequence_length': self.sequence_length
            }
        )
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model
        
        Args:
            X: Test features
            y: True labels
            
        Returns:
            Evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Scale and sequence
        X_scaled, y_scaled = self._scale_data(X, y, fit=False)
        X_seq, y_seq = self._prepare_sequences(X_scaled, y_scaled)
        
        # Evaluate
        results = self.model.evaluate(X_seq, y_seq, verbose=0)
        
        if self.config['output_type'] == 'regression':
            return {
                'loss': results[0],
                'mae': results[1]
            }
        else:  # classification
            return {
                'loss': results[0],
                'accuracy': results[1]
            }
    
    def save(self, filepath: str) -> bool:
        """Save model to disk"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save Keras model
            self.model.save(str(path / 'model.keras'))
            
            # Save scalers and metadata
            metadata = {
                'config': self.config,
                'scaler_X': self.scaler_X,
                'scaler_y': self.scaler_y,
                'is_trained': self.is_trained,
                'sequence_length': self.sequence_length
            }
            
            with open(path / 'metadata.pkl', 'wb') as f:
                pickle.dump(metadata, f)
            
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load(self, filepath: str) -> bool:
        """Load model from disk"""
        try:
            path = Path(filepath)
            
            # Load Keras model
            self.model = keras.models.load_model(str(path / 'model.keras'))
            
            # Load metadata
            with open(path / 'metadata.pkl', 'rb') as f:
                metadata = pickle.load(f)
            
            self.config = metadata['config']
            self.scaler_X = metadata['scaler_X']
            self.scaler_y = metadata['scaler_y']
            self.is_trained = metadata['is_trained']
            self.sequence_length = metadata['sequence_length']
            
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
