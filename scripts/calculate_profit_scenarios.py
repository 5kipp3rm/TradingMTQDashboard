"""
Profit Calculator for Interval-Based Trading Strategies

This script helps you calculate expected profits, position sizes, and risks
for different interval-based trading approaches.
"""

from dataclasses import dataclass
from typing import List, Tuple
import math


@dataclass
class TradingScenario:
    """Parameters for a trading scenario"""
    name: str
    account_balance: float
    risk_percent: float
    sl_pips: int
    tp_pips: int
    win_rate: float
    trades_per_day: int
    trading_days_per_month: int = 20


@dataclass
class TradeResult:
    """Result of a single trade"""
    profit_usd: float
    profit_percent: float
    risk_usd: float


def calculate_position_size(
    balance: float,
    risk_percent: float,
    sl_pips: int,
    pip_value: float = 10.0  # For 1 standard lot EURUSD
) -> Tuple[float, float]:
    """
    Calculate position size using risk-based method
    
    Args:
        balance: Account balance in USD
        risk_percent: Percentage of balance to risk
        sl_pips: Stop loss in pips
        pip_value: Pip value per standard lot (default 10 for EURUSD)
    
    Returns:
        (lot_size, risk_amount_usd)
    """
    risk_amount = balance * (risk_percent / 100.0)
    
    # Lot size = Risk Amount / (SL in pips × pip value per lot)
    lot_size = risk_amount / (sl_pips * pip_value)
    
    return lot_size, risk_amount


def calculate_trade_outcome(
    balance: float,
    risk_percent: float,
    sl_pips: int,
    tp_pips: int,
    win: bool = True,
    pip_value: float = 10.0
) -> TradeResult:
    """Calculate outcome of a single trade"""
    lot_size, risk_amount = calculate_position_size(
        balance, risk_percent, sl_pips, pip_value
    )
    
    if win:
        profit_usd = lot_size * tp_pips * pip_value
    else:
        profit_usd = -risk_amount
    
    profit_percent = (profit_usd / balance) * 100
    
    return TradeResult(
        profit_usd=profit_usd,
        profit_percent=profit_percent,
        risk_usd=risk_amount
    )


def simulate_trading_period(scenario: TradingScenario) -> dict:
    """
    Simulate trading over a period with compounding
    
    Returns detailed statistics including:
    - Daily profit
    - Monthly profit
    - Total trades
    - Win/loss distribution
    - Final balance
    """
    balance = scenario.account_balance
    daily_balances = []
    total_wins = 0
    total_losses = 0
    
    # Calculate expected wins and losses per day
    wins_per_day = scenario.trades_per_day * scenario.win_rate
    losses_per_day = scenario.trades_per_day * (1 - scenario.win_rate)
    
    # Simulate each day
    for day in range(scenario.trading_days_per_month):
        day_start_balance = balance
        
        # Simulate trades for the day
        for trade_num in range(scenario.trades_per_day):
            # Determine if this trade wins (probabilistically)
            trade_position = total_wins + total_losses
            expected_wins_so_far = trade_position * scenario.win_rate
            
            # Win if we're below expected win count
            is_win = total_wins < expected_wins_so_far + 0.5
            
            # Calculate trade result
            result = calculate_trade_outcome(
                balance=balance,
                risk_percent=scenario.risk_percent,
                sl_pips=scenario.sl_pips,
                tp_pips=scenario.tp_pips,
                win=is_win
            )
            
            # Update balance (compounding)
            balance += result.profit_usd
            
            # Track wins/losses
            if is_win:
                total_wins += 1
            else:
                total_losses += 1
        
        daily_balances.append(balance)
    
    # Calculate statistics
    total_trades = total_wins + total_losses
    final_balance = balance
    total_profit = final_balance - scenario.account_balance
    total_profit_percent = (total_profit / scenario.account_balance) * 100
    
    # Average daily profit
    daily_profits = [
        daily_balances[i] - (daily_balances[i-1] if i > 0 else scenario.account_balance)
        for i in range(len(daily_balances))
    ]
    avg_daily_profit = sum(daily_profits) / len(daily_profits)
    avg_daily_profit_percent = (avg_daily_profit / scenario.account_balance) * 100
    
    return {
        "scenario_name": scenario.name,
        "starting_balance": scenario.account_balance,
        "final_balance": final_balance,
        "total_profit_usd": total_profit,
        "total_profit_percent": total_profit_percent,
        "total_trades": total_trades,
        "winning_trades": total_wins,
        "losing_trades": total_losses,
        "actual_win_rate": total_wins / total_trades if total_trades > 0 else 0,
        "avg_daily_profit_usd": avg_daily_profit,
        "avg_daily_profit_percent": avg_daily_profit_percent,
        "trading_days": scenario.trading_days_per_month,
        "daily_balances": daily_balances,
    }


def calculate_kelly_criterion(win_rate: float, avg_win_pips: int, avg_loss_pips: int) -> float:
    """
    Calculate optimal risk percent using Kelly Criterion
    
    Kelly % = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
    
    Args:
        win_rate: Win rate as decimal (e.g., 0.60 for 60%)
        avg_win_pips: Average winning trade in pips
        avg_loss_pips: Average losing trade in pips
    
    Returns:
        Optimal risk percent (use half for conservative approach)
    """
    loss_rate = 1 - win_rate
    kelly = (win_rate * avg_win_pips - loss_rate * avg_loss_pips) / avg_win_pips
    
    # Return as percentage
    return kelly * 100


def print_scenario_results(results: dict):
    """Print formatted results of a trading scenario"""
    print(f"\n{'='*70}")
    print(f"SCENARIO: {results['scenario_name']}")
    print(f"{'='*70}")
    print(f"Starting Balance:     ${results['starting_balance']:,.2f}")
    print(f"Final Balance:        ${results['final_balance']:,.2f}")
    print(f"Total Profit:         ${results['total_profit_usd']:,.2f} ({results['total_profit_percent']:.2f}%)")
    print(f"\nTrading Statistics:")
    print(f"  Total Trades:       {results['total_trades']}")
    print(f"  Winning Trades:     {results['winning_trades']} ({results['actual_win_rate']*100:.1f}%)")
    print(f"  Losing Trades:      {results['losing_trades']}")
    print(f"  Trading Days:       {results['trading_days']}")
    print(f"\nDaily Performance:")
    print(f"  Avg Daily Profit:   ${results['avg_daily_profit_usd']:,.2f} ({results['avg_daily_profit_percent']:.2f}%)")
    
    # Show balance growth over time (weekly snapshots)
    print(f"\nBalance Growth (Weekly):")
    balances = results['daily_balances']
    for week in range(0, len(balances), 5):
        if week < len(balances):
            week_num = week // 5 + 1
            balance = balances[week]
            profit = balance - results['starting_balance']
            profit_pct = (profit / results['starting_balance']) * 100
            print(f"  Week {week_num}: ${balance:,.2f} (+${profit:,.2f}, +{profit_pct:.1f}%)")


def main():
    """Run profit calculations for different trading scenarios"""
    
    print("="*70)
    print("TRADING PROFIT CALCULATOR - Interval-Based Strategies")
    print("="*70)
    
    # Define scenarios
    scenarios = [
        TradingScenario(
            name="Conservative Scalping (M15, Every 15 min)",
            account_balance=10000,
            risk_percent=1.0,
            sl_pips=15,
            tp_pips=30,
            win_rate=0.58,
            trades_per_day=8,
        ),
        TradingScenario(
            name="Moderate Day Trading (M30, Every 30 min)",
            account_balance=10000,
            risk_percent=1.5,
            sl_pips=25,
            tp_pips=50,
            win_rate=0.60,
            trades_per_day=6,
        ),
        TradingScenario(
            name="Aggressive Day Trading (M30, Every 30 min)",
            account_balance=10000,
            risk_percent=2.0,
            sl_pips=25,
            tp_pips=50,
            win_rate=0.60,
            trades_per_day=6,
        ),
        TradingScenario(
            name="Swing Trading (H4, Every 4 hours)",
            account_balance=10000,
            risk_percent=2.0,
            sl_pips=60,
            tp_pips=180,
            win_rate=0.55,
            trades_per_day=2,
        ),
        TradingScenario(
            name="High-Frequency Scalping (M5, Every 5 min)",
            account_balance=10000,
            risk_percent=0.5,
            sl_pips=10,
            tp_pips=20,
            win_rate=0.62,
            trades_per_day=15,
        ),
    ]
    
    # Run simulations
    all_results = []
    for scenario in scenarios:
        results = simulate_trading_period(scenario)
        all_results.append(results)
        print_scenario_results(results)
    
    # Compare scenarios
    print(f"\n{'='*70}")
    print("SCENARIO COMPARISON")
    print(f"{'='*70}")
    print(f"{'Scenario':<45} {'Monthly Profit':<20} {'Risk Level'}")
    print(f"{'-'*70}")
    
    for results in all_results:
        scenario = next(s for s in scenarios if s.name == results['scenario_name'])
        print(f"{results['scenario_name']:<45} "
              f"+{results['total_profit_percent']:>6.1f}% (${results['total_profit_usd']:>7,.0f})  "
              f"{scenario.risk_percent:.1f}%/trade")
    
    # Kelly Criterion recommendations
    print(f"\n{'='*70}")
    print("KELLY CRITERION - OPTIMAL RISK CALCULATION")
    print(f"{'='*70}")
    
    kelly_scenarios = [
        ("Scalping (15 pip SL, 30 pip TP, 58% WR)", 0.58, 30, 15),
        ("Day Trading (25 pip SL, 50 pip TP, 60% WR)", 0.60, 50, 25),
        ("Swing Trading (60 pip SL, 180 pip TP, 55% WR)", 0.55, 180, 60),
    ]
    
    for name, win_rate, avg_win, avg_loss in kelly_scenarios:
        kelly = calculate_kelly_criterion(win_rate, avg_win, avg_loss)
        half_kelly = kelly / 2
        
        print(f"\n{name}")
        print(f"  Full Kelly:        {kelly:.2f}% risk per trade")
        print(f"  Half Kelly:        {half_kelly:.2f}% risk per trade (recommended)")
        print(f"  Quarter Kelly:     {kelly/4:.2f}% risk per trade (conservative)")
    
    # Single trade examples
    print(f"\n{'='*70}")
    print("SINGLE TRADE PROFIT/LOSS EXAMPLES")
    print(f"{'='*70}")
    
    account = 10000
    risk = 1.5
    
    print(f"\nAccount Balance: ${account:,.2f}")
    print(f"Risk per Trade: {risk}%")
    
    trade_examples = [
        ("Scalping", 15, 30),
        ("Day Trading", 25, 50),
        ("Swing Trading", 60, 180),
    ]
    
    for name, sl, tp in trade_examples:
        win = calculate_trade_outcome(account, risk, sl, tp, win=True)
        loss = calculate_trade_outcome(account, risk, sl, tp, win=False)
        
        print(f"\n{name} (SL: {sl} pips, TP: {tp} pips):")
        print(f"  Winning Trade:     +${win.profit_usd:,.2f} (+{win.profit_percent:.2f}%)")
        print(f"  Losing Trade:      -${abs(loss.profit_usd):,.2f} (-{abs(loss.profit_percent):.2f}%)")
        print(f"  Risk:Reward Ratio: 1:{tp/sl:.1f}")
    
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print(f"{'='*70}")
    print("""
1. START CONSERVATIVE:
   - Begin with 0.5-1% risk per trade
   - Use scalping or day trading approach (M15-M30)
   - Target 60%+ win rate with ML enhancement
   
2. FOCUS ON QUALITY:
   - Trade only during high-volume sessions (London/NY overlap)
   - Use ML confidence threshold ≥ 0.70
   - Require multiple confirmations (confluence score ≥ 5)
   
3. POSITION MANAGEMENT:
   - Always use breakeven (move SL to BE at 1:1 R:R)
   - Take partial profits (50% at 1.5:1)
   - Trail remaining position
   
4. COMPOUND WISELY:
   - Reinvest profits automatically
   - Increase risk as account grows (use tiered approach)
   - Cap maximum risk at 3% per trade
   
5. TRACK & ADAPT:
   - Monitor win rate by session/pair
   - Disable losing sessions (<55% win rate)
   - Adjust parameters based on data, not emotions
   
REALISTIC MONTHLY TARGETS:
   - Conservative (1% risk):   +30-40% per month
   - Moderate (1.5% risk):     +40-60% per month  ← Recommended
   - Aggressive (2%+ risk):    +60-100% per month (higher drawdown risk)
   
Remember: Past performance doesn't guarantee future results.
Always backtest your strategy before live trading!
""")


if __name__ == "__main__":
    main()
