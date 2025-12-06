# 🚀 Ready to Run - Real Trading Scripts

All scripts are ready to use! Update your MT5 credentials and run.

## 📋 Quick Reference

| Script | Purpose | Requires Credentials | Risk Level |
|--------|---------|---------------------|------------|
| `test_connection.py` | Test MT5 connection | ✓ | ⚪ None - No trading |
| `preflight_check.py` | System readiness check | ✗ | ⚪ None - No connection |
| `quick_start.py` | Simple live trading | ✓ | 🟡 Live trading |
| `live_trading.py` | Full-featured bot | ✓ | 🟡 Live trading |
| `manage_positions.py` | View/close positions | ✓ | 🟠 Position management |

## 🎯 Recommended Workflow

### 1️⃣ First Time - Test Connection
```bash
python examples/test_connection.py
```
**What it does:**
- Verifies MT5 connection works
- Shows account information
- Tests symbol data retrieval
- Displays any open positions
- **NO TRADING** - 100% safe

**You'll be asked for:**
- MT5 Login
- MT5 Password  
- MT5 Server
- Test symbol (optional)

**Output:**
```
MT5 CONNECTION TEST
================================================================================

MT5 Login: 12345678
MT5 Password: ********
MT5 Server: Broker-Demo

Connecting to Broker-Demo...

✓ CONNECTION SUCCESSFUL

ACCOUNT INFORMATION
--------------------------------------------------------------------------------
Login:          12345678
Server:         Broker-Demo
Name:           Your Name
Balance:        $10,000.00
Equity:         $10,000.00
Leverage:       1:100
...
```

---

### 2️⃣ Check System - Pre-flight
```bash
python examples/preflight_check.py
```
**What it does:**
- Verifies all Python packages installed
- Tests MT5 terminal connection
- Validates project imports
- Checks error descriptions working
- Tests strategy generation
- **NO CREDENTIALS NEEDED**

**Output:**
```
PRE-FLIGHT CHECK - LIVE TRADING READINESS
================================================================================

✓ MetaTrader5 module installed (version: 5.0.5430)
✓ NumPy and Pandas installed
✓ Project modules import successfully
✓ Error descriptions working
✓ MT5 terminal detected
✓ Strategy generates signals correctly
✓ AccountUtils available with risk management functions
⚠ Live trading script exists but credentials NOT updated

RESULTS: 7/8 checks passed
================================================================================

🎉 SYSTEM READY FOR LIVE TRADING!
```

---

### 3️⃣ Quick Test - Simple Trading
```bash
python examples/quick_start.py
```
**What it does:**
- Prompts for credentials (no file editing needed)
- Quick configuration (symbol, risk %)
- Starts trading immediately
- Simple MA crossover strategy
- Risk-based position sizing

**⚠️ WARNING: This executes REAL trades!**

**Interactive prompts:**
```
Enter MT5 Login: 12345678
Enter MT5 Password: ********
Enter MT5 Server: Broker-Demo
Enter Symbol (default: EURUSD): EURUSD
Risk % per trade (default: 1.0): 1.0

Account: 12345678
Balance: $10,000.00

Strategy: Simple MA Crossover
Risk per trade: 1.0%

WARNING: This will execute REAL trades!
================================================================================

Type 'GO' to start trading: GO

[14:30:15] EURUSD @ 1.08525 - Signal: HOLD (0%)
[14:30:45] EURUSD @ 1.08530 - Signal: BUY (45%)
  📊 Executing BUY - 0.15 lots
     Entry: 1.08530, SL: 1.08330, TP: 1.08930
  ✓ Order #123456789 executed @ 1.08530
```

---

### 4️⃣ Full Bot - Advanced Trading
```bash
# First, edit the file to add credentials
# Update lines 25-27 in examples/live_trading.py

python examples/live_trading.py
```

**What it does:**
- Full-featured automated trading bot
- Configurable everything (strategy params, risk, hours, etc.)
- Trading hours restriction
- Maximum runtime limit
- Position monitoring
- Detailed logging

**Configuration (in file):**
```python
# MT5 Connection
MT5_LOGIN = 12345678  # UPDATE THIS
MT5_PASSWORD = "your_password"  # UPDATE THIS
MT5_SERVER = "YourBroker-Demo"  # UPDATE THIS

# Trading Parameters
SYMBOL = "EURUSD"
TIMEFRAME = "M5"
RISK_PERCENT = 1.0
MAX_POSITIONS = 1

# Strategy Parameters
STRATEGY_PARAMS = {
    'fast_period': 10,
    'slow_period': 20,
    'sl_pips': 20,
    'tp_pips': 40,
}

# Trading Hours
TRADING_START_HOUR = 0
TRADING_END_HOUR = 23
CHECK_INTERVAL = 30
MAX_RUNTIME_HOURS = 24
```

**Features:**
- ✅ Risk-based position sizing
- ✅ Margin verification
- ✅ Trading hours control
- ✅ Max positions limit
- ✅ Error descriptions
- ✅ Position monitoring
- ✅ Graceful shutdown

---

### 5️⃣ Manage Positions - Quick Control
```bash
# Edit file to add credentials first
# Update lines 11-13 in examples/manage_positions.py

python examples/manage_positions.py
```

**What it does:**
- View all open positions
- Close individual positions
- Close all positions at once
- Real-time P/L display

**Interface:**
```
POSITION MANAGER
================================================================================

Account: 12345678 | Balance: $10,050.00 | Equity: $10,055.50 | Profit: $5.50

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

Choice:
```

---

## 🔧 Configuration Files

All scripts need these credentials:

```python
MT5_LOGIN = 12345678  # Your MT5 account number
MT5_PASSWORD = "your_password"  # Your MT5 password
MT5_SERVER = "YourBroker-Demo"  # Your broker server name
```

### How to find your Server Name:

1. Open MT5
2. File → Open Account
3. Look at server list
4. Common formats:
   - `Broker-Demo` (demo account)
   - `Broker-Live` (live account)
   - `Broker-Server1` (specific server)

**⚠️ Server name is CASE-SENSITIVE!**

---

## 📊 Which Script to Use?

### Just want to test connection?
👉 `test_connection.py` - Safe, no trading

### Ready to trade right now?
👉 `quick_start.py` - Interactive, fast setup

### Want full control and monitoring?
👉 `live_trading.py` - Full bot with all features

### Need to close positions quickly?
👉 `manage_positions.py` - Position management

### Not sure if system is ready?
👉 `preflight_check.py` - System validation

---

## 🛡️ Safety Tips

### ⚠️ ALWAYS Start with Demo
- Use demo account first
- Test for at least 1 week
- Verify strategy performance
- Only then consider live

### 💰 Risk Management
- Start with 1% risk per trade
- Never exceed 2% per trade
- Limit total exposure to 6% of account
- Always use stop losses

### 👁️ Monitoring
- Watch first 10 trades closely
- Keep a trading journal
- Review performance daily
- Don't leave bot unattended initially

### 🛑 Stop Rules
- Set max daily loss limit
- Set max drawdown tolerance
- Don't trade during news events
- Stop if win rate < 40%

---

## 📖 Documentation

- `LIVE_TRADING_GUIDE.md` - Complete guide to live trading
- `INTEGRATION_COMPLETE.md` - All features explained
- `QUICK_REFERENCE.md` - Code snippets and examples
- `README.md` - Project overview

---

## 🆘 Troubleshooting

### Connection fails?
```bash
python examples/test_connection.py
```
Will help diagnose the issue

### System not ready?
```bash
python examples/preflight_check.py
```
Shows what needs to be fixed

### Want to test without risk?
```bash
python examples/features_demo_no_connection.py
```
Shows all features without connecting

---

## 🚀 Quick Start Checklist

- [ ] Run `preflight_check.py` - Verify system ready
- [ ] Run `test_connection.py` - Verify MT5 connection works
- [ ] Read `LIVE_TRADING_GUIDE.md` - Understand the system
- [ ] Choose your script (`quick_start.py` recommended)
- [ ] Update credentials in the script
- [ ] **Start with DEMO account**
- [ ] **Use low risk % (1.0%)**
- [ ] Run the script
- [ ] Monitor closely for first day
- [ ] Review performance after 1 week

---

## ⚡ Super Quick Start (3 steps)

1. **Test connection:**
   ```bash
   python examples/test_connection.py
   ```

2. **If successful, start trading:**
   ```bash
   python examples/quick_start.py
   ```
   
3. **Monitor and manage:**
   ```bash
   python examples/manage_positions.py
   ```

That's it! 🎉

---

## 📞 Need Help?

1. Review error messages - they're descriptive
2. Check `LIVE_TRADING_GUIDE.md` troubleshooting section
3. Verify MT5 is running
4. Ensure credentials are correct
5. Test with different symbols
6. Check account has sufficient margin

---

**Happy Trading! 📈💰**

Remember: Past performance doesn't guarantee future results. Trade responsibly!
