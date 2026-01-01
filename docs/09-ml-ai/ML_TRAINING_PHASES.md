# 🚀 ML Training Phases - Complete Guide

## Overview
This guide provides a comprehensive, phased approach to train and integrate ML models into your MT5 trading bot.

---

## 📋 PHASE 1: Data Collection (Foundation)

### Objective
Collect high-quality historical data from MT5 for model training.

### Steps

#### 1.1 Create Data Collection Script
```python
# scripts/collect_data.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os

def collect_historical_data(symbol='EURUSD', timeframe=mt5.TIMEFRAME_H1, bars=10000):
    """
    Collect historical OHLCV data from MT5
    
    Args:
        symbol: Currency pair
        timeframe: MT5 timeframe constant
        bars: Number of bars to collect
    """
    if not mt5.initialize():
        print("MT5 initialization failed")
        return None
    
    # Get historical data
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    
    if rates is None:
        print(f"Failed to get data for {symbol}")
        mt5.shutdown()
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Save to CSV
    os.makedirs('data/raw', exist_ok=True)
    filename = f'data/raw/{symbol}_{timeframe}_historical.csv'
    df.to_csv(filename, index=False)
    
    print(f"✅ Saved {len(df)} bars to {filename}")
    mt5.shutdown()
    return df

if __name__ == '__main__':
    # Collect data for different symbols
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    for symbol in symbols:
        collect_historical_data(symbol, mt5.TIMEFRAME_H1, 10000)
        collect_historical_data(symbol, mt5.TIMEFRAME_M15, 20000)
```

#### 1.2 Run Collection
```bash
python scripts/collect_data.py
```

**Expected Output:**
```
data/raw/
├── EURUSD_1_historical.csv     (H1 data)
├── EURUSD_4_historical.csv     (M15 data)
├── GBPUSD_1_historical.csv
└── USDJPY_1_historical.csv
```

---

## 📊 PHASE 2: Feature Engineering (Prepare Data)

### Objective
Transform raw OHLCV data into ML-ready features with technical indicators.

### Steps

#### 2.1 Create Feature Engineering Pipeline
```python
# scripts/prepare_features.py
import pandas as pd
import numpy as np
from src.ml.feature_engineer import FeatureEngineer
import os

def prepare_training_data(symbol='EURUSD', timeframe='1'):
    """
    Prepare features from raw data
    """
    # Load raw data
    raw_file = f'data/raw/{symbol}_{timeframe}_historical.csv'
    df = pd.read_csv(raw_file)
    
    print(f"📂 Loaded {len(df)} bars from {raw_file}")
    
    # Initialize feature engineer
    engineer = FeatureEngineer()
    
    # Generate features
    feature_set = engineer.transform(df)
    
    print(f"✅ Generated {len(feature_set.features.columns)} features")
    print(f"   Features: {', '.join(feature_set.features.columns[:10])}...")
    
    # Create labels for classification
    # Label: 1 = price goes up, 0 = price goes down
    df['future_return'] = df['close'].shift(-5) - df['close']
    df['label'] = (df['future_return'] > 0).astype(int)
    
    # Merge features with labels
    data = pd.concat([
        feature_set.features,
        df[['label']].iloc[:len(feature_set.features)]
    ], axis=1).dropna()
    
    # Save processed data
    os.makedirs('data/processed', exist_ok=True)
    processed_file = f'data/processed/{symbol}_{timeframe}_features.csv'
    data.to_csv(processed_file, index=False)
    
    print(f"💾 Saved {len(data)} samples to {processed_file}")
    return data

if __name__ == '__main__':
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    for symbol in symbols:
        prepare_training_data(symbol, '1')  # H1 data
```

#### 2.2 Run Feature Engineering
```bash
python scripts/prepare_features.py
```

**Expected Output:**
```
data/processed/
├── EURUSD_1_features.csv       (Ready for training)
├── GBPUSD_1_features.csv
└── USDJPY_1_features.csv
```

---

## 🤖 PHASE 3: Model Training (Build AI)

### Objective
Train multiple ML models using prepared features.

### Steps

#### 3.1 Train Random Forest Model
```python
# scripts/train_random_forest.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

def train_rf_model(symbol='EURUSD', timeframe='1'):
    """
    Train Random Forest classification model
    """
    # Load prepared data
    data = pd.read_csv(f'data/processed/{symbol}_{timeframe}_features.csv')
    
    print(f"📊 Training data: {len(data)} samples")
    
    # Split features and labels
    X = data.drop('label', axis=1)
    y = data['label']
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"🔄 Training on {len(X_train)} samples, testing on {len(X_test)}")
    
    # Train Random Forest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42,
        n_jobs=-1
    )
    
    print("🤖 Training Random Forest...")
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✅ Training Complete!")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"\n{classification_report(y_test, y_pred)}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n📊 Top 10 Important Features:")
    print(feature_importance.head(10))
    
    # Save model
    os.makedirs('models', exist_ok=True)
    model_file = f'models/rf_{symbol}_{timeframe}.pkl'
    joblib.dump(model, model_file)
    
    print(f"\n💾 Model saved to {model_file}")
    return model, accuracy

if __name__ == '__main__':
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"Training {symbol}")
        print(f"{'='*60}")
        train_rf_model(symbol, '1')
```

#### 3.2 Train LSTM Model
```python
# scripts/train_lstm.py
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import joblib
import os

def train_lstm_model(symbol='EURUSD', timeframe='1', lookback=60):
    """
    Train LSTM price prediction model
    """
    # Load data
    data = pd.read_csv(f'data/processed/{symbol}_{timeframe}_features.csv')
    
    # Use only price data for LSTM
    raw_data = pd.read_csv(f'data/raw/{symbol}_{timeframe}_historical.csv')
    prices = raw_data['close'].values
    
    print(f"📊 Training LSTM on {len(prices)} price points")
    
    # Scale data
    scaler = MinMaxScaler()
    scaled_prices = scaler.fit_transform(prices.reshape(-1, 1))
    
    # Create sequences
    X, y = [], []
    for i in range(lookback, len(scaled_prices)):
        X.append(scaled_prices[i-lookback:i, 0])
        y.append(scaled_prices[i, 0])
    
    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"🔄 Training shape: {X_train.shape}")
    
    # Build LSTM model
    model = keras.Sequential([
        keras.layers.LSTM(50, return_sequences=True, input_shape=(lookback, 1)),
        keras.layers.Dropout(0.2),
        keras.layers.LSTM(50, return_sequences=False),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(25),
        keras.layers.Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    print("🤖 Training LSTM...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=50,
        batch_size=32,
        verbose=1
    )
    
    # Evaluate
    loss, mae = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n✅ Training Complete!")
    print(f"   Test Loss: {loss:.6f}")
    print(f"   Test MAE: {mae:.6f}")
    
    # Save model
    os.makedirs('models', exist_ok=True)
    model_file = f'models/lstm_{symbol}_{timeframe}.h5'
    scaler_file = f'models/lstm_{symbol}_{timeframe}_scaler.pkl'
    
    model.save(model_file)
    joblib.dump(scaler, scaler_file)
    
    print(f"\n💾 Model saved to {model_file}")
    print(f"💾 Scaler saved to {scaler_file}")
    
    return model, scaler

if __name__ == '__main__':
    symbols = ['EURUSD']
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"Training LSTM for {symbol}")
        print(f"{'='*60}")
        train_lstm_model(symbol, '1')
```

#### 3.3 Train Ensemble Model
```python
# scripts/train_ensemble.py
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import VotingClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import os

def train_ensemble_model(symbol='EURUSD', timeframe='1'):
    """
    Train ensemble combining multiple models
    """
    # Load data
    data = pd.read_csv(f'data/processed/{symbol}_{timeframe}_features.csv')
    
    X = data.drop('label', axis=1)
    y = data['label']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"📊 Training ensemble on {len(X_train)} samples")
    
    # Create individual models
    rf_model = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )
    
    gb_model = GradientBoostingClassifier(
        n_estimators=100, max_depth=5, random_state=42
    )
    
    lr_model = LogisticRegression(
        max_iter=1000, random_state=42
    )
    
    # Create ensemble
    ensemble = VotingClassifier(
        estimators=[
            ('rf', rf_model),
            ('gb', gb_model),
            ('lr', lr_model)
        ],
        voting='soft'  # Use probability averaging
    )
    
    print("🤖 Training Ensemble (RF + GradientBoost + LogReg)...")
    ensemble.fit(X_train, y_train)
    
    # Evaluate
    y_pred = ensemble.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Cross-validation
    cv_scores = cross_val_score(ensemble, X_train, y_train, cv=5)
    
    print(f"\n✅ Training Complete!")
    print(f"   Test Accuracy: {accuracy:.4f}")
    print(f"   CV Mean Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    print(f"\n{classification_report(y_test, y_pred)}")
    
    # Save
    model_file = f'models/ensemble_{symbol}_{timeframe}.pkl'
    joblib.dump(ensemble, model_file)
    
    print(f"\n💾 Ensemble saved to {model_file}")
    return ensemble, accuracy

if __name__ == '__main__':
    train_ensemble_model('EURUSD', '1')
```

#### 3.4 Run All Training
```bash
# Run in sequence
python scripts/train_random_forest.py
python scripts/train_lstm.py
python scripts/train_ensemble.py
```

**Expected Output:**
```
models/
├── rf_EURUSD_1.pkl              (Random Forest)
├── rf_GBPUSD_1.pkl
├── rf_USDJPY_1.pkl
├── lstm_EURUSD_1.h5             (LSTM model)
├── lstm_EURUSD_1_scaler.pkl     (LSTM scaler)
└── ensemble_EURUSD_1.pkl        (Ensemble)
```

---

## 🔗 PHASE 4: Integration with Bot

### Objective
Integrate trained models into your live trading bot.

### Steps

#### 4.1 Update Model Loader
```python
# src/ml/model_loader.py
import joblib
import os
from tensorflow import keras

class ModelLoader:
    """Load and manage ML models"""
    
    @staticmethod
    def load_rf_model(symbol='EURUSD', timeframe='1'):
        """Load Random Forest model"""
        path = f'models/rf_{symbol}_{timeframe}.pkl'
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}")
        return joblib.load(path)
    
    @staticmethod
    def load_lstm_model(symbol='EURUSD', timeframe='1'):
        """Load LSTM model and scaler"""
        model_path = f'models/lstm_{symbol}_{timeframe}.h5'
        scaler_path = f'models/lstm_{symbol}_{timeframe}_scaler.pkl'
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"LSTM model not found: {model_path}")
        
        model = keras.models.load_model(model_path)
        scaler = joblib.load(scaler_path)
        
        return model, scaler
    
    @staticmethod
    def load_ensemble_model(symbol='EURUSD', timeframe='1'):
        """Load ensemble model"""
        path = f'models/ensemble_{symbol}_{timeframe}.pkl'
        if not os.path.exists(path):
            raise FileNotFoundError(f"Ensemble not found: {path}")
        return joblib.load(path)
```

#### 4.2 Update Main Bot Configuration
```python
# In main.py

from src.ml.model_loader import ModelLoader

# Load your preferred model
try:
    # Option 1: Random Forest (fastest)
    ml_model = ModelLoader.load_rf_model('EURUSD', '1')
    
    # Option 2: Ensemble (most accurate)
    # ml_model = ModelLoader.load_ensemble_model('EURUSD', '1')
    
    # Option 3: LSTM (price prediction)
    # lstm_model, lstm_scaler = ModelLoader.load_lstm_model('EURUSD', '1')
    
    orchestrator.enable_ml_for_all(ml_model)
    print("✅ ML Model loaded successfully")
except Exception as e:
    print(f"⚠️  ML model not available: {e}")
```

#### 4.3 Update currencies.yaml
```yaml
ml_settings:
  enabled: true
  model_type: 'ensemble'  # 'rf', 'lstm', or 'ensemble'
  symbol: 'EURUSD'
  timeframe: '1'
  confidence_threshold: 0.65  # Only trade when ML confidence > 65%
  
currencies:
  - symbol: EURUSD
    enabled: true
    use_ml: true  # Enable ML for this pair
    ml_model: 'ensemble'  # Which model to use
```

---

## 🎯 PHASE 5: Backtesting & Validation

### Objective
Test models before live trading.

```python
# scripts/backtest_models.py
import pandas as pd
import joblib
from src.ml.feature_engineer import FeatureEngineer

def backtest_model(model_path, test_data_path):
    """
    Backtest a trained model
    """
    # Load model and data
    model = joblib.load(model_path)
    data = pd.read_csv(test_data_path)
    
    X = data.drop('label', axis=1)
    y = data['label']
    
    # Predict
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    
    # Calculate trading performance
    data['prediction'] = predictions
    data['confidence'] = probabilities.max(axis=1)
    
    # Simulate trades
    data['signal'] = data['prediction'].apply(lambda x: 'BUY' if x == 1 else 'SELL')
    data['correct'] = (data['prediction'] == data['label']).astype(int)
    
    accuracy = data['correct'].mean()
    high_conf_accuracy = data[data['confidence'] > 0.7]['correct'].mean()
    
    print(f"📊 Backtest Results:")
    print(f"   Overall Accuracy: {accuracy:.4f}")
    print(f"   High Confidence (>70%) Accuracy: {high_conf_accuracy:.4f}")
    print(f"   High Confidence Trades: {len(data[data['confidence'] > 0.7])}")
    
    return data

if __name__ == '__main__':
    backtest_model(
        'models/ensemble_EURUSD_1.pkl',
        'data/processed/EURUSD_1_features.csv'
    )
```

---

## 📈 PHASE 6: Monitoring & Retraining

### Objective
Keep models updated and performing well.

```python
# scripts/monitor_performance.py
import pandas as pd
from datetime import datetime

def log_prediction(symbol, prediction, actual, confidence):
    """Log model predictions for monitoring"""
    log_file = f'data/logs/ml_predictions_{symbol}.csv'
    
    log_entry = pd.DataFrame([{
        'timestamp': datetime.now(),
        'symbol': symbol,
        'prediction': prediction,
        'actual': actual,
        'confidence': confidence,
        'correct': int(prediction == actual)
    }])
    
    # Append to log
    if os.path.exists(log_file):
        logs = pd.read_csv(log_file)
        logs = pd.concat([logs, log_entry])
    else:
        logs = log_entry
    
    logs.to_csv(log_file, index=False)
    
    # Check if retraining needed
    recent = logs.tail(1000)
    accuracy = recent['correct'].mean()
    
    if accuracy < 0.55:  # Below threshold
        print(f"⚠️  Model accuracy dropped to {accuracy:.2%} - Consider retraining!")
```

---

## 🎓 Summary: How to Use ML in Your Bot

### Quick Start (After Training)

1. **Train models:**
   ```bash
   python scripts/collect_data.py
   python scripts/prepare_features.py
   python scripts/train_ensemble.py
   ```

2. **Configure bot:**
   ```yaml
   # config/currencies.yaml
   ml_settings:
     enabled: true
     model_type: 'ensemble'
   ```

3. **Run bot:**
   ```bash
   python main.py
   ```

### Model Selection Guide

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| **Random Forest** | ⚡⚡⚡ Fast | 65-70% | High-frequency, quick decisions |
| **LSTM** | ⚡ Slow | 70-75% | Price prediction, trend following |
| **Ensemble** | ⚡⚡ Medium | 75-80% | **Best overall, most reliable** |

### Best Practice Workflow

```
Week 1: Collect Data
Week 2: Train RF + LSTM
Week 3: Train Ensemble
Week 4: Backtest all models
Week 5: Paper trade with best model
Week 6+: Live trade + monitor + retrain monthly
```

---

## 📞 Next Steps

Ready to start? Run:
```bash
# Create all training scripts
mkdir -p scripts
# Copy the training code from Phase 3
# Run data collection first
python scripts/collect_data.py
```

Would you like me to create these training scripts for you now? 🚀
