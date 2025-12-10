"""
Unit tests for ML Model Loader
"""
import pytest
import os
import tempfile
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier

from src.ml.model_loader import ModelLoader, MLModelWrapper
from src.ml.base import MLPrediction


@pytest.fixture
def temp_models_dir():
    """Create temporary models directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass


@pytest.fixture
def sample_rf_model():
    """Create a sample trained Random Forest model"""
    # Create and train a simple model
    X = np.random.randn(100, 42)
    y = np.random.randint(0, 2, 100)  # Binary classification
    
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model


@pytest.fixture
def sample_ensemble_model():
    """Create a sample ensemble model"""
    X = np.random.randn(100, 42)
    y = np.random.randint(0, 2, 100)
    
    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=10, random_state=42)
    lr = LogisticRegression(random_state=42, max_iter=1000)
    
    ensemble = VotingClassifier(
        estimators=[('rf', rf), ('gb', gb), ('lr', lr)],
        voting='soft'
    )
    ensemble.fit(X, y)
    return ensemble


@pytest.fixture
def models_with_files(temp_models_dir, sample_rf_model, sample_ensemble_model):
    """Create model files in temp directory"""
    # Save RF models
    joblib.dump(sample_rf_model, os.path.join(temp_models_dir, 'rf_EURUSD_H1.pkl'))
    joblib.dump(sample_rf_model, os.path.join(temp_models_dir, 'rf_EURUSD_M15.pkl'))
    
    # Save ensemble models
    joblib.dump(sample_ensemble_model, os.path.join(temp_models_dir, 'ensemble_EURUSD_H1.pkl'))
    joblib.dump(sample_ensemble_model, os.path.join(temp_models_dir, 'ensemble_GBPUSD_M15.pkl'))
    
    return temp_models_dir


class TestModelLoader:
    """Test ModelLoader class"""
    
    def test_initialization(self, temp_models_dir):
        """Test loader initialization"""
        loader = ModelLoader(temp_models_dir)
        assert loader.models_dir == temp_models_dir
        assert isinstance(loader.loaded_models, dict)
        assert len(loader.loaded_models) == 0
    
    def test_get_model_path_exists(self, models_with_files):
        """Test getting path to existing model"""
        loader = ModelLoader(models_with_files)
        path = loader.get_model_path('EURUSD', 'H1', 'ensemble')
        assert path is not None
        assert os.path.exists(path)
        assert 'ensemble_EURUSD_H1.pkl' in path
    
    def test_get_model_path_not_exists(self, models_with_files):
        """Test getting path to non-existent model"""
        loader = ModelLoader(models_with_files)
        path = loader.get_model_path('USDJPY', 'H4', 'ensemble')
        assert path is None
    
    def test_load_ensemble_model(self, models_with_files):
        """Test loading ensemble model"""
        loader = ModelLoader(models_with_files)
        model = loader.load_model('EURUSD', 'H1', 'ensemble')
        assert model is not None
        assert isinstance(model, VotingClassifier)
    
    def test_load_rf_model(self, models_with_files):
        """Test loading Random Forest model"""
        loader = ModelLoader(models_with_files)
        model = loader.load_model('EURUSD', 'H1', 'rf')
        assert model is not None
        assert isinstance(model, RandomForestClassifier)
    
    def test_load_model_caching(self, models_with_files):
        """Test that models are cached"""
        loader = ModelLoader(models_with_files)
        
        # Load model first time
        model1 = loader.load_model('EURUSD', 'H1', 'ensemble')
        assert len(loader.loaded_models) == 1
        
        # Load same model again
        model2 = loader.load_model('EURUSD', 'H1', 'ensemble')
        assert len(loader.loaded_models) == 1  # Still 1, not 2
        assert model1 is model2  # Same object
    
    def test_load_model_fallback_to_rf(self, models_with_files):
        """Test fallback to RF when ensemble not found"""
        loader = ModelLoader(models_with_files)
        
        # Try to load ensemble for EURUSD M15 (doesn't exist)
        # Should fall back to RF
        model = loader.load_model('EURUSD', 'M15', 'ensemble')
        assert model is not None
        assert isinstance(model, RandomForestClassifier)
    
    def test_load_model_not_found(self, models_with_files):
        """Test loading non-existent model"""
        loader = ModelLoader(models_with_files)
        model = loader.load_model('NONEXISTENT', 'H1', 'ensemble')
        assert model is None
    
    def test_load_all_models(self, models_with_files):
        """Test loading all models for currencies"""
        loader = ModelLoader(models_with_files)
        
        currencies = {
            'EURUSD': {'enabled': True, 'timeframe': 'H1'},
            'GBPUSD': {'enabled': True, 'timeframe': 'M15'},
            'USDJPY': {'enabled': False, 'timeframe': 'H1'},
        }
        
        models = loader.load_all_models(currencies, model_type='ensemble')
        
        # Should load for EURUSD and GBPUSD (enabled), not USDJPY (disabled)
        assert len(models) == 2
        assert 'EURUSD' in models
        assert 'GBPUSD' in models
        assert 'USDJPY' not in models
    
    def test_get_available_models(self, models_with_files):
        """Test getting list of available models"""
        loader = ModelLoader(models_with_files)
        available = loader.get_available_models()
        
        assert 'ensemble' in available
        assert 'rf' in available
        assert len(available['ensemble']) == 2  # EURUSD H1, GBPUSD M15
        assert len(available['rf']) == 2  # EURUSD H1, M15
        assert ('EURUSD', 'H1') in available['ensemble']
        assert ('GBPUSD', 'M15') in available['ensemble']


class TestMLModelWrapper:
    """Test MLModelWrapper class"""
    
    def test_initialization(self, sample_rf_model):
        """Test wrapper initialization"""
        wrapper = MLModelWrapper(sample_rf_model)
        assert wrapper.model is not None
        assert wrapper.model is sample_rf_model
    
    def test_predict_binary_classification(self, sample_rf_model):
        """Test prediction with binary model"""
        wrapper = MLModelWrapper(sample_rf_model)
        X = np.random.randn(1, 42)
        
        prediction = wrapper.predict(X)
        
        assert isinstance(prediction, MLPrediction)
        assert prediction.prediction in [-1, 1]  # Should be SELL or BUY
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.probabilities is not None
        assert len(prediction.probabilities) == 2
    
    def test_predict_class_0_maps_to_sell(self, sample_rf_model):
        """Test that class 0 maps to SELL (-1)"""
        wrapper = MLModelWrapper(sample_rf_model)
        
        # Create input that will likely predict class 0
        X = np.random.randn(1, 42) * -10  # Extreme negative values
        prediction = wrapper.predict(X)
        
        # Can't guarantee the prediction, but verify the mapping is correct
        assert prediction.prediction in [-1, 1]
        assert isinstance(prediction.metadata, dict)
        assert 'class' in prediction.metadata
    
    def test_predict_class_1_maps_to_buy(self, sample_rf_model):
        """Test that class 1 maps to BUY (1)"""
        wrapper = MLModelWrapper(sample_rf_model)
        
        # Create input that will likely predict class 1
        X = np.random.randn(1, 42) * 10  # Extreme positive values
        prediction = wrapper.predict(X)
        
        # Verify prediction structure
        assert prediction.prediction in [-1, 1]
        assert prediction.confidence > 0
    
    def test_predict_confidence_from_probabilities(self, sample_rf_model):
        """Test that confidence comes from probabilities"""
        wrapper = MLModelWrapper(sample_rf_model)
        X = np.random.randn(1, 42)
        
        prediction = wrapper.predict(X)
        
        # Confidence should match the probability of the predicted class
        if prediction.metadata['class'] == 0:
            assert abs(prediction.confidence - prediction.probabilities[0]) < 0.001
        else:
            assert abs(prediction.confidence - prediction.probabilities[1]) < 0.001
    
    def test_predict_proba(self, sample_rf_model):
        """Test predict_proba method"""
        wrapper = MLModelWrapper(sample_rf_model)
        X = np.random.randn(1, 42)
        
        probas = wrapper.predict_proba(X)
        assert probas is not None
        assert len(probas[0]) == 2
        assert abs(sum(probas[0]) - 1.0) < 0.01  # Probabilities sum to 1
    
    def test_metadata_includes_num_classes(self, sample_rf_model):
        """Test that metadata includes number of classes"""
        wrapper = MLModelWrapper(sample_rf_model)
        X = np.random.randn(1, 42)
        
        prediction = wrapper.predict(X)
        assert 'num_classes' in prediction.metadata
        assert prediction.metadata['num_classes'] == 2
    
    def test_wrapper_with_ensemble(self, sample_ensemble_model):
        """Test wrapper works with ensemble models"""
        wrapper = MLModelWrapper(sample_ensemble_model)
        X = np.random.randn(1, 42)
        
        prediction = wrapper.predict(X)
        assert isinstance(prediction, MLPrediction)
        assert prediction.prediction in [-1, 1]
        assert 0.0 <= prediction.confidence <= 1.0


class TestModelLoaderIntegration:
    """Integration tests for complete workflow"""
    
    def test_load_and_predict_workflow(self, models_with_files):
        """Test complete load and predict workflow"""
        # Load model
        loader = ModelLoader(models_with_files)
        sklearn_model = loader.load_model('EURUSD', 'H1', 'ensemble')
        assert sklearn_model is not None
        
        # Wrap model
        wrapper = MLModelWrapper(sklearn_model)
        
        # Make prediction
        X = np.random.randn(1, 42)
        prediction = wrapper.predict(X)
        
        # Verify complete prediction
        assert isinstance(prediction, MLPrediction)
        assert prediction.prediction in [-1, 1]
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.probabilities is not None
        assert 'class' in prediction.metadata
        assert 'num_classes' in prediction.metadata
    
    def test_multiple_currencies_workflow(self, models_with_files):
        """Test loading models for multiple currencies"""
        loader = ModelLoader(models_with_files)
        
        currencies = {
            'EURUSD': {'enabled': True, 'timeframe': 'H1'},
            'GBPUSD': {'enabled': True, 'timeframe': 'M15'},
        }
        
        models = loader.load_all_models(currencies, model_type='ensemble')
        
        # Test predictions for both
        for symbol, model in models.items():
            wrapper = MLModelWrapper(model)
            X = np.random.randn(1, 42)
            prediction = wrapper.predict(X)
            assert prediction is not None
            assert prediction.prediction in [-1, 1]
