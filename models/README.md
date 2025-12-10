# ML Models Directory

This directory contains trained machine learning models for the trading system.

## Model Types

### Ensemble Models (`ensemble_*.pkl`)
- Voting classifier combining RandomForest, GradientBoosting, and LogisticRegression
- Recommended for production use
- Better accuracy and robustness

### Random Forest Models (`rf_*.pkl`)
- Single RandomForest classifier
- Faster inference
- Fallback option when ensemble not available

## Naming Convention

Models are named: `{model_type}_{SYMBOL}_{TIMEFRAME}.pkl`

Examples:
- `ensemble_EURUSD_H1.pkl` - Ensemble model for EUR/USD on H1 timeframe
- `rf_GBPUSD_M15.pkl` - Random Forest model for GBP/USD on M15 timeframe

## Model Training

To retrain models, use:
```bash
python train_ml_model.py
```

See `ML_TRAINING_PHASES.md` for detailed training documentation.
