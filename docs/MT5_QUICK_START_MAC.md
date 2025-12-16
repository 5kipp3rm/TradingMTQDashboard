# MT5 Quick Start Guide for Mac

This guide will help you connect your MT5 account on Mac to TradingMTQ using the bridge solution.

## Overview

TradingMTQ connects to MT5 via an HTTP bridge using an MQL5 Expert Advisor. This works on Mac even though the MetaTrader5 Python package doesn't support macOS.

**Architecture:**
```
Python (TradingMTQ) <--HTTP--> MQL5 EA <--> MT5 Terminal <--> Broker
```

## Prerequisites

- ✅ MT5 installed on your Mac
- ✅ MT5 connected to your broker
- ✅ TradingMTQ installed
- ✅ Python requests package (`pip install requests`)

## Step 1: Test Socket Support (Optional but Recommended)

First, let's verify that MT5 supports sockets in your Wine environment:

1. Open MetaTrader 5
2. Press `⌘+F4` (or Tools → MetaQuotes Language Editor)
3. In MetaEditor Navigator panel:
   - Expand "Experts"
   - You should see `mt5_bridge_test.mq5` (already copied)
   - Double-click to open it
4. Press `⌘+F7` (or Compile → Compile)
5. Check bottom: "0 error(s), 0 warning(s)" ✅
6. Go back to MT5 Terminal
7. Open any chart (e.g., EURUSD)
8. Press `⌘+N` to open Navigator
9. Expand "Expert Advisors"
10. Drag `mt5_bridge_test` onto the chart

**Settings dialog:**
- **Common Tab:**
  - ✅ Allow DLL imports (check this!)
  - ✅ Allow external experts imports
- Click **OK**

**Enable AutoTrading:**
- In MT5 toolbar, click "Algo Trading" button
- Button should turn GREEN

**Check Results:**
Look at the "Experts" tab (bottom of MT5). You should see:

✅ **If sockets work:**
```
=== MT5 Bridge Socket Test ===
Testing if sockets work in Wine environment...
✅ Socket created successfully!
✅ Socket bound to port 8080
✅ Socket listening on port 8080
🎉 SUCCESS! Sockets work in this MT5 installation!
```

❌ **If sockets DON'T work:**
```
=== MT5 Bridge Socket Test ===
❌ SOCKET CREATION FAILED!
This means Wine MT5 does NOT support sockets.
```

**If sockets don't work:** Stop here and contact support. You may need to use a Windows VM or a different approach.

## Step 2: Copy Full Bridge EA

The test EA has been placed in your MT5 Experts folder:
```
~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/mt5_bridge_test.mq5
```

For production use, you'll need the full bridge EA (coming soon in next version).

## Step 3: Configure MT5 Account in TradingMTQ

1. Open TradingMTQ UI: http://localhost:8000
2. Go to "Accounts" page
3. Find your MT5 account
4. Make sure `platform_type` is set to "MT5"
5. Save the account

## Step 4: Test Connection

### From Terminal:

```bash
# Test if bridge is accessible
curl http://localhost:8080/ping

# Expected output:
# {"success": true, "message": "pong"}
```

### From TradingMTQ UI:

1. Go to Accounts page
2. Click "Connect" button on your MT5 account
3. Status should change to "Connected" ✅

## Troubleshooting

### Socket Test Fails

**Problem:** mt5_bridge_test reports socket creation failed

**Cause:** Wine MT5 doesn't support sockets (similar to MT4 limitation)

**Solutions:**
1. Use Windows VM (Parallels, VMware, VirtualBox) - **RECOMMENDED**
2. Use remote Windows server with MT5
3. Check if broker offers Mac-compatible API

### EA Not Starting

**Problem:** EA shows error or doesn't initialize

**Solutions:**
1. Verify "Allow DLL imports" is checked in EA settings
2. Check "Algo Trading" button is GREEN
3. Ensure MT5 is connected to broker
4. Check Experts tab for specific error messages

### Connection Refused from Python

**Problem:** `curl http://localhost:8080` returns "Connection refused"

**Solutions:**
1. Verify EA is running (check Experts tab for "Socket listening")
2. Check port 8080 isn't used by another app:
   ```bash
   lsof -i :8080
   ```
3. Try different port (update in EA settings and Python connector)

### Account Mismatch Warning

**Problem:** "Account mismatch: Expected #123, but MT5 is logged in as #456"

**Solution:** Update the account number in TradingMTQ database to match the actual MT5 login

## Next Steps

Once connected, you can:
- ✅ View real-time account balance and equity
- ✅ Monitor open positions
- ✅ Execute trades via UI or Python API
- ✅ Access historical data
- ✅ Run automated trading strategies

## Comparison: MT4 vs MT5 on Mac

| Feature | MT4 (Wine) | MT5 (Wine) |
|---------|------------|------------|
| Socket Support | ❌ No | ✅ Maybe* |
| Bridge Solution | ❌ Doesn't work | ✅ Should work* |
| Python Package | ❌ No macOS support | ❌ No macOS support |
| Recommendation | Use Windows VM | Try bridge first |

\* Test with `mt5_bridge_test.mq5` to confirm

## Support

If you encounter issues:
1. Run `mt5_bridge_test.mq5` and share Experts tab output
2. Check TradingMTQ logs: `logs/trading_YYYYMMDD.log`
3. Test with curl before Python connection
4. See full guide: docs/MT5_INTEGRATION_GUIDE.md (coming soon)

## Summary

✅ **What You Did:**
- Tested MT5 socket support with test EA
- Confirmed Wine MT5 can (or cannot) run HTTP bridge
- Configured MT5 account in TradingMTQ

✅ **What Works (if sockets supported):**
- HTTP bridge from Python to MT5
- Real-time account data
- Position management
- Order execution

🎉 **You're ready to trade with MT5 on your Mac!** (if socket test passed)
