# Profit Maximization Strategy for Interval-Based Trading

## Overview
When opening a single position at fixed intervals (e.g., every X minutes/hours), maximizing profit requires optimizing multiple factors simultaneously.

## Key Strategies

### 1. **Optimal Timing Selection**

#### A. Market Session Alignment
```yaml
# Best times to trade (UTC):
EURUSD: 
  - London Open: 08:00-12:00 (highest volatility)
  - London-NY Overlap: 13:00-17:00 (highest volume)
  
USDJPY:
  - Tokyo Session: 00:00-06:00
  - London Open: 08:00-10:00
  
GBPUSD:
  - London Session: 08:00-16:00
```

**Implementation**: Use `trading_hours` in `currencies.yaml`:
```yaml
EURUSD:
  trading_hours:
    start: "08:00"  # London open
    end: "17:00"    # NY close
```

#### B. Interval Optimization
- **5-15 minute intervals**: Scalping (tight SL/TP, 0.5-1% per trade)
- **30-60 minute intervals**: Day trading (moderate SL/TP, 1-2% per trade)
- **4+ hour intervals**: Swing trading (wide SL/TP, 2-5% per trade)

### 2. **Position Sizing Optimization**

#### A. Kelly Criterion (Optimal Risk)
```
Kelly % = (Win Rate × Avg Win - (1 - Win Rate) × Avg Loss) / Avg Win

Example:
- Win Rate: 60% (0.6)
- Avg Win: $40
- Avg Loss: $20

Kelly % = (0.6 × 40 - 0.4 × 20) / 40
        = (24 - 8) / 40
        = 0.4 = 40%

Conservative Kelly = 40% / 2 = 20% (half Kelly)
```

**Implementation**:
```python
def calculate_optimal_risk(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Calculate optimal risk using Kelly Criterion"""
    kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
    # Use half Kelly for safety
    return max(0.5, min(kelly / 2 * 100, 3.0))  # Cap at 3%
```

#### B. Dynamic Position Sizing Based on Confidence
```python
# Base risk: 1%
# ML confidence adjustment: 0.5x to 2x
# Final risk = base_risk × confidence_multiplier

if ml_confidence > 0.8:
    risk_multiplier = 1.5  # 1.5% risk
elif ml_confidence > 0.7:
    risk_multiplier = 1.2  # 1.2% risk
elif ml_confidence > 0.6:
    risk_multiplier = 1.0  # 1.0% risk
else:
    risk_multiplier = 0.5  # 0.5% risk or skip
```

### 3. **Entry Signal Quality**

#### A. Multi-Timeframe Confirmation
```python
# Check alignment across timeframes
H1_trend = "UP"    # Higher timeframe trend
M15_signal = "BUY"  # Entry timeframe signal
M5_momentum = "STRONG"  # Lower timeframe confirmation

# Only enter if aligned
if all_aligned:
    confidence_multiplier = 1.5
```

#### B. ML-Enhanced Entries
```python
# Current implementation
ml_confidence = 0.62  # From ensemble model

# Enhanced with multiple factors:
ml_signal = get_ml_prediction(bars)
technical_signal = get_technical_signal(bars)
sentiment = get_market_sentiment(symbol)

# Combine scores
final_confidence = (
    ml_signal.confidence * 0.5 +
    technical_signal.confidence * 0.3 +
    sentiment.score * 0.2
)

# Only trade if confidence > threshold
if final_confidence >= 0.7:
    open_position()
```

### 4. **Risk-Reward Optimization**

#### A. Dynamic SL/TP Based on Volatility
```python
from ta.volatility import AverageTrueRange

def calculate_dynamic_sltp(bars, atr_multiplier=2.0):
    """Calculate SL/TP based on ATR"""
    atr = AverageTrueRange(bars.high, bars.low, bars.close, window=14).average_true_range()
    current_atr = atr.iloc[-1]
    
    # SL: 1.5 × ATR
    # TP: 3.0 × ATR (Risk:Reward = 1:2)
    sl_distance = current_atr * 1.5
    tp_distance = current_atr * 3.0
    
    return sl_distance, tp_distance
```

**Configuration**:
```yaml
EURUSD:
  use_dynamic_sltp: true
  atr_period: 14
  sl_atr_multiplier: 1.5
  tp_atr_multiplier: 3.0  # 1:2 risk-reward
```

#### B. Minimum Risk-Reward Ratio
```python
# Only enter trades with R:R ≥ 1:2
risk = entry_price - stop_loss
reward = take_profit - entry_price

if reward / risk < 2.0:
    skip_trade()  # Not worth the risk
```

### 5. **Position Management for Maximum Profit**

#### A. Partial Profit Taking (Scaling Out)
```yaml
modifications:
  enable_partial_close: true
  partial_close_trigger_pips: 30   # Close 50% at 30 pips
  partial_close_percent: 50
  
  # Then let remaining 50% run to TP or trailing stop
```

#### B. Trailing Stop Strategy
```python
# 3-Stage Trailing Stop
def apply_intelligent_trailing(position, current_profit_pips):
    if current_profit_pips >= 50:
        # Stage 3: Tight trailing (lock in profits)
        trailing_distance = 10
    elif current_profit_pips >= 30:
        # Stage 2: Moderate trailing
        trailing_distance = 15
    elif current_profit_pips >= 20:
        # Stage 1: Wide trailing
        trailing_distance = 20
    else:
        # No trailing yet
        return
    
    new_sl = current_price - trailing_distance * pip_value
    if new_sl > position.sl:
        modify_position(sl=new_sl)
```

Configuration:
```yaml
modifications:
  enable_trailing_stop: true
  trailing_stop_pips: 15
  trailing_activation_pips: 20
  
  # Multi-stage trailing (advanced)
  use_multi_stage_trailing: true
  stage1_profit: 20
  stage1_trail: 20
  stage2_profit: 30
  stage2_trail: 15
  stage3_profit: 50
  stage3_trail: 10
```

#### C. Breakeven Protection
```yaml
modifications:
  enable_breakeven: true
  breakeven_trigger_pips: 20  # Move SL to BE when 20 pips in profit
  breakeven_offset_pips: 5    # Actually set SL at BE + 5 pips
```

### 6. **Time-Based Optimization**

#### A. Close Before Major News
```python
# Close 15 minutes before high-impact news
def check_news_schedule():
    upcoming_news = get_economic_calendar(next_hours=1)
    
    for event in upcoming_news:
        if event.impact == "HIGH":
            time_to_news = event.time - datetime.now()
            if time_to_news < timedelta(minutes=15):
                close_all_positions()
                return True
    return False
```

#### B. End-of-Day Position Management
```yaml
# Close all positions before market close
end_of_day_management:
  enabled: true
  close_time: "22:00"  # UTC
  close_all_positions: true
  
  # Or only close losing positions
  close_only_losing: false
```

### 7. **Compound Profit Strategy**

#### A. Reinvest Profits
```python
# Calculate lot size based on current balance (includes profits)
def calculate_lot_size_with_compounding():
    current_balance = mt5.account_info().balance
    risk_amount = current_balance * (risk_percent / 100)
    # Lot size automatically increases as balance grows
    return risk_based_lot_size(risk_amount)
```

#### B. Progressive Risk Increase
```python
# Increase risk after X consecutive wins
consecutive_wins = 3

if stats.consecutive_wins >= consecutive_wins:
    risk_percent = base_risk * 1.5  # 1.5% instead of 1%
else:
    risk_percent = base_risk  # Back to 1%
```

### 8. **Filtering Low-Probability Setups**

#### A. Confluence Requirements
```python
# Require multiple confirmations
def check_trade_confluence(signal):
    score = 0
    
    # 1. ML confidence
    if signal.ml_confidence > 0.7:
        score += 2
    
    # 2. Technical alignment
    if signal.technical_aligned:
        score += 2
    
    # 3. Trend alignment
    if signal.trend_aligned:
        score += 1
    
    # 4. Volume confirmation
    if signal.volume_increasing:
        score += 1
    
    # 5. Sentiment positive
    if signal.sentiment > 0.6:
        score += 1
    
    # Only trade if score >= 5
    return score >= 5
```

#### B. Avoid Choppy Markets
```python
def is_market_trending(bars, adx_threshold=25):
    """Check if market has sufficient trend strength"""
    adx = calculate_adx(bars)
    
    if adx[-1] < adx_threshold:
        return False  # Choppy market, skip
    return True
```

### 9. **Portfolio-Level Optimization**

#### A. Correlation-Based Position Sizing
```python
# Reduce risk when trading correlated pairs
pairs_open = ["EURUSD", "GBPUSD"]  # Highly correlated
correlation = 0.8

# Reduce individual risk
adjusted_risk = base_risk * (1 - correlation * 0.5)
# If correlation = 0.8: adjusted_risk = 1.0 * (1 - 0.4) = 0.6%
```

#### B. Maximum Portfolio Exposure
```yaml
global:
  max_concurrent_trades: 10
  portfolio_risk_percent: 8.0  # Total risk across all trades
  
  # If you have 5 open trades at 1% each = 5% total risk
  # System will reduce new trade risk or skip
```

### 10. **Performance Tracking & Adaptation**

#### A. Track Metrics Per Time Interval
```python
# Track profitability by hour
stats = {
    "00:00-04:00": {"trades": 10, "profit": -50, "win_rate": 0.40},
    "08:00-12:00": {"trades": 25, "profit": 320, "win_rate": 0.68},
    "13:00-17:00": {"trades": 30, "profit": 450, "win_rate": 0.73},
}

# Only trade during profitable hours
def should_trade_now():
    current_hour = datetime.now().hour
    hour_group = f"{current_hour:02d}:00-{current_hour+1:02d}:00"
    
    if stats[hour_group]["win_rate"] < 0.55:
        return False  # Skip low-performance hours
    return True
```

#### B. Adaptive Strategy Adjustment
```python
# Adjust parameters based on recent performance
def adapt_strategy():
    last_10_trades = get_recent_trades(10)
    win_rate = calculate_win_rate(last_10_trades)
    
    if win_rate < 0.50:
        # Losing streak - reduce risk and be more selective
        risk_percent *= 0.5
        ml_threshold = 0.75  # Higher threshold
        
    elif win_rate > 0.70:
        # Winning streak - slightly increase risk
        risk_percent *= 1.2
        ml_threshold = 0.65  # Lower threshold
```

## Recommended Configuration for Maximum Profit

### For Scalping (Every 5-15 minutes)
```yaml
EURUSD:
  enabled: true
  risk_percent: 1.0
  timeframe: "M5"
  fast_period: 5
  slow_period: 10
  sl_pips: 10
  tp_pips: 20
  cooldown_seconds: 300  # 5 minutes
  
  modifications:
    enable_breakeven: true
    breakeven_trigger_pips: 12
    enable_trailing_stop: true
    trailing_stop_pips: 8
    trailing_activation_pips: 15
```

### For Day Trading (Every 30-60 minutes)
```yaml
EURUSD:
  enabled: true
  risk_percent: 1.5
  timeframe: "M15"
  fast_period: 10
  slow_period: 20
  sl_pips: 20
  tp_pips: 40
  cooldown_seconds: 1800  # 30 minutes
  
  modifications:
    enable_partial_close: true
    partial_close_trigger_pips: 30
    enable_trailing_stop: true
    trailing_stop_pips: 15
```

### For Swing Trading (Every 4+ hours)
```yaml
EURUSD:
  enabled: true
  risk_percent: 2.0
  timeframe: "H4"
  fast_period: 20
  slow_period: 50
  sl_pips: 50
  tp_pips: 150
  cooldown_seconds: 14400  # 4 hours
  
  modifications:
    enable_partial_close: true
    partial_close_trigger_pips: 100
    partial_close_percent: 50
    enable_trailing_stop: true
    trailing_stop_pips: 30
```

## Expected Results

### Conservative Approach (1% risk, 1:2 R:R, 60% win rate)
- Average profit per trade: +0.2% of account
- 10 trades per day = +2% per day
- Monthly: +40% (compounded)

### Aggressive Approach (2% risk, 1:3 R:R, 55% win rate)
- Average profit per trade: +0.8% of account
- 5 trades per day = +4% per day
- Monthly: +120% (compounded)

### Realistic Sustainable Approach (1-1.5% risk, 1:2 R:R, 58% win rate)
- Average profit per trade: +0.3% of account
- 8 trades per day = +2.4% per day
- Monthly: +50-60% (compounded)

## Implementation Checklist

- [ ] Enable ML enhancement for better entry quality
- [ ] Configure dynamic SL/TP based on ATR
- [ ] Set up partial profit taking
- [ ] Enable trailing stops
- [ ] Add breakeven protection
- [ ] Filter trades by confluence score
- [ ] Track performance by time interval
- [ ] Optimize trading hours per pair
- [ ] Implement Kelly Criterion for position sizing
- [ ] Add correlation-based risk adjustment
- [ ] Set up end-of-day management
- [ ] Configure news calendar integration
- [ ] Enable compound profit reinvestment
- [ ] Monitor and adapt based on statistics

## Monitoring & Adjustment

Review every week:
1. Win rate by hour/session
2. Average R:R ratio achieved
3. Best performing currency pairs
4. Optimal cooldown periods
5. SL/TP effectiveness

Adjust configuration based on data, not emotions.
