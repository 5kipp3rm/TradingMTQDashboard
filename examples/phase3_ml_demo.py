"""
Phase 3 ML Demo - Train and Test ML Models
Demonstrates the complete ML pipeline:
1. Data collection and preprocessing
2. Feature engineering
3. Model training (Random Forest & LSTM)
4. Model evaluation
5. Live prediction example
"""
import numpy as np
import pandas as pd
from pathlib import Path

# Check ML dependencies
print("=" * 80)
print("  PHASE 3: MACHINE LEARNING DEMONSTRATION")
print("=" * 80)

print("\n📦 Checking ML dependencies...")

from src.ml import RF_AVAILABLE, LSTM_AVAILABLE

if RF_AVAILABLE:
    print("✓ scikit-learn installed - Random Forest available")
    from src.ml import RandomForestClassifier
else:
    print("✗ scikit-learn not installed")
    print("  Install with: pip install scikit-learn")

if LSTM_AVAILABLE:
    print("✓ TensorFlow installed - LSTM available")
    from src.ml import LSTMPricePredictor
else:
    print("✗ TensorFlow not installed")
    print("  Install with: pip install tensorflow")

if not (RF_AVAILABLE or LSTM_AVAILABLE):
    print("\n⚠️  No ML libraries installed!")
    print("Install ML dependencies with:")
    print("  pip install -r requirements-ml.txt")
    exit(1)

from src.ml import FeatureEngineer


def generate_sample_data(n_samples=1000):
    """Generate synthetic OHLC data for demonstration"""
    print("\n📊 Generating sample OHLC data...")
    
    # Create realistic price movements
    np.random.seed(42)
    
    timestamps = pd.date_range('2023-01-01', periods=n_samples, freq='1H')
    
    # Start price
    price = 1.0500
    prices = [price]
    
    # Random walk with trend
    for i in range(n_samples - 1):
        change = np.random.normal(0.0001, 0.0005)  # Small random changes
        price = price * (1 + change)
        prices.append(price)
    
    prices = np.array(prices)
    
    # Generate OHLC from close prices
    data = {
        'timestamp': timestamps,
        'open': prices * (1 + np.random.normal(0, 0.0002, n_samples)),
        'high': prices * (1 + abs(np.random.normal(0, 0.0003, n_samples))),
        'low': prices * (1 - abs(np.random.normal(0, 0.0003, n_samples))),
        'close': prices,
        'volume': np.random.randint(100, 1000, n_samples)
    }
    
    df = pd.DataFrame(data)
    print(f"✓ Generated {n_samples} candles")
    print(f"  Price range: {df['close'].min():.5f} - {df['close'].max():.5f}")
    
    return df


def demo_feature_engineering(bars):
    """Demonstrate feature engineering"""
    print("\n" + "=" * 80)
    print("  1. FEATURE ENGINEERING")
    print("=" * 80)
    
    engineer = FeatureEngineer()
    feature_set = engineer.transform(bars)
    
    print(f"\n✓ Generated {len(feature_set.feature_names)} features:")
    print(f"  Feature matrix shape: {feature_set.features.shape}")
    print(f"\n  Sample features:")
    for i, name in enumerate(feature_set.feature_names[:10]):
        print(f"    - {name}")
    if len(feature_set.feature_names) > 10:
        print(f"    ... and {len(feature_set.feature_names) - 10} more")
    
    # Create target variable
    target = engineer.create_target(bars, target_type='classification', threshold=0.0005)
    
    # Remove NaN values
    valid_idx = ~np.isnan(target)
    features_clean = feature_set.features[valid_idx]
    target_clean = target[valid_idx]
    
    print(f"\n  Target distribution:")
    unique, counts = np.unique(target_clean, return_counts=True)
    for val, count in zip(unique, counts):
        label = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}.get(val, 'UNKNOWN')
        print(f"    {label:4s} ({int(val):2d}): {count:4d} samples ({count/len(target_clean)*100:.1f}%)")
    
    return features_clean, target_clean, feature_set.feature_names


def demo_random_forest(X, y, feature_names):
    """Demonstrate Random Forest training and prediction"""
    if not RF_AVAILABLE:
        print("\n⚠️  Skipping Random Forest demo (scikit-learn not installed)")
        return None
    
    print("\n" + "=" * 80)
    print("  2. RANDOM FOREST CLASSIFIER")
    print("=" * 80)
    
    # Split data
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    print(f"\n📊 Data split:")
    print(f"  Training: {len(X_train)} samples")
    print(f"  Testing:  {len(X_test)} samples")
    
    # Create and train model
    print(f"\n🔄 Training Random Forest...")
    
    model = RandomForestClassifier({
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42
    })
    
    model.feature_names = feature_names
    metrics = model.train(X_train, y_train, validation_data=(X_test, y_test))
    
    print(f"\n✓ Training complete!")
    print(f"  Train accuracy: {metrics['train_accuracy']:.3f}")
    print(f"  Val accuracy:   {metrics['val_accuracy']:.3f}")
    print(f"  Val precision:  {metrics['val_precision']:.3f}")
    print(f"  Val recall:     {metrics['val_recall']:.3f}")
    print(f"  Val F1 score:   {metrics['val_f1_score']:.3f}")
    
    # Feature importance
    importance = model.get_feature_importance()
    print(f"\n📊 Top 10 important features:")
    for i, (feature, score) in enumerate(list(importance.items())[:10], 1):
        print(f"  {i:2d}. {feature:25s}: {score:.4f}")
    
    # Test prediction
    print(f"\n🔮 Making predictions on test data...")
    prediction = model.predict(X_test[:5])
    
    print(f"\n  Sample prediction:")
    print(f"    Signal: {['SELL', 'HOLD', 'BUY'][int(prediction.prediction) + 1]}")
    print(f"    Confidence: {prediction.confidence:.2%}")
    print(f"    Probabilities: {prediction.probabilities}")
    
    # Save model
    model_dir = Path("models/random_forest")
    if model.save(str(model_dir)):
        print(f"\n💾 Model saved to {model_dir}/")
    
    return model


def demo_lstm(X, y):
    """Demonstrate LSTM training and prediction"""
    if not LSTM_AVAILABLE:
        print("\n⚠️  Skipping LSTM demo (TensorFlow not installed)")
        return None
    
    print("\n" + "=" * 80)
    print("  3. LSTM PRICE PREDICTOR")
    print("=" * 80)
    
    # Split data
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Convert classification labels to regression (returns)
    # For demo, just use normalized targets
    y_train_reg = (y_train.astype(float) / 2)  # Scale to -0.5, 0, 0.5
    y_test_reg = (y_test.astype(float) / 2)
    
    print(f"\n📊 Data split:")
    print(f"  Training: {len(X_train)} samples")
    print(f"  Testing:  {len(X_test)} samples")
    
    # Create and train model
    print(f"\n🔄 Training LSTM (this may take a few minutes)...")
    
    model = LSTMPricePredictor({
        'sequence_length': 30,
        'lstm_units': [64, 32],
        'epochs': 10,  # Reduced for demo
        'batch_size': 32,
        'patience': 5
    })
    
    try:
        metrics = model.train(X_train, y_train_reg, validation_data=(X_test, y_test_reg))
        
        print(f"\n✓ Training complete!")
        print(f"  Final loss: {metrics['loss']:.4f}")
        print(f"  Epochs trained: {metrics['epochs_trained']}")
        
        # Test prediction
        print(f"\n🔮 Making predictions on test data...")
        prediction = model.predict(X_test)
        
        print(f"\n  Sample prediction:")
        print(f"    Predicted value: {prediction.prediction:.4f}")
        print(f"    Confidence: {prediction.confidence:.2%}")
        
        # Save model
        model_dir = Path("models/lstm")
        if model.save(str(model_dir)):
            print(f"\n💾 Model saved to {model_dir}/")
        
        return model
    
    except Exception as e:
        print(f"\n⚠️  LSTM training failed: {e}")
        print(f"  This is normal if TensorFlow is not properly configured")
        return None


def main():
    """Run complete ML demonstration"""
    
    # 1. Generate data
    bars = generate_sample_data(n_samples=1000)
    
    # 2. Feature engineering
    X, y, feature_names = demo_feature_engineering(bars)
    
    # 3. Random Forest
    rf_model = demo_random_forest(X, y, feature_names)
    
    # 4. LSTM
    lstm_model = demo_lstm(X, y)
    
    # Summary
    print("\n" + "=" * 80)
    print("  PHASE 3 SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ Machine Learning Infrastructure Complete!")
    print(f"\n  Components:")
    print(f"    ✓ Feature engineering pipeline ({len(feature_names)} features)")
    
    if rf_model:
        print(f"    ✓ Random Forest classifier (trained & saved)")
    else:
        print(f"    ⚠ Random Forest (skipped)")
    
    if lstm_model:
        print(f"    ✓ LSTM price predictor (trained & saved)")
    else:
        print(f"    ⚠ LSTM (skipped)")
    
    print(f"\n📚 Next Steps:")
    print(f"  1. Train models on real market data")
    print(f"  2. Integrate ML models into live trading (MLEnhancedStrategy)")
    print(f"  3. Backtest ML strategy performance")
    print(f"  4. Optimize hyperparameters")
    
    print(f"\n📖 Documentation:")
    print(f"  - See examples/ml_training.py for advanced training")
    print(f"  - See src/strategies/ml_strategy.py for ML trading")
    print(f"  - See docs/ML_GUIDE.md for complete guide")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
