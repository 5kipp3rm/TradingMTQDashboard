# 🤖 TradingMTQ - Automated Trading System

## What Changed?

Your system is now **fully automated**! No more manual menus - the bot monitors the market and trades automatically based on strategy signals.

## How It Works

1. **Auto-connects** to MT5 using credentials from `.env`
2. **Monitors** multiple currency pairs continuously
3. **Analyzes** price data using Moving Average strategy
4. **Executes** trades automatically when signals are detected
5. **Manages** positions with stop-loss and take-profit

## Quick Start

```bash
# 1. Make sure MT5 is running and logged in

# 2. Configure your .env file
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# 3. Run the bot
python -m src.main
```

## Current Strategy: Simple Moving Average Crossover

**How it works:**
- **BUY Signal**: When Fast MA (10 periods) crosses **above** Slow MA (20 periods)
- **SELL Signal**: When Fast MA crosses **below** Slow MA
- **Auto SL/TP**: 20 pips stop loss, 40 pips take profit

**Example:**
```
EURUSD price is rising
Fast MA = 1.0855
Slow MA = 1.0850
→ Fast MA crosses above → BUY signal generated → Trade executed automatically
```

## What the Bot Does

### Every 60 seconds:
1. ✅ Fetches latest price data for each symbol
2. ✅ Calculates moving averages
3. ✅ Detects crossover signals
4. ✅ Executes trades when signals occur
5. ✅ Monitors existing positions
6. ✅ Displays current status

### Sample Output:
```
[2025-11-29 21:30:00] Iteration #5
----------------------------------------------------------------------
  EURUSD: 🟢 BUY @ 1.08550
           Bullish crossover (Fast MA 1.08555 > Slow MA 1.08540)
           ✓ ORDER PLACED: Ticket #123456789
           SL: 1.08350 | TP: 1.08950

  GBPUSD: ⚪ HOLD @ 1.26750
           No crossover

  USDJPY: 🔴 SELL @ 149.850
           Bearish crossover (Fast MA 149.840 < Slow MA 149.860)
           ✓ ORDER PLACED: Ticket #123456790
           SL: 150.050 | TP: 149.450

📊 Open Positions: 2
   EURUSD: BUY 0.01 lots | P&L: $2.50 | Pips: 2.5
   USDJPY: SELL 0.01 lots | P&L: -$1.20 | Pips: -1.2
   Total P&L: $1.30
💰 Balance: $10,000.00 | Equity: $10,001.30

⏳ Waiting 60s until next check...
```

## Configuration

### Edit Strategy Parameters

Open `src/main.py` and modify:

```python
strategy = SimpleMovingAverageStrategy(params={
    'fast_period': 10,    # Fast MA period
    'slow_period': 20,    # Slow MA period
    'sl_pips': 20,        # Stop loss in pips
    'tp_pips': 40         # Take profit in pips
})
```

### Edit Trading Symbols

```python
symbols = [
    'EURUSD',
    'GBPUSD',
    'USDJPY',
    'AUDUSD'  # Add or remove symbols
]
```

### Edit Risk Settings

In `config/mt5_config.yaml`:
```yaml
risk:
  default_lot_size: 0.01      # Volume per trade
  max_positions: 3            # Max concurrent positions
  max_daily_loss: 100.0       # Max loss per day (future)
```

## Safety Features

✅ **Max Positions Limit** - Won't open more than configured max
✅ **One Position Per Symbol** - Prevents duplicate positions
✅ **Auto Stop Loss** - Every trade has SL
✅ **Auto Take Profit** - Every trade has TP
✅ **Connection Monitoring** - Checks connection before trading
✅ **Error Handling** - Graceful error recovery

## Stopping the Bot

Press `Ctrl+C` to stop - the bot will:
1. Stop monitoring
2. **Keep existing positions open** (they have SL/TP)
3. Disconnect from MT5
4. Exit cleanly

## Next Steps (Future Enhancements)

You can now add:
- ✨ More sophisticated strategies (RSI, MACD, Bollinger Bands)
- ✨ Machine learning models (Phase 3)
- ✨ Sentiment analysis from news (Phase 4)
- ✨ Multiple strategies running simultaneously
- ✨ Backtesting before live trading
- ✨ Web dashboard for monitoring

## Files Structure

```
src/
├── main.py                    # New automated entry point
├── bot.py                     # Trading bot engine
├── strategies/
│   ├── base.py               # Strategy interface
│   └── simple_ma.py          # Moving Average strategy
├── connectors/               # MT5 connection (unchanged)
├── trading/                  # Trading controller (unchanged)
└── utils/                    # Utilities (unchanged)
```

## Old Menu-Based System

The old interactive menu is saved in `src/main_old.py` if you need it for reference.

---

**Ready to trade!** 🚀

```bash
python -m src.main
```
