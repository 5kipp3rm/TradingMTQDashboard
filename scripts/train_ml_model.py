"""
Quick ML Model Training Script
Trains a Random Forest classifier for trading signals
"""
import sys
sys.path.insert(0, '.')

from src.ml import RF_AVAILABLE, FeatureEngineer, RandomForestClassifier
import numpy as np
import pandas as pd
from pathlib import Path

print('='*80)
print('QUICK ML MODEL TRAINING')
print('='*80)

if not RF_AVAILABLE:
    print('\nERROR: scikit-learn not installed')
    print('Install with: pip install scikit-learn')
    sys.exit(1)

print('\nGenerating sample training data...')
np.random.seed(42)

# Generate 1000 samples of OHLC data
n_samples = 1000
timestamps = pd.date_range('2023-01-01', periods=n_samples, freq='1H')

price = 1.0500
prices = [price]
for i in range(n_samples - 1):
    change = np.random.normal(0.0001, 0.0005)
    price = price * (1 + change)
    prices.append(price)

prices = np.array(prices)

df = pd.DataFrame({
    'timestamp': timestamps,
    'open': prices * (1 + np.random.normal(0, 0.0002, n_samples)),
    'high': prices * (1 + abs(np.random.normal(0, 0.0003, n_samples))),
    'low': prices * (1 - abs(np.random.normal(0, 0.0003, n_samples))),
    'close': prices,
    'volume': np.random.randint(100, 1000, n_samples)
})

print(f'Generated {len(df)} candles')
print(f'Price range: {df["close"].min():.5f} - {df["close"].max():.5f}')

print('\nEngineering features...')
engineer = FeatureEngineer()
feature_set = engineer.transform(df)

print(f'Generated {len(feature_set.feature_names)} features')

# Create target
target = engineer.create_target(df, target_type='classification', threshold=0.0005)

# Both features and target might have different lengths due to indicator calculation
# Use the shorter length
min_length = min(len(feature_set.features), len(target))
features_trimmed = feature_set.features[:min_length]
target_trimmed = target[:min_length]

# Clean data - remove NaN values
valid_idx = ~np.isnan(target_trimmed)
# Also check for NaN in features
if hasattr(features_trimmed, 'values'):
    feature_valid_idx = ~np.isnan(features_trimmed.values).any(axis=1)
else:
    feature_valid_idx = ~np.isnan(features_trimmed).any(axis=1)

valid_idx = valid_idx & feature_valid_idx

X = features_trimmed[valid_idx]
y = target_trimmed[valid_idx]

print(f'Clean dataset: {len(X)} samples')

# Split data
split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f'\nTraining Random Forest model...')
print(f'  Training set: {len(X_train)} samples')
print(f'  Test set: {len(X_test)} samples')

model = RandomForestClassifier({
    'n_estimators': 100,
    'max_depth': 10,
    'random_state': 42
})

model.feature_names = feature_set.feature_names
metrics = model.train(X_train, y_train, validation_data=(X_test, y_test))

print(f'\nTraining complete!')
print(f'  Train accuracy: {metrics["train_accuracy"]:.3f}')
print(f'  Val accuracy:   {metrics["val_accuracy"]:.3f}')
print(f'  Val precision:  {metrics["val_precision"]:.3f}')
print(f'  Val recall:     {metrics["val_recall"]:.3f}')

# Save model
model_dir = Path('models')
model_dir.mkdir(parents=True, exist_ok=True)

# The save method expects a directory and will create rf_model.pkl inside
if model.save(str(model_dir)):
    print(f'\nModel saved to {model_dir}/rf_model.pkl')
    print('='*80)
    print('SUCCESS! ML model ready for production!')
    print('='*80)
else:
    print(f'\nERROR: Failed to save model')
    sys.exit(1)
