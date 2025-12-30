"""
ML Model Loader
Automatically loads trained models for each currency/timeframe combination
"""
import os
import joblib
import warnings
from typing import Dict, Optional
from src.utils.unified_logger import UnifiedLogger

# Suppress sklearn feature name warnings for ensemble models
warnings.filterwarnings('ignore', message='X does not have valid feature names')

logger = UnifiedLogger.get_logger(__name__)


class ModelLoader:
    """Manages loading of trained ML models"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.loaded_models = {}
    
    def get_model_path(self, symbol: str, timeframe: str, model_type: str = "ensemble") -> Optional[str]:
        """
        Get path to model file for given symbol/timeframe
        
        Args:
            symbol: Currency pair (e.g., EURUSD)
            timeframe: Timeframe (e.g., H1, M15)
            model_type: Type of model ("ensemble" or "rf")
        
        Returns:
            Path to model file or None if not found
        """
        model_filename = f"{model_type}_{symbol}_{timeframe}.pkl"
        model_path = os.path.join(self.models_dir, model_filename)
        
        if os.path.exists(model_path):
            return model_path
        
        logger.debug(f"Model not found: {model_path}")
        return None
    
    def load_model(self, symbol: str, timeframe: str, model_type: str = "ensemble"):
        """
        Load trained model for symbol/timeframe
        
        Args:
            symbol: Currency pair
            timeframe: Timeframe
            model_type: "ensemble" (default) or "rf"
        
        Returns:
            Loaded model or None if not found
        """
        cache_key = f"{model_type}_{symbol}_{timeframe}"
        
        # Return cached model if already loaded
        if cache_key in self.loaded_models:
            logger.debug(f"Using cached model: {cache_key}")
            return self.loaded_models[cache_key]
        
        # Get model path
        model_path = self.get_model_path(symbol, timeframe, model_type)
        if not model_path:
            # Try fallback to RF if ensemble not found
            if model_type == "ensemble":
                logger.info(f"Ensemble model not found for {symbol} {timeframe}, trying Random Forest...")
                return self.load_model(symbol, timeframe, "rf")
            return None
        
        # Load model
        try:
            model = joblib.load(model_path)
            self.loaded_models[cache_key] = model
            
            model_size_mb = os.path.getsize(model_path) / (1024 * 1024)
            logger.info(f"✅ Loaded {model_type.upper()} model for {symbol} {timeframe} ({model_size_mb:.2f} MB)")
            
            return model
        
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            return None
    
    def load_all_models(self, currencies: Dict, model_type: str = "ensemble") -> Dict:
        """
        Load models for all enabled currencies
        
        Args:
            currencies: Dict of currency configs from yaml
            model_type: "ensemble" or "rf"
        
        Returns:
            Dict mapping symbol -> model
        """
        models = {}
        
        for symbol, config in currencies.items():
            if not config.get('enabled', False):
                continue
            
            timeframe = config.get('timeframe', 'H1')
            model = self.load_model(symbol, timeframe, model_type)
            
            if model:
                models[symbol] = model
                logger.info(f"  {symbol} ({timeframe}): {model_type.upper()} model loaded")
            else:
                logger.warning(f"  {symbol} ({timeframe}): No model found, trading without ML")
        
        return models
    
    def get_available_models(self) -> Dict[str, list]:
        """
        List all available models in models directory
        
        Returns:
            Dict with 'ensemble' and 'rf' keys, each containing list of (symbol, timeframe) tuples
        """
        if not os.path.exists(self.models_dir):
            return {'ensemble': [], 'rf': []}
        
        ensemble_models = []
        rf_models = []
        
        for filename in os.listdir(self.models_dir):
            if not filename.endswith('.pkl'):
                continue
            
            # Parse filename: ensemble_EURUSD_H1.pkl or rf_EURUSD_M15.pkl
            parts = filename.replace('.pkl', '').split('_')
            
            if len(parts) >= 3:
                model_type = parts[0]
                symbol = parts[1]
                timeframe = parts[2]
                
                if model_type == 'ensemble':
                    ensemble_models.append((symbol, timeframe))
                elif model_type == 'rf':
                    rf_models.append((symbol, timeframe))
        
        return {
            'ensemble': sorted(ensemble_models),
            'rf': sorted(rf_models)
        }
    
    def print_available_models(self):
        """Print summary of available models"""
        models = self.get_available_models()
        
        logger.info("=" * 80)
        logger.info("  AVAILABLE ML MODELS")
        logger.info("=" * 80)
        
        if models['ensemble']:
            logger.info("Ensemble Models (Recommended):")
            for symbol, tf in models['ensemble']:
                path = self.get_model_path(symbol, tf, 'ensemble')
                size_mb = os.path.getsize(path) / (1024 * 1024)
                logger.info(f"  ✓ {symbol:8} {tf:4} ({size_mb:.2f} MB)")
        else:
            logger.info("  No ensemble models found")
        
        if models['rf']:
            logger.info("\nRandom Forest Models:")
            for symbol, tf in models['rf']:
                # Skip if ensemble exists for same symbol/tf
                if (symbol, tf) in models['ensemble']:
                    continue
                path = self.get_model_path(symbol, tf, 'rf')
                size_mb = os.path.getsize(path) / (1024 * 1024)
                logger.info(f"  ✓ {symbol:8} {tf:4} ({size_mb:.2f} MB)")
        
        total_models = len(models['ensemble']) + len(models['rf'])
        logger.info(f"\nTotal: {total_models} models ready for trading")
        logger.info("=" * 80)


class MLModelWrapper:
    """
    Wrapper to make sklearn models compatible with the existing ML interface
    Provides predict() method that returns MLPrediction objects
    """
    
    def __init__(self, sklearn_model):
        self.model = sklearn_model
    
    def predict(self, X):
        """
        Make prediction on features
        
        Args:
            X: Feature array (numpy or pandas)
        
        Returns:
            MLPrediction object with prediction (-1, 0, 1) and confidence
        """
        from src.ml.base import MLPrediction
        
        # Get class prediction
        prediction_class = self.model.predict(X)[0]
        
        # Initialize variables
        probabilities = None
        prediction_value = 0
        confidence = 0.5
        
        # Get probabilities if available
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(X)[0]
            num_classes = len(probabilities)
            
            if num_classes == 2:
                # Binary classification: Class 0 = DOWN, Class 1 = UP
                if prediction_class == 0:
                    prediction_value = -1  # SELL
                    confidence = probabilities[0]
                else:  # prediction_class == 1
                    prediction_value = 1  # BUY
                    confidence = probabilities[1]
            
            elif num_classes == 3:
                # Multi-class: Class 0 = DOWN, Class 1 = NEUTRAL, Class 2 = UP
                if prediction_class == 0:
                    prediction_value = -1
                    confidence = probabilities[0]
                elif prediction_class == 2:
                    prediction_value = 1
                    confidence = probabilities[2]
                else:  # Class 1 = NEUTRAL
                    prediction_value = 0
                    confidence = probabilities[1]
            else:
                # Unknown number of classes - use simple mapping
                prediction_value = 1 if prediction_class == 1 else -1
                confidence = 0.6
        else:
            # No probabilities - use simple mapping
            if prediction_class == 0:
                prediction_value = -1
                confidence = 0.7
            elif prediction_class == 1:
                prediction_value = 1
                confidence = 0.7
            else:
                prediction_value = 0
                confidence = 0.6
        
        return MLPrediction(
            prediction=prediction_value,
            confidence=confidence,
            probabilities=probabilities,
            metadata={
                'class': int(prediction_class),
                'num_classes': len(probabilities) if probabilities is not None else None
            }
        )
    
    def predict_proba(self, X):
        """Get prediction probabilities"""
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            # Fallback for models without predict_proba
            predictions = self.model.predict(X)
            probs = []
            for pred in predictions:
                if pred == 0:  # DOWN
                    probs.append([0.7, 0.2, 0.1])
                elif pred == 1:  # NEUTRAL
                    probs.append([0.2, 0.6, 0.2])
                else:  # UP
                    probs.append([0.1, 0.2, 0.7])
            return probs
    
    def load(self, path):
        """Load model from file"""
        try:
            self.model = joblib.load(path)
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
