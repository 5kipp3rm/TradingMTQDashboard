"""
Backtest Demo
Test strategies on sample historical data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import numpy as np

from src.connectors.base import OHLCBar
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.bb_strategy import BollingerBandsStrategy
from src.strategies.multi_indicator import MultiIndicatorStrategy
from src.backtest.engine import BacktestEngine
from src.backtest.reporter import BacktestReporter


def generate_sample_data(bars: int = 1000, trend: str = 'ranging') -> list[OHLCBar]:
    """
    Generate synthetic OHLC data for testing
    
    Args:
        bars: Number of bars to generate
        trend: 'ranging', 'uptrend', 'downtrend', or 'volatile'
    
    Returns:
        List of OHLCBar objects
    """
    print(f"Generating {bars} bars of {trend} data...")
    
    data = []
    base_price = 1.1000
    current_time = datetime.now() - timedelta(hours=bars)
    
    for i in range(bars):
        # Base movement
        if trend == 'uptrend':
            drift = 0.0001
            noise = np.random.normal(0, 0.0005)
        elif trend == 'downtrend':
            drift = -0.0001
            noise = np.random.normal(0, 0.0005)
        elif trend == 'volatile':
            drift = 0
            noise = np.random.normal(0, 0.0015)
        else:  # ranging
            drift = 0
            noise = np.random.normal(0, 0.0003)
        
        # Add some cyclical component (simulates market cycles)
        cycle = 0.0002 * np.sin(i / 50)
        
        base_price += drift + noise + cycle
        
        # Generate OHLC
        volatility = 0.0003
        open_price = base_price
        high_price = base_price + abs(np.random.normal(0, volatility))
        low_price = base_price - abs(np.random.normal(0, volatility))
        close_price = base_price + np.random.normal(0, volatility/2)
        
        # Ensure OHLC logic
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        volume = int(np.random.uniform(1000, 5000))
        
        bar = OHLCBar(
            symbol='EURUSD',
            timeframe='H1',
            time=current_time + timedelta(hours=i),
            open=round(open_price, 5),
            high=round(high_price, 5),
            low=round(low_price, 5),
            close=round(close_price, 5),
            volume=volume
        )
        
        data.append(bar)
        base_price = close_price
    
    return data


def backtest_all_strategies(data: list[OHLCBar]):
    """
    Backtest all available strategies
    
    Args:
        data: Historical OHLC bars
    """
    print("\n" + "="*70)
    print("BACKTESTING ALL STRATEGIES")
    print("="*70)
    
    # Initialize strategies
    strategies = [
        RSIStrategy(),
        MACDStrategy(),
        BollingerBandsStrategy(),
        MultiIndicatorStrategy(),
    ]
    
    # Run backtests
    results = {}
    
    for strategy in strategies:
        print(f"\n▶ Testing: {strategy.name}")
        
        engine = BacktestEngine(
            initial_balance=10000.0,
            commission_pips=2.0,
            slippage_pips=1.0
        )
        
        metrics = engine.run(
            strategy=strategy,
            bars=data,
            volume=0.1,  # 0.1 lots
            max_positions=1
        )
        
        results[strategy.name] = metrics
        
        # Print summary
        BacktestReporter.print_summary(metrics, strategy.name)
        
        # Print some trades
        if engine.positions:
            BacktestReporter.print_trades(engine.positions, limit=5)
    
    # Compare strategies
    if len(results) > 1:
        BacktestReporter.compare_strategies(results)
    
    return results


def main():
    """Run backtest demo"""
    print("\n🚀 Backtest Engine Demo\n")
    
    # Test different market conditions
    market_conditions = ['ranging', 'uptrend', 'downtrend', 'volatile']
    
    for condition in market_conditions:
        print(f"\n{'='*70}")
        print(f"TESTING IN {condition.upper()} MARKET")
        print(f"{'='*70}")
        
        # Generate data
        data = generate_sample_data(bars=500, trend=condition)
        
        # Backtest all strategies
        results = backtest_all_strategies(data)
        
        # Find best strategy for this condition
        if results:
            best = max(results.items(), 
                      key=lambda x: BacktestReporter._calculate_rating(x[1])['score'])
            print(f"\n✅ BEST FOR {condition.upper()}: {best[0]}")
            print(f"   Win Rate: {best[1].win_rate:.1f}% | "
                  f"Profit: ${best[1].total_profit:.2f} | "
                  f"Sharpe: {best[1].sharpe_ratio:.2f}")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Test with real historical data")
    print("2. Optimize strategy parameters")
    print("3. Implement walk-forward analysis")
    print("4. Add Monte Carlo simulation")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
