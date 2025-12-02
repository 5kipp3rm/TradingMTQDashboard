"""
Backtest Reporter
Generate comprehensive performance reports
"""
from typing import List, Dict
from datetime import datetime
import logging

from .engine import BacktestMetrics, BacktestPosition

logger = logging.getLogger(__name__)


class BacktestReporter:
    """
    Generate and format backtest reports
    
    Features:
    - Console reports
    - Trade-by-trade breakdown
    - Performance summaries
    - Comparison reports
    """
    
    @staticmethod
    def print_summary(metrics: BacktestMetrics, strategy_name: str = "Strategy"):
        """
        Print comprehensive backtest summary
        
        Args:
            metrics: Backtest metrics
            strategy_name: Name of the strategy
        """
        print("\n" + "="*70)
        print(f"BACKTEST RESULTS: {strategy_name}")
        print("="*70)
        
        # Trade Statistics
        print("\n📊 TRADE STATISTICS")
        print("-" * 70)
        print(f"Total Trades:        {metrics.total_trades}")
        print(f"Winning Trades:      {metrics.winning_trades} ({metrics.win_rate:.1f}%)")
        print(f"Losing Trades:       {metrics.losing_trades}")
        print(f"Break-Even Trades:   {metrics.break_even_trades}")
        
        # Profit Metrics
        print("\n💰 PROFIT METRICS")
        print("-" * 70)
        print(f"Total Profit:        ${metrics.total_profit:,.2f}")
        print(f"Total Profit (pips): {metrics.total_profit_pips:,.1f}")
        print(f"Average Profit:      ${metrics.avg_profit:.2f} ({metrics.avg_profit_pips:.1f} pips)")
        print(f"Best Trade:          ${metrics.max_win:,.2f}")
        print(f"Worst Trade:         ${metrics.max_loss:,.2f}")
        print(f"Average Win:         ${metrics.avg_win:.2f}")
        print(f"Average Loss:        ${metrics.avg_loss:.2f}")
        
        # Risk Metrics
        print("\n⚠️  RISK METRICS")
        print("-" * 70)
        print(f"Profit Factor:       {metrics.profit_factor:.2f}")
        print(f"Sharpe Ratio:        {metrics.sharpe_ratio:.2f}")
        print(f"Max Drawdown:        ${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_pct:.1f}%)")
        print(f"Win Streak:          {metrics.largest_win_streak}")
        print(f"Loss Streak:         {metrics.largest_loss_streak}")
        print(f"Avg Trade Duration:  {metrics.avg_trade_duration:.1f} hours")
        
        # Performance Rating
        print("\n⭐ PERFORMANCE RATING")
        print("-" * 70)
        rating = BacktestReporter._calculate_rating(metrics)
        print(f"Overall Rating:      {rating['stars']} ({rating['score']:.1f}/100)")
        print(f"Assessment:          {rating['assessment']}")
        
        print("="*70 + "\n")
    
    @staticmethod
    def print_trades(positions: List[BacktestPosition], limit: int = 10):
        """
        Print trade-by-trade breakdown
        
        Args:
            positions: List of backtest positions
            limit: Maximum number of trades to display
        """
        closed = [p for p in positions if p.exit_time is not None]
        
        if not closed:
            print("No closed trades to display")
            return
        
        print("\n" + "="*120)
        print("TRADE BREAKDOWN")
        print("="*120)
        print(f"{'#':<4} {'Type':<5} {'Entry Time':<20} {'Exit Time':<20} {'Entry':<10} {'Exit':<10} {'Profit':<12} {'Pips':<8} {'Reason':<15}")
        print("-"*120)
        
        for i, pos in enumerate(closed[:limit], 1):
            entry_time = pos.entry_time.strftime("%Y-%m-%d %H:%M") if pos.entry_time else "N/A"
            exit_time = pos.exit_time.strftime("%Y-%m-%d %H:%M") if pos.exit_time else "N/A"
            
            profit_str = f"${pos.profit:+.2f}"
            pips_str = f"{pos.profit_pips:+.1f}"
            
            print(f"{i:<4} {pos.position_type.value:<5} {entry_time:<20} {exit_time:<20} "
                  f"{pos.entry_price:<10.5f} {pos.exit_price:<10.5f} {profit_str:<12} {pips_str:<8} {pos.exit_reason:<15}")
        
        if len(closed) > limit:
            print(f"\n... and {len(closed) - limit} more trades")
        
        print("="*120 + "\n")
    
    @staticmethod
    def compare_strategies(results: Dict[str, BacktestMetrics]):
        """
        Compare multiple strategy results
        
        Args:
            results: Dictionary of {strategy_name: BacktestMetrics}
        """
        if len(results) < 2:
            print("Need at least 2 strategies to compare")
            return
        
        print("\n" + "="*100)
        print("STRATEGY COMPARISON")
        print("="*100)
        
        # Header
        strategies = list(results.keys())
        header = f"{'Metric':<25}"
        for name in strategies:
            header += f"{name[:20]:<22}"
        print(header)
        print("-"*100)
        
        # Metrics to compare
        metrics_to_compare = [
            ('Total Trades', lambda m: f"{m.total_trades}"),
            ('Win Rate %', lambda m: f"{m.win_rate:.1f}%"),
            ('Total Profit', lambda m: f"${m.total_profit:,.2f}"),
            ('Avg Profit/Trade', lambda m: f"${m.avg_profit:.2f}"),
            ('Profit Factor', lambda m: f"{m.profit_factor:.2f}"),
            ('Sharpe Ratio', lambda m: f"{m.sharpe_ratio:.2f}"),
            ('Max Drawdown %', lambda m: f"{m.max_drawdown_pct:.1f}%"),
            ('Avg Win', lambda m: f"${m.avg_win:.2f}"),
            ('Avg Loss', lambda m: f"${m.avg_loss:.2f}"),
        ]
        
        for metric_name, metric_func in metrics_to_compare:
            row = f"{metric_name:<25}"
            for name in strategies:
                value = metric_func(results[name])
                row += f"{value:<22}"
            print(row)
        
        # Best strategy
        print("\n" + "-"*100)
        best_strategy = max(results.items(), 
                          key=lambda x: BacktestReporter._calculate_rating(x[1])['score'])
        print(f"🏆 BEST STRATEGY: {best_strategy[0]} (Score: {BacktestReporter._calculate_rating(best_strategy[1])['score']:.1f}/100)")
        print("="*100 + "\n")
    
    @staticmethod
    def _calculate_rating(metrics: BacktestMetrics) -> Dict:
        """
        Calculate overall performance rating
        
        Returns:
            Dictionary with score, stars, and assessment
        """
        if metrics.total_trades == 0:
            return {
                'score': 0,
                'stars': '☆☆☆☆☆',
                'assessment': 'No trades executed'
            }
        
        score = 0
        
        # Win rate (max 25 points)
        if metrics.win_rate >= 60:
            score += 25
        elif metrics.win_rate >= 50:
            score += 20
        elif metrics.win_rate >= 40:
            score += 15
        else:
            score += 10
        
        # Profit factor (max 25 points)
        if metrics.profit_factor >= 2.0:
            score += 25
        elif metrics.profit_factor >= 1.5:
            score += 20
        elif metrics.profit_factor >= 1.2:
            score += 15
        elif metrics.profit_factor >= 1.0:
            score += 10
        else:
            score += 0
        
        # Sharpe ratio (max 20 points)
        if metrics.sharpe_ratio >= 2.0:
            score += 20
        elif metrics.sharpe_ratio >= 1.5:
            score += 15
        elif metrics.sharpe_ratio >= 1.0:
            score += 10
        else:
            score += 5
        
        # Drawdown (max 15 points)
        if metrics.max_drawdown_pct <= 5:
            score += 15
        elif metrics.max_drawdown_pct <= 10:
            score += 12
        elif metrics.max_drawdown_pct <= 15:
            score += 8
        else:
            score += 4
        
        # Total profit (max 15 points)
        if metrics.total_profit > 0:
            score += 15
        elif metrics.total_profit == 0:
            score += 8
        else:
            score += 0
        
        # Stars
        if score >= 80:
            stars = '⭐⭐⭐⭐⭐'
            assessment = 'Excellent - Ready for live trading'
        elif score >= 65:
            stars = '⭐⭐⭐⭐☆'
            assessment = 'Good - Consider optimization'
        elif score >= 50:
            stars = '⭐⭐⭐☆☆'
            assessment = 'Fair - Needs improvement'
        elif score >= 35:
            stars = '⭐⭐☆☆☆'
            assessment = 'Poor - Significant issues'
        else:
            stars = '⭐☆☆☆☆'
            assessment = 'Very Poor - Not recommended'
        
        return {
            'score': score,
            'stars': stars,
            'assessment': assessment
        }
    
    @staticmethod
    def generate_equity_curve_data(metrics: BacktestMetrics) -> Dict:
        """
        Generate data for equity curve plotting
        
        Args:
            metrics: Backtest metrics with equity_curve
            
        Returns:
            Dictionary with dates and equity values
        """
        if not metrics.equity_curve or not metrics.dates:
            return {'dates': [], 'equity': []}
        
        return {
            'dates': metrics.dates,
            'equity': metrics.equity_curve,
            'initial': metrics.equity_curve[0] if metrics.equity_curve else 0,
            'final': metrics.equity_curve[-1] if metrics.equity_curve else 0,
            'peak': max(metrics.equity_curve) if metrics.equity_curve else 0,
            'trough': min(metrics.equity_curve) if metrics.equity_curve else 0,
        }
