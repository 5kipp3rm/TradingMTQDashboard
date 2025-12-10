"""
PHASE 3: Model Training
Train ML models using prepared features
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def train_random_forest(symbol='EURUSD', timeframe='H1'):
    """Train Random Forest classifier"""
    
    print(f"\n{'='*60}")
    print(f"Training Random Forest: {symbol} {timeframe}")
    print(f"{'='*60}")
    
    # Load prepared data
    data_file = f'data/processed/{symbol}_{timeframe}_features.csv'
    
    if not os.path.exists(data_file):
        print(f"❌ Processed data not found: {data_file}")
        print(f"   Run 'python scripts/prepare_features.py' first")
        return None
    
    data = pd.read_csv(data_file)
    print(f"📊 Loaded {len(data):,} samples")
    
    # Split features and labels
    X = data.drop(['label', 'label_binary', 'future_return'], axis=1, errors='ignore')
    y = data['label_binary']  # Use binary classification
    
    print(f"   Features: {X.shape[1]}")
    print(f"   Samples: {len(X):,}")
    
    # Train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 Split:")
    print(f"   Train: {len(X_train):,} samples")
    print(f"   Test: {len(X_test):,} samples")
    
    # Train Random Forest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=20,
        min_samples_leaf=10,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    
    print(f"\n🤖 Training Random Forest...")
    model.fit(X_train, y_train)
    
    # Evaluate
    print(f"\n📈 Evaluation:")
    
    # Training accuracy
    train_pred = model.predict(X_train)
    train_acc = accuracy_score(y_train, train_pred)
    print(f"   Train Accuracy: {train_acc:.4f}")
    
    # Test accuracy
    test_pred = model.predict(X_test)
    test_acc = accuracy_score(y_test, test_pred)
    print(f"   Test Accuracy: {test_acc:.4f}")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, n_jobs=-1)
    print(f"   CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    # Detailed metrics
    print(f"\n{classification_report(y_test, test_pred, target_names=['DOWN', 'UP'])}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n📊 Top 10 Important Features:")
    for idx, row in feature_importance.head(10).iterrows():
        print(f"   {row['feature']}: {row['importance']:.4f}")
    
    # Save model
    os.makedirs('models', exist_ok=True)
    model_file = f'models/rf_{symbol}_{timeframe}.pkl'
    joblib.dump(model, model_file)
    
    file_size = os.path.getsize(model_file) / (1024 * 1024)
    print(f"\n💾 Model saved to {model_file}")
    print(f"   File size: {file_size:.2f} MB")
    
    return model, test_acc

def train_ensemble(symbol='EURUSD', timeframe='H1'):
    """Train ensemble combining multiple models"""
    
    print(f"\n{'='*60}")
    print(f"Training Ensemble: {symbol} {timeframe}")
    print(f"{'='*60}")
    
    # Load data
    data_file = f'data/processed/{symbol}_{timeframe}_features.csv'
    data = pd.read_csv(data_file)
    
    X = data.drop(['label', 'label_binary', 'future_return'], axis=1, errors='ignore')
    y = data['label_binary']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"📊 Training on {len(X_train):,} samples")
    
    # Create individual models
    print(f"\n🤖 Creating ensemble components...")
    
    rf_model = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )
    
    gb_model = GradientBoostingClassifier(
        n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
    )
    
    lr_model = LogisticRegression(
        max_iter=1000, random_state=42, solver='lbfgs'
    )
    
    # Create ensemble
    ensemble = VotingClassifier(
        estimators=[
            ('rf', rf_model),
            ('gb', gb_model),
            ('lr', lr_model)
        ],
        voting='soft',  # Use probability averaging
        n_jobs=-1
    )
    
    print(f"   - Random Forest (100 trees)")
    print(f"   - Gradient Boosting (100 estimators)")
    print(f"   - Logistic Regression")
    
    print(f"\n🚀 Training ensemble (this may take a few minutes)...")
    ensemble.fit(X_train, y_train)
    
    # Evaluate
    print(f"\n📈 Evaluation:")
    
    test_pred = ensemble.predict(X_test)
    test_acc = accuracy_score(y_test, test_pred)
    
    # Get probabilities for confidence analysis
    test_proba = ensemble.predict_proba(X_test)
    confidence = np.max(test_proba, axis=1)
    
    # Accuracy at different confidence levels
    for conf_thresh in [0.6, 0.7, 0.8]:
        high_conf_mask = confidence >= conf_thresh
        if high_conf_mask.sum() > 0:
            high_conf_acc = accuracy_score(
                y_test[high_conf_mask],
                test_pred[high_conf_mask]
            )
            print(f"   Accuracy (conf>{conf_thresh}): {high_conf_acc:.4f} ({high_conf_mask.sum()} samples)")
    
    # Cross-validation
    cv_scores = cross_val_score(ensemble, X_train, y_train, cv=5, n_jobs=-1)
    print(f"   CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    print(f"\n{classification_report(y_test, test_pred, target_names=['DOWN', 'UP'])}")
    
    # Save
    model_file = f'models/ensemble_{symbol}_{timeframe}.pkl'
    joblib.dump(ensemble, model_file)
    
    file_size = os.path.getsize(model_file) / (1024 * 1024)
    print(f"\n💾 Ensemble saved to {model_file}")
    print(f"   File size: {file_size:.2f} MB")
    
    return ensemble, test_acc

def train_all_models():
    """Train models for all processed data"""
    
    print("\n" + "="*60)
    print("  PHASE 3: MODEL TRAINING")
    print("="*60)
    
    # Find all processed data files
    processed_files = [f for f in os.listdir('data/processed') if f.endswith('_features.csv')]
    
    if not processed_files:
        print("❌ No processed data files found in data/processed/")
        print("   Run 'python scripts/prepare_features.py' first")
        return
    
    print(f"Found {len(processed_files)} processed datasets")
    print("="*60)
    
    results = []
    
    for proc_file in processed_files:
        # Extract symbol and timeframe
        parts = proc_file.replace('_features.csv', '').split('_')
        if len(parts) >= 2:
            symbol = parts[0]
            timeframe = parts[1]
            
            # Train Random Forest
            rf_model, rf_acc = train_random_forest(symbol, timeframe)
            
            # Train Ensemble
            ens_model, ens_acc = train_ensemble(symbol, timeframe)
            
            results.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'rf_accuracy': rf_acc,
                'ensemble_accuracy': ens_acc
            })
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  TRAINING COMPLETE")
    print(f"{'='*60}")
    
    print(f"\n📊 Model Performance Summary:")
    print(f"{'Symbol':<10} {'TF':<5} {'RF Acc':<10} {'Ensemble Acc':<15}")
    print("-" * 60)
    
    for r in results:
        print(f"{r['symbol']:<10} {r['timeframe']:<5} {r['rf_accuracy']:.4f}     {r['ensemble_accuracy']:.4f}")
    
    print(f"\n💾 Models saved to: models/")
    print(f"\n🚀 Next step: Update main.py to load your preferred model")
    print(f"\nRecommended: Use ensemble models for best accuracy!")

if __name__ == '__main__':
    train_all_models()
