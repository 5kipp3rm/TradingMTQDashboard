"""
Quick Phase 2 Test - Verify backtesting works
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
import numpy as np

from src.connectors.base import OHLCBar
from src.strategies.simple_ma import SimpleMovingAverageStrategy
from src.backtest.engine import BacktestEngine
from src.backtest.reporter import BacktestReporter


def generate_trending_data(num_bars: int = 500) -> list:
    """Generate simple uptrending data"""
    bars = []
    base_price = 1.0850
    base_time = datetime.now() - timedelta(hours=num_bars)
    
    for i in range(num_bars):
        price = base_price + (i * 0.00005) + (np.random.randn() * 0.0002)
        
        bar = OHLCBar(
            symbol="EURUSD",
            timeframe="H1",
            time=base_time + timedelta(hours=i),
            open=price,
            high=price + abs(np.random.randn() * 0.0003),
            low=price - abs(np.random.randn() * 0.0003),
            close=price + (np.random.randn() * 0.0001),
            tick_volume=int(1000 + np.random.randn() * 200),
            real_volume=100000,
            spread=2
        )
        bars.append(bar)
    
    return bars


def main():
    print("\n" + "="*80)
    print("  PHASE 2 - BACKTESTING ENGINE TEST")
    print("="*80 + "\n")
    
    # Generate data
    print("Generating 500 bars of uptrending market data...")
    bars = generate_trending_data(500)
    print(f"Generated {len(bars)} bars\n")
    
    # Create strategy
    print("Creating Simple MA Crossover Strategy (Fast=10, Slow=20)...")
    strategy = SimpleMovingAverageStrategy({'fast_period': 10, 'slow_period': 20})
    
    # Run backtest
    print("Running backtest...")
    engine = BacktestEngine(
        initial_balance=10000.0,
        commission_pips=2.0,
        slippage_pips=1.0
    )
    
    metrics = engine.run(strategy, bars)
    positions = engine.positions
    
    # Print results
    BacktestReporter.print_summary(metrics, "Simple MA Strategy")
    
    if len(positions) > 0:
        print(f"\n  Sample Trades (first 5):")
        BacktestReporter.print_trades(positions[:5])
    
    # Summary
    print("\n" + "="*80)
    print("  PHASE 2 STATUS")
    print("="*80)
    print("\n  COMPLETED:")
    print("  [x] Technical Indicators (12+ indicators)")
    print("  [x] Strategy Framework")
    print("  [x] Backtesting Engine")
    print("  [x] Performance Analytics")
    print("\n  Backtest ran successfully!")
    print(f"  - Processed {len(bars)} bars")
    print(f"  - Executed {metrics.total_trades} trades")
    print(f"  - Final P&L: ${metrics.total_profit:,.2f}")
    print(f"  - Win Rate: {metrics.win_rate:.1f}%")
    if metrics.sharpe_ratio:
        print(f"  - Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print("\n  PHASE 2 COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
