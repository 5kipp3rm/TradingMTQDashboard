"""
Phase 2 Demo - Complete Backtesting System
Demonstrates all Phase 2 features:
- Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Multiple trading strategies
- Backtesting engine
- Performance analytics
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
import numpy as np

from src.connectors.base import OHLCBar, OrderType
from src.strategies.simple_ma import SimpleMovingAverageStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.bb_strategy import BollingerBandsStrategy
from src.strategies.multi_indicator import MultiIndicatorStrategy
from src.backtest.engine import BacktestEngine
from src.backtest.reporter import BacktestReporter


def generate_sample_data(num_bars: int = 1000, trend: str = 'uptrend') -> list:
    """
    Generate synthetic OHLC data for backtesting
    
    Args:
        num_bars: Number of bars to generate
        trend: 'uptrend', 'downtrend', or 'sideways'
    """
    bars = []
    base_price = 1.0850
    base_time = datetime.now() - timedelta(hours=num_bars)
    
    for i in range(num_bars):
        # Generate price based on trend
        if trend == 'uptrend':
            trend_component = i * 0.00005
            noise = np.random.randn() * 0.0002
        elif trend == 'downtrend':
            trend_component = -i * 0.00005
            noise = np.random.randn() * 0.0002
        else:  # sideways
            trend_component = np.sin(i / 50) * 0.002
            noise = np.random.randn() * 0.0001
        
        price = base_price + trend_component + noise
        
        # Generate OHLC
        spread = 0.0002
        bar = OHLCBar(
            symbol="EURUSD",
            timeframe="H1",
            time=base_time + timedelta(hours=i),
            open=price,
            high=price + abs(np.random.randn() * 0.0003),
            low=price - abs(np.random.randn() * 0.0003),
            close=price + np.random.randn() * 0.0001,
            tick_volume=int(1000 + np.random.randn() * 200),
            real_volume=100000,
            spread=2
        )
        bars.append(bar)
    
    return bars


def test_single_strategy(strategy_name: str, strategy, bars: list):
    """Test a single strategy"""
    print(f"\n{'='*80}")
    print(f"  Testing: {strategy_name}")
    print(f"{'='*80}")
    
    engine = BacktestEngine(
        initial_balance=10000.0,
        commission=0.00002,  # 2 pips
        slippage=0.00001     # 1 pip
    )
    
    metrics, positions = engine.run(strategy, bars)
    
    BacktestReporter.print_summary(metrics, strategy_name)
    
    if len(positions) > 0:
        print(f"\n  First 5 Trades:")
        BacktestReporter.print_trades(positions[:5])
    
    return metrics


def compare_strategies(strategies: dict, bars: list):
    """Compare multiple strategies"""
    print(f"\n{'='*80}")
    print(f"  STRATEGY COMPARISON")
    print(f"{'='*80}\n")
    
    results = {}
    
    for name, strategy in strategies.items():
        engine = BacktestEngine(
            initial_balance=10000.0,
            commission=0.00002,
            slippage=0.00001
        )
        
        metrics, _ = engine.run(strategy, bars)
        results[name] = metrics
    
    BacktestReporter.print_comparison(results)


def main():
    """Run Phase 2 demonstration"""
    print("\n" + "="*80)
    print("  PHASE 2 COMPLETION DEMO")
    print("  Technical Indicators + Strategies + Backtesting")
    print("="*80)
    
    # Generate test data
    print("\nGenerating synthetic market data...")
    uptrend_data = generate_sample_data(1000, 'uptrend')
    downtrend_data = generate_sample_data(1000, 'downtrend')
    sideways_data = generate_sample_data(1000, 'sideways')
    
    print(f"  Generated {len(uptrend_data)} bars for uptrend market")
    print(f"  Generated {len(downtrend_data)} bars for downtrend market")
    print(f"  Generated {len(sideways_data)} bars for sideways market")
    
    # Test 1: Simple MA Strategy
    print("\n\n" + "="*80)
    print("  TEST 1: SIMPLE MOVING AVERAGE STRATEGY")
    print("="*80)
    ma_strategy = SimpleMovingAverageStrategy({'fast_period': 10, 'slow_period': 20})
    test_single_strategy("Simple MA Strategy", ma_strategy, uptrend_data)
    
    # Test 2: RSI Strategy
    print("\n\n" + "="*80)
    print("  TEST 2: RSI STRATEGY")
    print("="*80)
    rsi_strategy = RSIStrategy({'rsi_period': 14, 'oversold': 30, 'overbought': 70})
    test_single_strategy("RSI Strategy", rsi_strategy, sideways_data)
    
    # Test 3: MACD Strategy
    print("\n\n" + "="*80)
    print("  TEST 3: MACD STRATEGY")
    print("="*80)
    macd_strategy = MACDStrategy({'fast': 12, 'slow': 26, 'signal': 9})
    test_single_strategy("MACD Strategy", macd_strategy, uptrend_data)
    
    # Test 4: Bollinger Bands Strategy
    print("\n\n" + "="*80)
    print("  TEST 4: BOLLINGER BANDS STRATEGY")
    print("="*80)
    bb_strategy = BollingerBandsStrategy({'period': 20, 'std_dev': 2.0})
    test_single_strategy("Bollinger Bands Strategy", bb_strategy, sideways_data)
    
    # Test 5: Multi-Indicator Strategy
    print("\n\n" + "="*80)
    print("  TEST 5: MULTI-INDICATOR STRATEGY")
    print("="*80)
    multi_strategy = MultiIndicatorStrategy({
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'bb_period': 20
    })
    test_single_strategy("Multi-Indicator Strategy", multi_strategy, uptrend_data)
    
    # Test 6: Strategy Comparison
    print("\n\n" + "="*80)
    print("  TEST 6: STRATEGY COMPARISON (UPTREND MARKET)")
    print("="*80)
    
    strategies = {
        "MA Crossover": SimpleMovingAverageStrategy({'fast_period': 10, 'slow_period': 20}),
        "RSI": RSIStrategy({'rsi_period': 14, 'oversold': 30, 'overbought': 70}),
        "MACD": MACDStrategy({'fast': 12, 'slow': 26, 'signal': 9}),
        "Bollinger": BollingerBandsStrategy({'period': 20, 'std_dev': 2.0}),
        "Multi-Indicator": MultiIndicatorStrategy()
    }
    
    compare_strategies(strategies, uptrend_data)
    
    # Test 7: Different Market Conditions
    print("\n\n" + "="*80)
    print("  TEST 7: MA STRATEGY IN DIFFERENT MARKETS")
    print("="*80)
    
    ma_strat = SimpleMovingAverageStrategy(10, 20)
    
    print("\n--- UPTREND MARKET ---")
    engine1 = BacktestEngine(10000.0)
    m1, _ = engine1.run(ma_strat, uptrend_data)
    print(f"Total Profit: ${m1.total_profit:,.2f} | Win Rate: {m1.win_rate:.1f}%")
    
    print("\n--- DOWNTREND MARKET ---")
    engine2 = BacktestEngine(10000.0)
    m2, _ = engine2.run(ma_strat, downtrend_data)
    print(f"Total Profit: ${m2.total_profit:,.2f} | Win Rate: {m2.win_rate:.1f}%")
    
    print("\n--- SIDEWAYS MARKET ---")
    engine3 = BacktestEngine(10000.0)
    m3, _ = engine3.run(ma_strat, sideways_data)
    print(f"Total Profit: ${m3.total_profit:,.2f} | Win Rate: {m3.win_rate:.1f}%")
    
    # Summary
    print("\n\n" + "="*80)
    print("  PHASE 2 COMPLETION SUMMARY")
    print("="*80)
    print("\n  COMPLETED FEATURES:")
    print("  [x] Technical Indicators Module")
    print("      - SMA, EMA, RSI, MACD, Bollinger Bands")
    print("      - ATR, Stochastic, ADX, CCI, Williams %R")
    print("      - ROC, OBV")
    print("\n  [x] Trading Strategies (5)")
    print("      - Simple Moving Average Crossover")
    print("      - RSI Oscillator Strategy")
    print("      - MACD Crossover Strategy")
    print("      - Bollinger Bands Mean Reversion")
    print("      - Multi-Indicator Combined Strategy")
    print("\n  [x] Backtesting Engine")
    print("      - Historical data simulation")
    print("      - Position management")
    print("      - Commission and slippage modeling")
    print("      - Risk management (SL/TP)")
    print("\n  [x] Performance Analytics")
    print("      - Win rate, profit factor, Sharpe ratio")
    print("      - Max drawdown, average trade metrics")
    print("      - Trade-by-trade analysis")
    print("      - Strategy comparison reports")
    print("\n  STATUS: PHASE 2 COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
