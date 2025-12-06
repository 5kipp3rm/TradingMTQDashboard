"""
Random Forest Classifier for Trade Signal Classification
Classifies trading signals as BUY, SELL, or HOLD
"""
import numpy as np
import pickle
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from sklearn.ensemble import RandomForestClassifier as SKRandomForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .base import BaseMLModel, ModelType, MLPrediction


class RandomForestClassifier(BaseMLModel):
    """
    Random Forest model for signal classification
    
    Classifies market conditions into:
    - BUY (1): Bullish signal
    - HOLD (0): Neutral signal
    - SELL (-1): Bearish signal
    
    Provides feature importance analysis and probability estimates.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Random Forest model
        
        Args:
            config: Model configuration
                - n_estimators: Number of trees (default: 100)
                - max_depth: Maximum tree depth (default: 10)
                - min_samples_split: Min samples to split (default: 5)
                - min_samples_leaf: Min samples per leaf (default: 2)
                - max_features: Features to consider (default: 'sqrt')
                - random_state: Random seed (default: 42)
                - n_jobs: Parallel jobs (default: -1)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required. Install with: pip install scikit-learn")
        
        default_config = {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'max_features': 'sqrt',
            'random_state': 42,
            'n_jobs': -1,
            'scale_features': True,
        }
        
        config = {**default_config, **(config or {})}
        super().__init__(ModelType.RANDOM_FOREST, config)
        
        self.scaler = None
        self._feature_importance = None
    
    def train(self, X: np.ndarray, y: np.ndarray,
             validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> Dict[str, Any]:
        """
        Train Random Forest classifier
        
        Args:
            X: Training features (n_samples, n_features)
            y: Training labels (n_samples,) - values in {-1, 0, 1}
            validation_data: Optional (X_val, y_val) for validation metrics
            
        Returns:
            Training metrics
        """
        # Convert labels to 0, 1, 2 for sklearn
        y_train = self._convert_labels(y)
        
        # Scale features if enabled
        if self.config['scale_features']:
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # Create and train model
        self.model = SKRandomForest(
            n_estimators=self.config['n_estimators'],
            max_depth=self.config['max_depth'],
            min_samples_split=self.config['min_samples_split'],
            min_samples_leaf=self.config['min_samples_leaf'],
            max_features=self.config['max_features'],
            random_state=self.config['random_state'],
            n_jobs=self.config['n_jobs'],
            verbose=0
        )
        
        self.model.fit(X_scaled, y_train)
        self.is_trained = True
        
        # Calculate feature importance
        self._feature_importance = self.model.feature_importances_
        
        # Training metrics
        train_score = self.model.score(X_scaled, y_train)
        metrics = {
            'train_accuracy': train_score,
            'n_features': X.shape[1],
            'n_samples': X.shape[0]
        }
        
        # Validation metrics
        if validation_data is not None:
            X_val, y_val = validation_data
            val_metrics = self.evaluate(X_val, y_val)
            metrics.update({'val_' + k: v for k, v in val_metrics.items()})
        
        return metrics
    
    def predict(self, X: np.ndarray) -> MLPrediction:
        """
        Predict trading signal
        
        Args:
            X: Features (n_samples, n_features) or (n_features,)
            
        Returns:
            MLPrediction with signal and confidence
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Handle single sample
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Scale features
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # Predict probabilities
        probabilities = self.model.predict_proba(X_scaled)
        
        # Get prediction for last sample
        probs = probabilities[-1]
        predicted_class = np.argmax(probs)
        confidence = probs[predicted_class]
        
        # Convert back to -1, 0, 1
        signal = self._convert_labels_inverse(np.array([predicted_class]))[0]
        
        return MLPrediction(
            prediction=signal,
            confidence=confidence,
            probabilities=probs,
            metadata={
                'model_type': 'RandomForest',
                'class_labels': ['SELL', 'HOLD', 'BUY']
            }
        )
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Args:
            X: Test features
            y: True labels in {-1, 0, 1}
            
        Returns:
            Evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Convert labels and scale features
        y_test = self._convert_labels(y)
        
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # Predict
        y_pred = self.model.predict(X_scaled)
        accuracy = self.model.score(X_scaled, y_test)
        
        # Calculate per-class metrics
        from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
        
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average='weighted', zero_division=0
        )
        
        cm = confusion_matrix(y_test, y_pred)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm.tolist()
        }
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance scores
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained or self._feature_importance is None:
            return None
        
        if not self.feature_names:
            # Use generic names if feature names not set
            self.feature_names = [f'feature_{i}' for i in range(len(self._feature_importance))]
        
        importance_dict = {
            name: float(importance)
            for name, importance in zip(self.feature_names, self._feature_importance)
        }
        
        # Sort by importance
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    
    def save(self, filepath: str) -> bool:
        """Save model to disk"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'config': self.config,
                'is_trained': self.is_trained,
                'feature_names': self.feature_names,
                'feature_importance': self._feature_importance
            }
            
            with open(path / 'rf_model.pkl', 'wb') as f:
                pickle.dump(model_data, f)
            
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load(self, filepath: str) -> bool:
        """Load model from disk"""
        try:
            path = Path(filepath)
            
            with open(path / 'rf_model.pkl', 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.config = model_data['config']
            self.is_trained = model_data['is_trained']
            self.feature_names = model_data['feature_names']
            self._feature_importance = model_data['feature_importance']
            
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    @staticmethod
    def _convert_labels(y: np.ndarray) -> np.ndarray:
        """Convert -1, 0, 1 to 0, 1, 2 for sklearn"""
        return y + 1
    
    @staticmethod
    def _convert_labels_inverse(y: np.ndarray) -> np.ndarray:
        """Convert 0, 1, 2 back to -1, 0, 1"""
        return y - 1
