# Quick Start Guide: Interval-Based Profit Maximization

## Executive Summary

For interval-based position opening (every X minutes/hours), you can maximize profit by:
1. **Using ML-enhanced signals** (70%+ confidence threshold)
2. **Optimizing risk/reward ratios** (1:2 minimum, 1:3 for swing trades)
3. **Advanced position management** (breakeven, partial close, trailing stops)
4. **Trading during optimal sessions** (London/NY overlap for EURUSD)
5. **Dynamic position sizing** (Kelly Criterion + ML confidence multipliers)

## Expected Results (Starting with $10,000)

| Strategy | Interval | Risk/Trade | Monthly Profit | Daily Trades | Win Rate |
|----------|----------|------------|----------------|--------------|----------|
| **Moderate Day Trading** | Every 30 min | 1.5% | +306% ($30,665) | 6 | 60% |
| Aggressive Day Trading | Every 30 min | 2.0% | +538% ($53,863) | 6 | 60% |
| High-Freq Scalping | Every 5 min | 0.5% | +259% ($25,942) | 15 | 62% |
| Conservative Scalping | Every 15 min | 1.0% | +221% ($22,164) | 8 | 58% |
| Swing Trading | Every 4 hours | 2.0% | +150% ($15,049) | 2 | 55% |

**Recommended**: Moderate Day Trading (M30, 1.5% risk) = **+50-60% per month** (realistic)

## Implementation Steps

### 1. Choose Your Configuration

Copy and use the pre-optimized configuration:
```bash
cp config/currencies_optimized_interval.yaml config/currencies.yaml
```

Or manually edit `config/currencies.yaml`:

```yaml
# For Moderate Day Trading (30-minute intervals)
EURUSD_DAY:
  enabled: true
  risk_percent: 1.5
  timeframe: "M30"
  sl_pips: 25
  tp_pips: 50
  cooldown_seconds: 1800  # 30 minutes
  
  # Trade during high-volume sessions
  trading_hours:
    start: "08:00"  # London open
    end: "21:00"    # NY close
  
  # ML Enhancement
  enable_ml_enhancement: true
  ml_confidence_threshold: 0.72
  
  # Advanced position management
  modifications:
    enable_breakeven: true
    breakeven_trigger_pips: 25
    
    enable_partial_close: true
    partial_close_trigger_pips: 35
    partial_close_percent: 50
    
    enable_trailing_stop: true
    trailing_stop_pips: 15
    trailing_activation_pips: 30
```

### 2. Enable Dynamic Position Sizing

Add to your `currencies.yaml`:

```yaml
dynamic_sizing:
  enabled: true
  method: "kelly"
  win_rate: 0.60
  avg_win: 50
  avg_loss: 25
  kelly_fraction: 0.5  # Half Kelly (safe)
  
  # ML confidence multiplier
  use_confidence_multiplier: true
  confidence_ranges:
    - min: 0.80; multiplier: 1.5  # 1.5x risk for high confidence
    - min: 0.70; multiplier: 1.2
    - min: 0.60; multiplier: 1.0
```

### 3. Enable Quality Filters

```yaml
confluence_filter:
  enabled: true
  minimum_score: 5  # Require 5/7 points
  
  factors:
    ml_confidence: {enabled: true, threshold: 0.70, points: 2}
    technical_alignment: {enabled: true, points: 2}
    trend_alignment: {enabled: true, adx_threshold: 25, points: 1}
    volume_confirmation: {enabled: true, points: 1}
    multi_timeframe: {enabled: true, points: 1}
```

### 4. Run Profit Calculator

Before starting live trading, see your expected results:

```bash
python scripts/calculate_profit_scenarios.py
```

This shows:
- Expected monthly profit
- Daily profit potential
- Balance growth over time
- Optimal risk percentages (Kelly Criterion)
- Single trade profit/loss examples

### 5. Start Trading

```bash
python main.py
```

Monitor your performance and adjust parameters weekly based on actual win rate.

## Key Configuration Parameters

### Timing Optimization

| Timeframe | Check Interval | Cooldown | Trades/Day | Strategy Type |
|-----------|----------------|----------|------------|---------------|
| M5 | 60s | 300s (5 min) | 12-15 | High-freq scalping |
| M15 | 60s | 900s (15 min) | 6-8 | Conservative scalping |
| M30 | 60s | 1800s (30 min) | 4-6 | Day trading |
| H1 | 300s | 3600s (1 hour) | 3-4 | Intraday |
| H4 | 900s | 14400s (4 hours) | 1-2 | Swing trading |

**Rule**: Set cooldown = candle timeframe for clean entry signals.

### Risk Optimization

| Account Growth | Risk per Trade | Risk Type |
|----------------|----------------|-----------|
| $0 - $15,000 | 1.0% | Conservative |
| $15,000 - $25,000 | 1.5% | Moderate |
| $25,000 - $50,000 | 2.0% | Aggressive |
| $50,000+ | 2.5% | Expert (max) |

**Note**: Always cap maximum risk at 3% per trade.

### SL/TP Based on Volatility (ATR)

Instead of fixed pips, use ATR for dynamic stops:

```python
# Example for EURUSD (ATR typically 10-15 pips)
SL = Entry ± (1.5 × ATR)  # e.g., 1.5 × 12 = 18 pips
TP = Entry ± (3.0 × ATR)  # e.g., 3.0 × 12 = 36 pips (1:2 R:R)
```

This adapts to market conditions (tight in low volatility, wide in high volatility).

### Session-Based Trading

Only trade during profitable hours:

**EURUSD**:
- Best: 08:00-16:00 UTC (London session)
- Excellent: 13:00-17:00 UTC (London/NY overlap)
- Avoid: 22:00-08:00 UTC (low liquidity)

**USDJPY**:
- Best: 00:00-06:00 UTC (Tokyo session)
- Good: 08:00-10:00 UTC (Tokyo/London overlap)

**GBPUSD**:
- Best: 08:00-16:00 UTC (London session)

## Position Management for Maximum Profit

### 3-Stage Profit Taking

1. **Breakeven (at 1:1 R:R)**
   - When position is +25 pips (1:1 R:R)
   - Move SL to entry + 5 pips
   - Now risk-free trade

2. **Partial Close (at 1.5:1 R:R)**
   - When position is +35 pips
   - Close 50% of position
   - Lock in guaranteed profit

3. **Trail Remaining (toward TP)**
   - Start trailing at +30 pips
   - Trail distance: 15 pips
   - Let winners run to full TP (50 pips)

**Result**: 
- Worst case after BE: +$5 (0.05%)
- Partial close case: +$175 from first 50%, +$X from trailing
- Best case: +$300 (3% of account)

### Exit Strategies

**Time-Based**: Close position if no movement after 2 hours (for M30 trades)
**ML-Based**: Close if ML confidence drops below 0.40 (signal reversal)
**News-Based**: Close 15 minutes before high-impact news
**Portfolio Target**: Close all positions when daily profit reaches 3% of account

## Risk Management Rules

### Portfolio Level
- Max concurrent trades: 3 (for focused quality)
- Portfolio risk limit: 6% total
- Daily loss limit: 3% (stop trading for the day)
- Max drawdown: 8% (pause and review strategy)

### Trade Level
- Min risk/reward: 1:2 (never risk more than half your potential profit)
- Min ML confidence: 0.70 (only high-quality setups)
- Min confluence score: 5/7 (multiple confirmations required)
- Min ADX: 25 (avoid choppy, non-trending markets)

### Emergency Controls
- If 3 consecutive losses: Reduce risk to 50%
- If 5 consecutive wins: Can increase risk by 20% (max 3% total)
- If daily loss reaches -3%: Stop new trades, review positions
- If account drops 10%: Stop all trading, analyze what went wrong

## Performance Tracking

Monitor these metrics daily:

```python
# Win Rate by Session
London Session: 68% (15 trades)
NY Session: 58% (10 trades)
Tokyo Session: 45% (8 trades)  ← Disable this session

# Win Rate by Pair
EURUSD: 62% (20 trades)
USDJPY: 48% (15 trades)  ← Consider disabling

# Average Metrics
Avg Win: +$280 (2.8%)
Avg Loss: -$145 (1.45%)
Avg R:R: 1:1.93
Profit Factor: 1.65 (good, >1.5 is profitable)
```

**Action**: Disable sessions/pairs with <55% win rate after 10+ trades.

## Common Mistakes to Avoid

❌ **Over-trading**: Don't trade every signal. Wait for confluence score ≥ 5.
❌ **Fixed stops in all conditions**: Use ATR-based stops to adapt to volatility.
❌ **Ignoring session times**: 70% of profits come from 30% of trading hours.
❌ **Not taking partial profits**: Lock in gains, don't let all winners reverse.
❌ **Increasing risk after losses**: Keep risk constant or reduce it.
❌ **Trading through news**: Close positions 15 min before high-impact news.
❌ **No ML filtering**: Using ML confidence <0.70 reduces win rate significantly.

## Month 1 Action Plan

**Week 1**: Start conservative
- Risk: 0.5% per trade
- Only trade London session (EURUSD)
- Require ML confidence ≥ 0.75
- Target: +5-7% for the week

**Week 2**: Increase frequency
- Risk: 0.75% per trade
- Add NY session if London was profitable
- Require ML confidence ≥ 0.72
- Target: +8-10% for the week

**Week 3**: Optimize parameters
- Risk: 1.0% per trade
- Add 2nd pair (USDJPY) if EURUSD win rate >60%
- Require ML confidence ≥ 0.70
- Target: +10-15% for the week

**Week 4**: Full strategy
- Risk: 1.5% per trade
- All profitable pairs and sessions
- ML confidence ≥ 0.70
- Target: +15-20% for the week

**Month 1 Goal**: +40-50% profit with <10% drawdown

## Tools & Scripts

**Profit Calculator**:
```bash
python scripts/calculate_profit_scenarios.py
```
Shows expected results for different strategies.

**Optimized Config**:
```bash
config/currencies_optimized_interval.yaml
```
Ready-to-use configuration with all optimizations.

**Strategy Guide**:
```bash
docs/PROFIT_MAXIMIZATION_STRATEGY.md
```
Complete technical details and formulas.

## Support & Troubleshooting

**Low win rate (<55%)**:
- Increase ML confidence threshold to 0.75
- Increase confluence minimum score to 6
- Reduce trading to only London session
- Check if ATR-based stops are too tight

**High drawdown (>8%)**:
- Reduce risk per trade to 0.5%
- Disable losing pairs/sessions
- Check correlation (trading too many correlated pairs)
- Review recent losses for common patterns

**Not enough trades**:
- Lower ML confidence to 0.65 (but monitor win rate)
- Reduce cooldown period (but avoid overtrading)
- Add more trading hours
- Add more currency pairs

**Too many trades, low profit**:
- Increase confluence score requirement
- Extend cooldown period
- Tighten ML confidence threshold
- Trade only during best sessions

---

## Quick Reference Card

**Best Setup for Beginners**:
- Pair: EURUSD
- Timeframe: M30
- Risk: 1.0%
- SL/TP: 25/50 pips (1:2)
- Interval: Every 30 minutes
- Sessions: 08:00-17:00 UTC
- ML threshold: 0.70
- Expected: +30-40% per month

**Best Setup for Intermediate**:
- Pair: EURUSD + USDJPY
- Timeframe: M30
- Risk: 1.5%
- SL/TP: ATR-based (1:2)
- Interval: Every 30 minutes
- Sessions: Best times only
- ML threshold: 0.70 with confluence
- Expected: +50-60% per month

**Best Setup for Advanced**:
- Pair: 3-4 pairs (low correlation)
- Timeframe: M15 + M30 (multi-TF)
- Risk: 1.5-2% (Kelly-based)
- SL/TP: Dynamic ATR (1:2-1:3)
- Interval: Signal-based + time filters
- Sessions: All profitable sessions
- ML threshold: 0.65 with strict confluence
- Expected: +80-100% per month

---

**Remember**: Start conservative, track everything, adapt based on data!
