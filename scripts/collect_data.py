"""
PHASE 1: Data Collection
Collect historical OHLCV data from MT5 for ML training
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def collect_historical_data(symbol='EURUSD', timeframe=mt5.TIMEFRAME_H1, bars=10000):
    """
    Collect historical OHLCV data from MT5
    
    Args:
        symbol: Currency pair (e.g., 'EURUSD', 'GBPUSD')
        timeframe: MT5 timeframe constant
        bars: Number of historical bars to collect
        
    Returns:
        DataFrame with OHLCV data
    """
    print(f"\n{'='*60}")
    print(f"Collecting data for {symbol}")
    print(f"Timeframe: {timeframe}, Bars: {bars}")
    print(f"{'='*60}")
    
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return None
    
    # Get historical data
    print(f"📡 Fetching data from MT5...")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    
    if rates is None or len(rates) == 0:
        print(f"❌ Failed to get data for {symbol}")
        print(f"   Error: {mt5.last_error()}")
        mt5.shutdown()
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Add derived features
    df['returns'] = df['close'].pct_change()
    df['high_low_range'] = df['high'] - df['low']
    df['body_size'] = abs(df['close'] - df['open'])
    
    # Save to CSV
    os.makedirs('data/raw', exist_ok=True)
    timeframe_name = {
        mt5.TIMEFRAME_M1: 'M1',
        mt5.TIMEFRAME_M5: 'M5',
        mt5.TIMEFRAME_M15: 'M15',
        mt5.TIMEFRAME_M30: 'M30',
        mt5.TIMEFRAME_H1: 'H1',
        mt5.TIMEFRAME_H4: 'H4',
        mt5.TIMEFRAME_D1: 'D1'
    }.get(timeframe, str(timeframe))
    
    filename = f'data/raw/{symbol}_{timeframe_name}_historical.csv'
    df.to_csv(filename, index=False)
    
    print(f"✅ Saved {len(df):,} bars to {filename}")
    print(f"   Date range: {df['time'].min()} to {df['time'].max()}")
    print(f"   File size: {os.path.getsize(filename) / 1024:.2f} KB")
    
    mt5.shutdown()
    return df

def collect_all_data():
    """Collect data for multiple symbols and timeframes"""
    
    # Configuration
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
    timeframes = [
        (mt5.TIMEFRAME_H1, 10000, 'H1'),
        (mt5.TIMEFRAME_M15, 20000, 'M15')
    ]
    
    print("\n" + "="*60)
    print("  PHASE 1: ML DATA COLLECTION")
    print("="*60)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Timeframes: {', '.join([tf[2] for tf in timeframes])}")
    print("="*60)
    
    total_files = 0
    total_bars = 0
    
    for symbol in symbols:
        for timeframe, bars, tf_name in timeframes:
            df = collect_historical_data(symbol, timeframe, bars)
            if df is not None:
                total_files += 1
                total_bars += len(df)
    
    print(f"\n{'='*60}")
    print(f"  COLLECTION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Total files created: {total_files}")
    print(f"✅ Total bars collected: {total_bars:,}")
    print(f"📂 Data saved to: data/raw/")
    print(f"\n🚀 Next step: Run 'python scripts/prepare_features.py'")

if __name__ == '__main__':
    collect_all_data()
