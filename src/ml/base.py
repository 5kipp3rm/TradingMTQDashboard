"""
Base classes for ML models in trading system
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass


class ModelType(Enum):
    """Types of ML models"""
    LSTM = "lstm"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    ENSEMBLE = "ensemble"


@dataclass
class MLPrediction:
    """ML model prediction result"""
    prediction: Any  # Predicted value or class
    confidence: float  # Confidence score (0-1)
    probabilities: Optional[np.ndarray] = None  # Class probabilities (for classification)
    metadata: Optional[Dict[str, Any]] = None  # Additional prediction info


class BaseMLModel(ABC):
    """
    Abstract base class for all ML models
    
    All models must implement:
    - train(): Train the model on data
    - predict(): Make predictions
    - evaluate(): Evaluate model performance
    - save(): Save trained model
    - load(): Load trained model
    """
    
    def __init__(self, model_type: ModelType, config: Dict[str, Any]):
        """
        Initialize ML model
        
        Args:
            model_type: Type of model
            config: Model configuration parameters
        """
        self.model_type = model_type
        self.config = config
        self.model = None
        self.is_trained = False
        self.feature_names = []
        self.metadata = {}
    
    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray, 
             validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> Dict[str, Any]:
        """
        Train the model
        
        Args:
            X: Training features (n_samples, n_features)
            y: Training labels (n_samples,)
            validation_data: Optional validation (X_val, y_val)
            
        Returns:
            Training metrics dictionary
        """
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> MLPrediction:
        """
        Make predictions
        
        Args:
            X: Features to predict (n_samples, n_features)
            
        Returns:
            MLPrediction with results
        """
        pass
    
    @abstractmethod
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Args:
            X: Test features
            y: True labels
            
        Returns:
            Evaluation metrics
        """
        pass
    
    @abstractmethod
    def save(self, filepath: str) -> bool:
        """
        Save trained model to disk
        
        Args:
            filepath: Path to save model
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def load(self, filepath: str) -> bool:
        """
        Load trained model from disk
        
        Args:
            filepath: Path to load model from
            
        Returns:
            True if successful
        """
        pass
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance scores (if supported)
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        return None
    
    def __repr__(self) -> str:
        status = "trained" if self.is_trained else "untrained"
        return f"<{self.__class__.__name__} ({self.model_type.value}) - {status}>"
