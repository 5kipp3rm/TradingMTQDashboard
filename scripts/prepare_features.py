"""
PHASE 2: Feature Engineering
Prepare ML-ready features from raw OHLCV data
"""
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.feature_engineer import FeatureEngineer

def prepare_training_data(symbol='EURUSD', timeframe='H1', future_bars=5):
    """
    Prepare features and labels from raw data
    
    Args:
        symbol: Currency pair
        timeframe: Timeframe identifier (H1, M15, etc.)
        future_bars: Number of bars ahead to predict
        
    Returns:
        DataFrame with features and labels
    """
    print(f"\n{'='*60}")
    print(f"Preparing features for {symbol} {timeframe}")
    print(f"{'='*60}")
    
    # Load raw data
    raw_file = f'data/raw/{symbol}_{timeframe}_historical.csv'
    
    if not os.path.exists(raw_file):
        print(f"❌ Raw data file not found: {raw_file}")
        print(f"   Run 'python scripts/collect_data.py' first")
        return None
    
    df = pd.read_csv(raw_file)
    print(f"📂 Loaded {len(df):,} bars from {raw_file}")
    
    # Initialize feature engineer
    engineer = FeatureEngineer()
    
    # Generate technical indicator features
    print(f"🔧 Generating technical indicators...")
    feature_set = engineer.transform(df)
    
    if feature_set.features is None or len(feature_set.features) == 0:
        print(f"❌ Feature generation failed")
        return None
    
    print(f"✅ Generated {len(feature_set.features.columns)} features:")
    feature_groups = {}
    for col in feature_set.features.columns:
        prefix = col.split('_')[0]
        feature_groups[prefix] = feature_groups.get(prefix, 0) + 1
    
    for group, count in sorted(feature_groups.items()):
        print(f"   {group}: {count} features")
    
    # Create labels for classification
    print(f"\n🎯 Creating labels (future={future_bars} bars)...")
    
    # Calculate future returns
    df['future_close'] = df['close'].shift(-future_bars)
    df['future_return'] = (df['future_close'] - df['close']) / df['close']
    
    # Multi-class classification
    # 0 = Strong DOWN (< -0.1%)
    # 1 = Neutral (-0.1% to +0.1%)
    # 2 = Strong UP (> +0.1%)
    conditions = [
        df['future_return'] < -0.001,
        (df['future_return'] >= -0.001) & (df['future_return'] <= 0.001),
        df['future_return'] > 0.001
    ]
    df['label'] = np.select(conditions, [0, 1, 2], default=1)
    
    # Also create binary label (simple UP/DOWN)
    df['label_binary'] = (df['future_return'] > 0).astype(int)
    
    # Merge features with labels
    data = pd.concat([
        feature_set.features,
        df[['label', 'label_binary', 'future_return']].iloc[:len(feature_set.features)]
    ], axis=1).dropna()
    
    print(f"✅ Created {len(data):,} labeled samples")
    print(f"\n📊 Label distribution:")
    print(f"   DOWN (0): {(data['label'] == 0).sum():,} ({(data['label'] == 0).mean()*100:.1f}%)")
    print(f"   NEUTRAL (1): {(data['label'] == 1).sum():,} ({(data['label'] == 1).mean()*100:.1f}%)")
    print(f"   UP (2): {(data['label'] == 2).sum():,} ({(data['label'] == 2).mean()*100:.1f}%)")
    
    # Save processed data
    os.makedirs('data/processed', exist_ok=True)
    processed_file = f'data/processed/{symbol}_{timeframe}_features.csv'
    data.to_csv(processed_file, index=False)
    
    print(f"\n💾 Saved to {processed_file}")
    print(f"   File size: {os.path.getsize(processed_file) / 1024:.2f} KB")
    
    return data

def prepare_all_features():
    """Prepare features for all collected data"""
    
    print("\n" + "="*60)
    print("  PHASE 2: FEATURE ENGINEERING")
    print("="*60)
    
    # Find all raw data files
    raw_files = [f for f in os.listdir('data/raw') if f.endswith('_historical.csv')]
    
    if not raw_files:
        print("❌ No raw data files found in data/raw/")
        print("   Run 'python scripts/collect_data.py' first")
        return
    
    print(f"Found {len(raw_files)} raw data files")
    print("="*60)
    
    success_count = 0
    
    for raw_file in raw_files:
        # Extract symbol and timeframe from filename
        # Format: SYMBOL_TIMEFRAME_historical.csv
        parts = raw_file.replace('_historical.csv', '').split('_')
        if len(parts) >= 2:
            symbol = parts[0]
            timeframe = parts[1]
            
            data = prepare_training_data(symbol, timeframe)
            if data is not None:
                success_count += 1
    
    print(f"\n{'='*60}")
    print(f"  FEATURE PREPARATION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successfully processed: {success_count}/{len(raw_files)} files")
    print(f"📂 Features saved to: data/processed/")
    print(f"\n🚀 Next step: Run 'python scripts/train_models.py'")

if __name__ == '__main__':
    prepare_all_features()
