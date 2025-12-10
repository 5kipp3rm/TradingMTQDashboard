"""
Test ML Integration
Quick test to verify ensemble models load and predict correctly
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ml import ModelLoader, MLModelWrapper
import numpy as np

def test_ml_integration():
    """Test that ML models load and predict"""
    
    print("=" * 80)
    print("  ML INTEGRATION TEST")
    print("=" * 80)
    
    # Initialize model loader
    loader = ModelLoader("models")
    
    # Show available models
    print("\n1. Checking available models...")
    loader.print_available_models()
    
    # Load EURUSD H1 ensemble model
    print("\n2. Loading EURUSD H1 ensemble model...")
    model = loader.load_model("EURUSD", "H1", "ensemble")
    
    if not model:
        print("❌ Failed to load model!")
        return False
    
    print("✅ Model loaded successfully!")
    
    # Wrap model
    print("\n3. Wrapping model for bot interface...")
    wrapped_model = MLModelWrapper(model)
    print("✅ Model wrapped!")
    
    # Create dummy features (42 features - same as FeatureEngineer generates)
    print("\n4. Testing prediction with dummy features...")
    X = np.random.randn(1, 42)  # 1 sample, 42 features (FeatureEngineer output)
    
    try:
        prediction = wrapped_model.predict(X)
        
        print(f"\n📊 Prediction Results:")
        print(f"   Prediction: {prediction.prediction}")
        print(f"   Confidence: {prediction.confidence:.4f}")
        print(f"   Class: {prediction.metadata.get('class', 'N/A')}")
        print(f"   Num Classes: {prediction.metadata.get('num_classes', 'N/A')}")
        
        if prediction.probabilities is not None:
            if len(prediction.probabilities) == 2:
                print(f"   Probabilities: DOWN={prediction.probabilities[0]:.3f}, "
                      f"UP={prediction.probabilities[1]:.3f}")
            elif len(prediction.probabilities) == 3:
                print(f"   Probabilities: DOWN={prediction.probabilities[0]:.3f}, "
                      f"NEUTRAL={prediction.probabilities[1]:.3f}, "
                      f"UP={prediction.probabilities[2]:.3f}")
        
        # Interpret prediction
        if prediction.prediction == -1:
            signal = "SELL (DOWN)"
        elif prediction.prediction == 1:
            signal = "BUY (UP)"
        else:
            signal = "HOLD (NEUTRAL)"
        
        print(f"\n   → Signal: {signal}")
        print(f"   → Confidence: {prediction.confidence*100:.1f}%")
        
        print("\n✅ ML Integration Test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ml_integration()
    sys.exit(0 if success else 1)
