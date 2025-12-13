# Market Data Issues - Resolution Guide

## Issue: "No bars for EURUSD/USDJPY" Warnings

### Root Cause
You're seeing repeated warnings like:
```
⚠️ WARNING [config_bot] No bars for EURUSD M5
⚠️ WARNING [config_bot] No bars for USDJPY M15
```

**This is expected behavior when the Forex market is closed.**

### Current Status (As of Dec 13, 2025)
```
Current Time: Saturday, December 13, 2025 at 07:03 AM
Market Status: Market closed - Saturday (no trading)
Market Open: False
Next Open: Sunday at 5:00 PM EST
```

## Forex Market Hours

The Forex market operates on a **24/5 schedule**:
- **Opens**: Sunday 5:00 PM EST
- **Closes**: Friday 5:00 PM EST
- **Closed**: Friday 5 PM → Sunday 5 PM (weekend)

## What Was Fixed

### 1. Reduced Warning Noise ✅
The bot now:
- Shows warning only on **first failure**
- Shows detailed help after **20 consecutive failures**
- Eliminates spam during market closures

**Before:**
```
15:32:40 ⚠️ WARNING [config_bot] No bars for EURUSD M5
15:33:10 ⚠️ WARNING [config_bot] No bars for EURUSD M5
15:33:40 ⚠️ WARNING [config_bot] No bars for EURUSD M5
... (repeated every 30 seconds)
```

**After:**
```
15:32:40 ⚠️ WARNING [config_bot] No bars for EURUSD M5 - Market may be closed or data not available
... (silent for cycles 2-19) ...
15:42:40 ⚠️ WARNING [config_bot] EURUSD M5 - Still no data after 20 attempts. Check:
  • Forex market hours (Sunday 5PM - Friday 5PM EST)
  • MT5 connection and symbol availability
  • Timeframe matches broker's available data
```

### 2. Market Hours Detection ✅
Added automatic market hours checking at startup:
```
================================================================================
⚠️  Market closed - Saturday (no trading)
   Next market open: Sunday at 5:00 PM EST
   Bot will continue running but may not receive new data
   Existing positions will be monitored if any
================================================================================
```

### 3. Utility Tool Created ✅
New file: `src/utils/market_hours.py`

**Check market status:**
```bash
cd /z/DevelopsHome/TradingMTQ
python src/utils/market_hours.py
```

**Output:**
```
Status: Market closed - Saturday (no trading)
Market Open: False
Next Open: Sunday at 5:00 PM EST
```

## What To Do

### Option 1: Wait for Market Open ⏰
The simplest approach - wait until:
```
Sunday, December 14, 2025 at 5:00 PM EST
```
Then restart the bot. It will have fresh market data.

### Option 2: Keep Bot Running 🤖
The bot can stay running during market closure:
- ✅ Monitors existing positions (if any)
- ✅ Checks for new data every cycle
- ✅ Automatically resumes trading when market opens
- ❌ Won't create new trades (no data = no signals)

### Option 3: Use Demo with Simulated Data 📊
Some MT5 demo servers provide limited weekend data. Check your broker's demo account features.

## Troubleshooting

### If warnings persist AFTER market opens:

1. **Check MT5 Connection:**
   ```python
   import MetaTrader5 as mt5
   if not mt5.initialize():
       print("MT5 initialization failed")
   else:
       print(f"Connected: {mt5.account_info()}")
   ```

2. **Verify Symbol Availability:**
   ```python
   import MetaTrader5 as mt5
   mt5.initialize()
   symbols = mt5.symbols_get("*USD*")
   for s in symbols:
       print(f"{s.name}: {s.visible}")
   ```

3. **Check Timeframe Data:**
   ```python
   import MetaTrader5 as mt5
   mt5.initialize()
   bars = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M5, 0, 100)
   print(f"Available bars: {len(bars) if bars is not None else 0}")
   ```

## Files Modified

1. **src/connectors/mt5_connector.py**
   - Added `_no_bars_count` tracking
   - Reduced warning frequency (1st warning, then every 20 cycles)
   - Added helpful diagnostic messages

2. **main.py**
   - Added market hours check at startup
   - Shows next market open time if closed

3. **src/utils/market_hours.py** (NEW)
   - Forex market hours detection
   - EST timezone handling
   - Next-open-time calculation

## CLI Commands Reference

All commands work the same way:

```bash
# Standard trading (will show market closed warning if weekend)
tradingmtq trade

# With ML/LLM control
tradingmtq trade --disable-ml
tradingmtq trade --disable-llm

# Aggressive mode
tradingmtq trade --aggressive

# Check market status
python src/utils/market_hours.py

# View help
tradingmtq --help
tradingmtq trade --help
```

## Summary

✅ **Bot is working correctly**
✅ **Warnings are expected during market closure**
✅ **Reduced noise from repetitive warnings**
✅ **Added market hours detection**
✅ **Created diagnostic utility**

**Next Steps:**
- Wait for Sunday 5 PM EST market open
- Or keep bot running to auto-resume when data available
- Use `python src/utils/market_hours.py` to check market status anytime
