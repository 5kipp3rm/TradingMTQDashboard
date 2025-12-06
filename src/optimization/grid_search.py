"""
Grid Search Optimization for Trading Strategies
Tests all combinations of parameters to find optimal settings
"""
import itertools
from typing import Dict, List, Any, Callable
import pandas as pd
from dataclasses import dataclass

from src.backtest import BacktestEngine


@dataclass
class OptimizationResult:
    """Single optimization result"""
    parameters: Dict[str, Any]
    metric_value: float
    all_metrics: Dict[str, Any]
    rank: int = 0


class GridSearchOptimizer:
    """
    Grid search parameter optimization
    
    Tests all possible combinations of parameters to find the best
    performing strategy configuration.
    """
    
    def __init__(self, backtest_engine: BacktestEngine,
                 optimization_metric: str = 'profit_factor'):
        """
        Initialize grid search optimizer
        
        Args:
            backtest_engine: Backtesting engine
            optimization_metric: Metric to optimize ('profit_factor', 'sharpe_ratio', 'total_profit', etc.)
        """
        self.engine = backtest_engine
        self.optimization_metric = optimization_metric
        self.results: List[OptimizationResult] = []
    
    def optimize(self, strategy_class, param_grid: Dict[str, List[Any]],
                bars: pd.DataFrame, symbol: str = "EURUSD",
                timeframe: str = "H1", volume: float = 0.01) -> OptimizationResult:
        """
        Run grid search optimization
        
        Args:
            strategy_class: Strategy class to optimize
            param_grid: Dictionary of parameters and their possible values
                Example: {
                    'fast_period': [10, 20, 30],
                    'slow_period': [50, 100, 200],
                    'sl_pips': [20, 30, 40]
                }
            bars: Historical OHLC data
            symbol: Trading symbol
            timeframe: Timeframe
            volume: Position size
            
        Returns:
            Best OptimizationResult
        """
        print(f"\n🔍 Starting Grid Search Optimization")
        print(f"   Metric: {self.optimization_metric}")
        
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(itertools.product(*param_values))
        
        total_combinations = len(combinations)
        print(f"   Testing {total_combinations} parameter combinations...")
        
        self.results = []
        
        # Test each combination
        for i, combo in enumerate(combinations, 1):
            # Create parameter dict
            params = dict(zip(param_names, combo))
            
            # Create strategy with these parameters
            strategy = strategy_class(params)
            
            # Run backtest
            try:
                metrics = self.engine.run(
                    strategy=strategy,
                    bars=bars,
                    symbol=symbol,
                    timeframe=timeframe,
                    volume=volume
                )
                
                # Get optimization metric value
                metric_value = getattr(metrics, self.optimization_metric, 0.0)
                
                # Store result
                result = OptimizationResult(
                    parameters=params,
                    metric_value=metric_value,
                    all_metrics=metrics.__dict__
                )
                self.results.append(result)
                
                # Progress update
                if i % max(1, total_combinations // 10) == 0:
                    print(f"   Progress: {i}/{total_combinations} ({i/total_combinations*100:.0f}%)")
            
            except Exception as e:
                print(f"   ⚠️  Error with params {params}: {e}")
        
        # Rank results
        self.results.sort(key=lambda x: x.metric_value, reverse=True)
        for rank, result in enumerate(self.results, 1):
            result.rank = rank
        
        best = self.results[0]
        
        print(f"\n✅ Optimization Complete!")
        print(f"   Best {self.optimization_metric}: {best.metric_value:.3f}")
        print(f"   Best parameters: {best.parameters}")
        
        return best
    
    def get_top_n(self, n: int = 10) -> List[OptimizationResult]:
        """Get top N results"""
        return self.results[:n]
    
    def print_summary(self, top_n: int = 5) -> None:
        """Print optimization summary"""
        print(f"\n{'='*80}")
        print(f"  GRID SEARCH OPTIMIZATION SUMMARY")
        print(f"{'='*80}")
        print(f"\nTotal combinations tested: {len(self.results)}")
        print(f"Optimization metric: {self.optimization_metric}")
        
        print(f"\nTop {top_n} results:")
        print(f"{'-'*80}")
        
        for i, result in enumerate(self.results[:top_n], 1):
            print(f"\n{i}. {self.optimization_metric.upper()}: {result.metric_value:.3f}")
            print(f"   Parameters: {result.parameters}")
            if 'total_trades' in result.all_metrics:
                print(f"   Trades: {result.all_metrics['total_trades']}, "
                      f"Win Rate: {result.all_metrics.get('win_rate', 0):.1f}%")
