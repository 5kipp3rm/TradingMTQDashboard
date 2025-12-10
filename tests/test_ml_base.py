"""
Comprehensive tests for src.ml.base module
Tests for BaseMLModel, ModelType, and MLPrediction
"""
import pytest
import sys
import importlib.util
from typing import Dict, Any, Optional, Tuple

# Import numpy first to avoid reloading issues
import numpy as np

# Import directly from the base.py file to bypass ml.__init__.py
spec = importlib.util.spec_from_file_location("ml_base", "src/ml/base.py")
ml_base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml_base)

BaseMLModel = ml_base.BaseMLModel
ModelType = ml_base.ModelType
MLPrediction = ml_base.MLPrediction


class TestModelType:
    """Test suite for ModelType enum"""
    
    def test_model_type_values(self):
        """Test all ModelType enum values"""
        assert ModelType.LSTM.value == "lstm"
        assert ModelType.RANDOM_FOREST.value == "random_forest"
        assert ModelType.XGBOOST.value == "xgboost"
        assert ModelType.ENSEMBLE.value == "ensemble"
    
    def test_model_type_members(self):
        """Test ModelType enum members"""
        assert len(ModelType) == 4
        assert ModelType.LSTM in ModelType
        assert ModelType.RANDOM_FOREST in ModelType


class TestMLPrediction:
    """Test suite for MLPrediction dataclass"""
    
    def test_prediction_creation_minimal(self):
        """Test MLPrediction with minimal parameters"""
        pred = MLPrediction(prediction=1, confidence=0.85)
        
        assert pred.prediction == 1
        assert pred.confidence == 0.85
        assert pred.probabilities is None
        assert pred.metadata is None
    
    def test_prediction_creation_full(self):
        """Test MLPrediction with all parameters"""
        probs = np.array([0.2, 0.8])
        metadata = {"model": "test", "version": "1.0"}
        
        pred = MLPrediction(
            prediction=1,
            confidence=0.85,
            probabilities=probs,
            metadata=metadata
        )
        
        assert pred.prediction == 1
        assert pred.confidence == 0.85
        assert np.array_equal(pred.probabilities, probs)
        assert pred.metadata == metadata
    
    def test_prediction_different_types(self):
        """Test MLPrediction with different prediction types"""
        # Integer prediction
        pred_int = MLPrediction(prediction=5, confidence=0.9)
        assert isinstance(pred_int.prediction, int)
        
        # Float prediction
        pred_float = MLPrediction(prediction=1.234, confidence=0.75)
        assert isinstance(pred_float.prediction, float)
        
        # String prediction
        pred_str = MLPrediction(prediction="BUY", confidence=0.6)
        assert isinstance(pred_str.prediction, str)
        
        # Array prediction
        pred_array = MLPrediction(prediction=np.array([1, 2, 3]), confidence=0.8)
        assert isinstance(pred_array.prediction, np.ndarray)


class ConcreteMLModel(BaseMLModel):
    """Concrete implementation of BaseMLModel for testing"""
    
    def train(self, X: np.ndarray, y: np.ndarray, 
             validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> Dict[str, Any]:
        """Concrete train implementation"""
        self.is_trained = True
        self.model = "trained_model"
        return {"loss": 0.1, "accuracy": 0.95}
    
    def predict(self, X: np.ndarray) -> MLPrediction:
        """Concrete predict implementation"""
        predictions = np.ones(X.shape[0])
        return MLPrediction(
            prediction=predictions,
            confidence=0.9,
            probabilities=np.array([0.1, 0.9]),
            metadata={"samples": X.shape[0]}
        )
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Concrete evaluate implementation"""
        return {"accuracy": 0.92, "precision": 0.88, "recall": 0.90}
    
    def save(self, filepath: str) -> bool:
        """Concrete save implementation"""
        return True
    
    def load(self, filepath: str) -> bool:
        """Concrete load implementation"""
        self.is_trained = True
        return True
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Override to return feature importance"""
        return {"feature1": 0.5, "feature2": 0.3, "feature3": 0.2}


class TestBaseMLModel:
    """Test suite for BaseMLModel abstract class"""
    
    def test_initialization(self):
        """Test BaseMLModel initialization"""
        config = {"param1": 10, "param2": "value"}
        model = ConcreteMLModel(ModelType.LSTM, config)
        
        assert model.model_type == ModelType.LSTM
        assert model.config == config
        assert model.model is None
        assert model.is_trained is False
        assert model.feature_names == []
        assert model.metadata == {}
    
    def test_initialization_different_types(self):
        """Test initialization with different model types"""
        model_lstm = ConcreteMLModel(ModelType.LSTM, {})
        assert model_lstm.model_type == ModelType.LSTM
        
        model_rf = ConcreteMLModel(ModelType.RANDOM_FOREST, {})
        assert model_rf.model_type == ModelType.RANDOM_FOREST
        
        model_xgb = ConcreteMLModel(ModelType.XGBOOST, {})
        assert model_xgb.model_type == ModelType.XGBOOST
        
        model_ens = ConcreteMLModel(ModelType.ENSEMBLE, {})
        assert model_ens.model_type == ModelType.ENSEMBLE
    
    def test_train(self):
        """Test train method"""
        model = ConcreteMLModel(ModelType.LSTM, {})
        X = np.random.rand(100, 10)
        y = np.random.randint(0, 2, 100)
        
        metrics = model.train(X, y)
        
        assert model.is_trained is True
        assert model.model is not None
        assert isinstance(metrics, dict)
        assert "loss" in metrics
        assert "accuracy" in metrics
    
    def test_train_with_validation(self):
        """Test train with validation data"""
        model = ConcreteMLModel(ModelType.RANDOM_FOREST, {})
        X_train = np.random.rand(100, 10)
        y_train = np.random.randint(0, 2, 100)
        X_val = np.random.rand(20, 10)
        y_val = np.random.randint(0, 2, 20)
        
        metrics = model.train(X_train, y_train, validation_data=(X_val, y_val))
        
        assert model.is_trained is True
        assert isinstance(metrics, dict)
    
    def test_predict(self):
        """Test predict method"""
        model = ConcreteMLModel(ModelType.LSTM, {})
        model.is_trained = True
        
        X = np.random.rand(10, 5)
        prediction = model.predict(X)
        
        assert isinstance(prediction, MLPrediction)
        assert prediction.prediction is not None
        assert prediction.confidence > 0
    
    def test_evaluate(self):
        """Test evaluate method"""
        model = ConcreteMLModel(ModelType.XGBOOST, {})
        model.is_trained = True
        
        X = np.random.rand(50, 10)
        y = np.random.randint(0, 2, 50)
        
        metrics = model.evaluate(X, y)
        
        assert isinstance(metrics, dict)
        assert "accuracy" in metrics
        assert all(0 <= v <= 1 for v in metrics.values())
    
    def test_save(self):
        """Test save method"""
        model = ConcreteMLModel(ModelType.LSTM, {})
        model.is_trained = True
        
        result = model.save("/tmp/model.pkl")
        assert result is True
    
    def test_load(self):
        """Test load method"""
        model = ConcreteMLModel(ModelType.LSTM, {})
        
        result = model.load("/tmp/model.pkl")
        assert result is True
        assert model.is_trained is True
    
    def test_get_feature_importance(self):
        """Test get_feature_importance method"""
        model = ConcreteMLModel(ModelType.RANDOM_FOREST, {})
        
        importance = model.get_feature_importance()
        
        assert isinstance(importance, dict)
        assert len(importance) == 3
        assert "feature1" in importance
        assert sum(importance.values()) == pytest.approx(1.0)
    
    def test_get_feature_importance_default(self):
        """Test default get_feature_importance returns None"""
        # Create a model without overriding get_feature_importance
        class MinimalModel(BaseMLModel):
            def train(self, X, y, validation_data=None):
                return {}
            def predict(self, X):
                return MLPrediction(prediction=0, confidence=0.5)
            def evaluate(self, X, y):
                return {}
            def save(self, filepath):
                return True
            def load(self, filepath):
                return True
        
        model = MinimalModel(ModelType.LSTM, {})
        assert model.get_feature_importance() is None
    
    def test_repr_untrained(self):
        """Test __repr__ for untrained model"""
        model = ConcreteMLModel(ModelType.LSTM, {})
        
        repr_str = repr(model)
        assert "ConcreteMLModel" in repr_str
        assert "lstm" in repr_str
        assert "untrained" in repr_str
    
    def test_repr_trained(self):
        """Test __repr__ for trained model"""
        model = ConcreteMLModel(ModelType.RANDOM_FOREST, {})
        model.is_trained = True
        
        repr_str = repr(model)
        assert "ConcreteMLModel" in repr_str
        assert "random_forest" in repr_str
        assert "trained" in repr_str
    
    def test_abstract_class_cannot_instantiate(self):
        """Test that BaseMLModel cannot be instantiated directly"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseMLModel(ModelType.LSTM, {})
    
    def test_model_state_persistence(self):
        """Test that model state persists across method calls"""
        model = ConcreteMLModel(ModelType.LSTM, {"layers": 3})
        
        # Initially untrained
        assert model.is_trained is False
        assert model.model is None
        
        # Train the model
        X = np.random.rand(50, 5)
        y = np.random.randint(0, 2, 50)
        model.train(X, y)
        
        # State should persist
        assert model.is_trained is True
        assert model.model is not None
        assert model.config["layers"] == 3
    
    def test_feature_names_attribute(self):
        """Test feature_names attribute"""
        model = ConcreteMLModel(ModelType.LSTM, {})
        
        assert model.feature_names == []
        
        # Add feature names
        model.feature_names = ["f1", "f2", "f3"]
        assert len(model.feature_names) == 3
        assert "f1" in model.feature_names
    
    def test_metadata_attribute(self):
        """Test metadata attribute"""
        model = ConcreteMLModel(ModelType.XGBOOST, {})
        
        assert model.metadata == {}
        
        # Add metadata
        model.metadata["training_date"] = "2025-12-08"
        model.metadata["version"] = "1.0"
        
        assert model.metadata["training_date"] == "2025-12-08"
        assert model.metadata["version"] == "1.0"
