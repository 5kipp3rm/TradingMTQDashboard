"""
Quick Start Guide for ML Training
================================

Follow these steps to train ML models for your trading bot:

## Prerequisites
- MT5 installed and running
- Bot configured with valid MT5 credentials
- Python environment activated

## Option 1: Automated Training (Recommended)
Run all phases automatically:

```bash
python scripts/train_all.py
```

This will:
1. Collect 10,000+ bars of historical data
2. Engineer 50+ technical indicator features  
3. Train Random Forest and Ensemble models
4. Save models to models/

Time: ~15-30 minutes

## Option 2: Manual Step-by-Step

### Step 1: Collect Data
```bash
python scripts/collect_data.py
```
Output: data/raw/*.csv files

### Step 2: Prepare Features
```bash
python scripts/prepare_features.py
```
Output: data/processed/*_features.csv files

### Step 3: Train Models
```bash
python scripts/train_models.py
```
Output: models/*.pkl files

## Using Models in Your Bot

The bot automatically loads ensemble models from models/.

To run with trained models:
```bash
python main.py
```

## Model Selection

Edit main.py line ~100 to choose model type:

```python
# Option 1: Ensemble (best accuracy, recommended)
ml_model = joblib.load('models/ensemble_EURUSD_H1.pkl')

# Option 2: Random Forest (fastest)
ml_model = joblib.load('models/rf_EURUSD_H1.pkl')
```

## Troubleshooting

**Error: "No raw data files found"**
- Run: python scripts/collect_data.py

**Error: "MT5 initialization failed"**
- Ensure MT5 is running
- Check config/mt5_config.yaml credentials

**Error: "Model file not found"**
- Complete all training steps first
- Check models/ directory exists

## Model Performance

Expected accuracy ranges:
- Random Forest: 60-70%
- Ensemble: 70-80%

Models with >70% accuracy are excellent for forex trading.

## Retraining Models

Retrain monthly or when:
- Market conditions change significantly
- Model accuracy drops below 60%
- You want to include recent market data

Simply run: python scripts/train_all.py

## Next Steps

1. Train models: python scripts/train_all.py
2. Backtest (optional): python scripts/backtest.py
3. Paper trade: Test with small lot sizes first
4. Live trade: Increase lot sizes gradually

For detailed information, see: ML_TRAINING_PHASES.md
