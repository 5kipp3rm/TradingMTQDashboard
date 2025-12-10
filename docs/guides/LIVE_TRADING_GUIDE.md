# Live Trading Guide

This guide explains how to run **real trading** with the TradingMTQ system.

## ⚠️ IMPORTANT WARNINGS

1. **START WITH DEMO ACCOUNT** - Always test on demo first
2. **REAL MONEY AT RISK** - Live trading risks your capital
3. **MONITOR ACTIVELY** - Don't leave the bot unattended initially
4. **START SMALL** - Use low risk % and position limits
5. **TEST THOROUGHLY** - Backtest and paper trade extensively first

## Available Scripts

### 1. `live_trading.py` - Automated Trading Bot

**Features:**
- Connects to MT5 in real-time
- Monitors market continuously
- Generates signals using strategy
- Executes trades automatically
- Risk-based position sizing
- Manages multiple positions
- Trading hours control
- Maximum runtime limit

**Before Running:**

1. **Update Credentials** (lines 25-27):
```python
MT5_LOGIN = 12345678  # Your actual MT5 login
MT5_PASSWORD = "your_password"  # Your actual password
MT5_SERVER = "YourBroker-Demo"  # Your broker server name
```

2. **Configure Trading** (lines 30-48):
```python
SYMBOL = "EURUSD"           # Symbol to trade
TIMEFRAME = "M5"            # Timeframe (M1, M5, M15, H1, etc.)
RISK_PERCENT = 1.0          # Risk per trade (1% recommended)
MAX_POSITIONS = 1           # Max concurrent positions
USE_RISK_MANAGEMENT = True  # Use AccountUtils for sizing
```

3. **Set Strategy Parameters** (lines 38-43):
```python
STRATEGY_PARAMS = {
    'fast_period': 10,   # Fast MA period
    'slow_period': 20,   # Slow MA period
    'sl_pips': 20,       # Stop loss
    'tp_pips': 40,       # Take profit
}
```

4. **Configure Runtime** (lines 46-48):
```python
TRADING_START_HOUR = 0    # Start hour (24h format)
TRADING_END_HOUR = 23     # End hour
CHECK_INTERVAL = 30       # Check every 30 seconds
MAX_RUNTIME_HOURS = 24    # Auto-stop after 24 hours
```

**Run:**
```bash
python examples/live_trading.py
```

**Expected Flow:**
1. Connects to MT5 and shows account info
2. Verifies symbol is available
3. Asks for confirmation: Type 'START' to begin
4. Starts monitoring loop
5. Checks market every 30 seconds
6. When signal detected:
   - Calculates position size (risk-based)
   - Verifies margin requirements
   - Executes trade
   - Reports result
7. Monitors open positions
8. Press Ctrl+C to stop

**Output Example:**
```
================================================================================
  LIVE TRADING BOT - INITIALIZING
================================================================================

Starting at: 2025-12-01 14:30:00

Connecting to MT5...
  Server: Broker-Demo
  Login: 12345678
✓ Connected to MT5

Account Information:
  Balance: $10000.00
  Equity: $10000.00
  Free Margin: $10000.00
  Leverage: 1:100

✓ Strategy: Simple MA Crossover
  Parameters: {'fast_period': 10, 'slow_period': 20, 'sl_pips': 20, 'tp_pips': 40}

✓ Symbol: EURUSD
  Bid: 1.08520
  Ask: 1.08522
  Spread: 2 points

================================================================================
  STARTING LIVE TRADING
================================================================================

Symbol: EURUSD
Timeframe: M5
Check Interval: 30 seconds
Risk per Trade: 1.0%
Max Positions: 1

⚠ WARNING: This will execute REAL trades on your account!

Type 'START' to begin trading: START

[2025-12-01 14:30:45] Checking market...
  Price: 1.08522
  Signal: HOLD (confidence: 0.0%)
  Reason: No crossover
  Open Positions: 0

[2025-12-01 14:31:15] Checking market...
  Price: 1.08525
  Signal: BUY (confidence: 42.3%)
  Reason: Bullish crossover (Fast MA 1.08515 > Slow MA 1.08510)
  Open Positions: 0

────────────────────────────────────────────────────────────────────────────────
EXECUTING SIGNAL:
  Type: BUY
  Price: 1.08525
  Volume: 0.15 lots
  Stop Loss: 1.08325
  Take Profit: 1.08925
  Reason: Bullish crossover (Fast MA 1.08515 > Slow MA 1.08510)
  Confidence: 42.3%
  Risk: $100.00 (1% of balance)
✓ ORDER EXECUTED
  Ticket: #123456789
  Fill Price: 1.08525

Current Positions (1):
  #123456789 - BUY 0.15 @ 1.08525
    SL: 1.08325, TP: 1.08925, P/L: $5.50
  Total P/L: $5.50
```

### 2. `manage_positions.py` - Position Manager

Quick tool to view and close positions.

**Update credentials** (lines 11-13):
```python
MT5_LOGIN = 12345678
MT5_PASSWORD = "your_password"
MT5_SERVER = "YourBroker-Demo"
```

**Run:**
```bash
python examples/manage_positions.py
```

**Features:**
- View all open positions
- Close specific position by number
- Close all positions at once
- Real-time P/L display

**Output Example:**
```
================================================================================
  POSITION MANAGER
================================================================================
✓ Connected to MT5

Account: 12345678 | Balance: $10050.00 | Equity: $10055.50 | Profit: $5.50

Open Positions (2):
====================================================================================================
#    Ticket       Symbol     Type   Volume   Open       Current    P/L         
----------------------------------------------------------------------------------------------------
1    123456789    EURUSD     BUY    0.15     1.08525    1.08575    $7.50       
2    123456790    GBPUSD     SELL   0.10     1.26430    1.26410    $2.50       
----------------------------------------------------------------------------------------------------
Total P/L:                                                         $10.00
====================================================================================================

Options:
  1-2: Close specific position
  A: Close ALL positions
  R: Refresh
  Q: Quit

Choice: 1
✓ Position #123456789 closed
  Close Price: 1.08575
```

## Risk Management

The bot uses professional risk management from `AccountUtils`:

### Position Sizing Formula

```python
lot_size = AccountUtils.risk_based_lot_size(
    symbol=symbol,
    order_type=order_type,
    entry_price=entry_price,
    stop_loss=stop_loss,
    risk_percent=RISK_PERCENT
)
```

**How it works:**
- If balance = $10,000 and risk = 1%
- Risk amount = $100
- If stop loss = 20 pips
- Calculates lot size so 20 pip loss = exactly $100

### Safety Limits

1. **Max Positions** - Limits concurrent trades
2. **Risk Percent** - Limits per-trade risk
3. **Trading Hours** - Only trade during specified hours
4. **Max Runtime** - Auto-stop after X hours
5. **Margin Check** - Verifies sufficient margin before trading

## Monitoring

### What to Watch

1. **Account Balance** - Is it growing or shrinking?
2. **Win Rate** - % of profitable trades
3. **Risk/Reward** - Are wins bigger than losses?
4. **Drawdown** - Maximum loss from peak
5. **Open Positions** - How many trades active?

### Logs

The bot prints detailed logs:
- Every market check (every 30s)
- Signal generation
- Order execution
- Position updates
- Errors with descriptions

### Stop the Bot

Press `Ctrl+C` to stop gracefully:
- Shows final positions
- Displays account status
- Disconnects from MT5

**Note:** Open positions remain open after stopping!

## Strategies

### Current: Simple MA Crossover

**Logic:**
- BUY when fast MA crosses above slow MA (bullish)
- SELL when fast MA crosses below slow MA (bearish)

**Parameters:**
- `fast_period`: Fast MA period (default 10)
- `slow_period`: Slow MA period (default 20)
- `sl_pips`: Stop loss in pips
- `tp_pips`: Take profit in pips

### Adding Your Strategy

To use a different strategy:

1. **Choose strategy:**
```python
from src.strategies import RSIStrategy  # Or your custom strategy
```

2. **Initialize it:**
```python
self.strategy = RSIStrategy(
    symbol=SYMBOL,
    timeframe=TIMEFRAME,
    rsi_period=14,
    oversold=30,
    overbought=70
)
```

3. **Update analyze call** (should work as-is if strategy follows base class)

## Best Practices

### Before Live Trading

1. ✅ **Backtest** - Run on historical data
2. ✅ **Paper Trade** - Test on demo for 1+ weeks
3. ✅ **Review Results** - Analyze performance metrics
4. ✅ **Start Small** - Use minimum lot size / low risk %
5. ✅ **Monitor Closely** - Watch first few trades live

### During Live Trading

1. 📊 **Track Performance** - Keep trading journal
2. 👁️ **Monitor Regularly** - Check bot status
3. 🛑 **Have Stop Rules** - Max daily loss, max drawdown
4. 📝 **Review Daily** - Analyze trades each day
5. 🔧 **Adjust Gradually** - Don't change parameters drastically

### Risk Management Rules

1. **Never risk more than 2% per trade**
2. **Limit total exposure to 6% of account**
3. **Use stop losses on every trade**
4. **Don't overtrade - quality over quantity**
5. **Review performance weekly**

## Troubleshooting

### Connection Issues

**Problem:** Failed to connect to MT5

**Solutions:**
- Verify MT5 is running
- Check credentials are correct
- Verify server name (case-sensitive)
- Check internet connection
- Try restarting MT5

### Symbol Not Available

**Problem:** Symbol EURUSD not available

**Solutions:**
- Open MT5 Market Watch
- Right-click → Show All
- Find symbol and enable it
- Restart the bot

### Insufficient Margin

**Problem:** Order failed - Not enough margin

**Solutions:**
- Reduce `RISK_PERCENT`
- Reduce `MAX_POSITIONS`
- Increase account balance
- Close existing positions

### Invalid Volume

**Problem:** Invalid volume in request

**Solutions:**
- Check symbol's volume_min and volume_max
- Verify volume_step
- Account may not support that lot size

## Performance Optimization

### Finding Good Parameters

Use the backtesting system to test different parameters:

```python
from src.backtesting import BacktestEngine

engine = BacktestEngine()

# Test different MA periods
for fast in [5, 10, 15]:
    for slow in [20, 30, 50]:
        strategy = SimpleMovingAverageStrategy({
            'fast_period': fast,
            'slow_period': slow,
            'sl_pips': 20,
            'tp_pips': 40
        })
        
        result = engine.run_backtest(
            strategy=strategy,
            symbol="EURUSD",
            timeframe="M5",
            start_date=start,
            end_date=end
        )
        
        print(f"Fast {fast} / Slow {slow}: "
              f"Sharpe: {result.sharpe_ratio:.2f}, "
              f"Win Rate: {result.win_rate:.1%}")
```

### Timeframe Selection

- **M1** - Very active, many trades, needs tight risk control
- **M5** - Active, good for day trading
- **M15** - Moderate, fewer but higher quality signals
- **H1** - Slower, swing trading style
- **H4/D1** - Position trading, very few trades

### Symbol Selection

**Good for beginners:**
- EUR/USD - Most liquid, tight spreads
- GBP/USD - Good volatility
- USD/JPY - Stable trends

**Avoid initially:**
- Exotic pairs - Wide spreads, low liquidity
- Cryptocurrencies - High volatility
- Indices during low volume hours

## Next Steps

1. **Update credentials in both scripts**
2. **Run on demo account first**
3. **Monitor for at least 1 week**
4. **Analyze results**
5. **Optimize parameters if needed**
6. **Consider going live with small amount**
7. **Scale up gradually as confidence grows**

## Support Files

- `enhanced_features_demo.py` - Test features without trading
- `features_demo_no_connection.py` - Documentation examples
- `INTEGRATION_COMPLETE.md` - Feature documentation
- `QUICK_REFERENCE.md` - Code snippets

## Questions?

Review the documentation:
- Main README.md - Project overview
- PHASE1_STATUS.md - Core functionality
- INTEGRATION_COMPLETE.md - Enhanced features

Happy Trading! 🚀📈
