# 🚀 How to Use TradingMTQ

## Quick Start - 3 Steps

### 1. Run from Root
```bash
python run.py
```

That's it! The system will:
- ✅ Check all dependencies
- ✅ Verify MT5 terminal is running
- ✅ Test project modules
- ✅ Prompt for credentials
- ✅ Test MT5 connection
- ✅ Show you a menu of options

### 2. Choose Your Mode

When you run `python run.py`, you'll see:

```
SELECT TRADING MODE
================================================================================

1. Quick Start Trading (Interactive)
   - Prompts for settings
   - Simple MA Crossover strategy
   - Risk-based position sizing
   - Recommended for beginners

2. Full Automated Bot
   - Comprehensive features
   - Multiple strategy options
   - Advanced risk management
   - Market analysis

3. Position Manager
   - View open positions
   - Close positions
   - No trading

4. Test Connection Only
   - Verify MT5 connection
   - Display account info
   - Safe - no trading

5. Exit

Choice (1-5):
```

### 3. Follow the Prompts

The system will guide you through everything!

## What Happens When You Run

### Pre-Flight Checks ✈️

```
🚀 PRE-FLIGHT CHECKS
================================================================================

🔍 Checking dependencies...
  ✓ MetaTrader5
  ✓ NumPy
  ✓ Pandas

🔍 Checking MT5 terminal...
  ✓ MT5 terminal found
    Path: C:\Program Files\MetaTrader 5\terminal64.exe
    Build: 3770

🔍 Checking project modules...
  ✓ MT5 Connector
  ✓ Trading Strategies
  ✓ Account Utilities

✅ All checks passed!
```

### Credential Input 🔐

```
🔐 MT5 Credentials
--------------------------------------------------------------------------------

  Enter your MT5 credentials:
  Login: 12345678
  Password: ********
  Server: Broker-Demo
```

**Or** set environment variables:
```bash
export MT5_LOGIN=12345678
export MT5_PASSWORD=your_password
export MT5_SERVER=Broker-Demo
```

### Connection Test 🔌

```
🔌 Testing MT5 connection...
  ✓ Connection successful!

  Account Information:
    Login: 12345678
    Server: Broker-Demo
    Balance: $10,000.00
    Equity: $10,000.00
    Leverage: 1:100
```

### Trading Modes

#### Mode 1: Quick Start Trading (Recommended)

Interactive and simple:

```bash
python run.py
# Choose option 1

Symbol (default: EURUSD): EURUSD
Risk % per trade (default: 1.0): 1.0

Symbol: EURUSD
Bid: 1.08520, Ask: 1.08522

Strategy: Simple MA Crossover
Risk: 1.0%

WARNING: This will execute REAL trades!
================================================================================

Type 'GO' to start: GO

TRADING ACTIVE - Press Ctrl+C to stop
================================================================================

[14:30:15] EURUSD @ 1.08525 - Signal: HOLD (0%)
[14:30:45] EURUSD @ 1.08530 - Signal: BUY (45%)
  📊 Executing BUY - 0.15 lots
  ✓ Order #123456789 executed @ 1.08530
```

**Features:**
- Interactive prompts (no file editing)
- Quick configuration
- Risk-based position sizing
- Real-time monitoring

#### Mode 2: Full Automated Bot

For advanced users:

```bash
python run.py
# Choose option 2
# Then edit examples/live_trading.py with your settings
python examples/live_trading.py
```

**Features:**
- All advanced features
- Configurable parameters
- Trading hours control
- Position limits
- Comprehensive logging

#### Mode 3: Position Manager

View and manage open positions:

```bash
python run.py
# Choose option 3

Open Positions (2):
====================================================================================================
#    Ticket       Symbol     Type   Volume   Open       Current    P/L         
----------------------------------------------------------------------------------------------------
1    123456789    EURUSD     BUY    0.15     1.08525    1.08575    $7.50       
2    123456790    GBPUSD     SELL   0.10     1.26430    1.26410    $2.50       
----------------------------------------------------------------------------------------------------
Total P/L:                                                         $10.00

Options:
  1-2: Close specific position
  A: Close ALL positions
  R: Refresh
  Q: Quit
```

#### Mode 4: Test Connection Only

Safe testing (no trading):

```bash
python run.py
# Choose option 4

✓ Connection test already completed above!
```

## Alternative Ways to Run

### Direct Scripts (Without run.py)

If you prefer, you can run scripts directly:

#### Test Connection
```bash
python examples/test_connection.py
```

#### Quick Start
```bash
python examples/quick_start.py
```

#### Full Bot
```bash
# Edit credentials first
python examples/live_trading.py
```

#### Position Manager
```bash
# Edit credentials first
python examples/manage_positions.py
```

#### System Check
```bash
python examples/preflight_check.py
```

## Environment Variables (Optional)

Set these to avoid entering credentials each time:

### Windows (PowerShell)
```powershell
$env:MT5_LOGIN="12345678"
$env:MT5_PASSWORD="your_password"
$env:MT5_SERVER="Broker-Demo"
```

### Windows (CMD)
```cmd
set MT5_LOGIN=12345678
set MT5_PASSWORD=your_password
set MT5_SERVER=Broker-Demo
```

### Linux/Mac (bash)
```bash
export MT5_LOGIN=12345678
export MT5_PASSWORD=your_password
export MT5_SERVER=Broker-Demo
```

### Permanent (Create .env file)
```bash
# Create .env file in project root
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=Broker-Demo
```

## Typical Workflow

### First Time User

```bash
# Step 1: Run with checks
python run.py

# Step 2: Choose "4" to test connection only
Choice: 4

# Step 3: If successful, run again and choose "1" for quick start
python run.py
Choice: 1

# Step 4: Enter symbol and risk
Symbol: EURUSD
Risk %: 1.0

# Step 5: Type GO to start
Type 'GO' to start: GO

# Step 6: Watch it trade, press Ctrl+C to stop
```

### Daily Trading

```bash
# Just run and choose your mode
python run.py

# Choose quick start (1) or full bot (2)
Choice: 1

# Credentials remembered from environment
# Or enter them again

# Start trading!
```

### Check Positions

```bash
python run.py
Choice: 3

# View and manage positions
```

## What to Expect

### When System Starts

1. **Checks run automatically** - Dependencies, MT5, modules
2. **Prompts for credentials** - Or uses environment variables
3. **Tests connection** - Verifies MT5 login works
4. **Shows menu** - Choose your mode
5. **Starts selected mode** - Begins trading or management

### During Trading (Quick Start)

- Checks market every 30 seconds
- Shows current price and signal
- Executes trades when signal detected
- Displays order confirmation
- Shows open positions
- Press Ctrl+C to stop

### When You Stop

- Shows final positions
- Displays account status
- Disconnects from MT5
- Exits gracefully

## Safety Features

### Built-in Protections

✅ **Connection Verification** - Tests before trading
✅ **Symbol Validation** - Ensures symbol available
✅ **Risk Management** - Position sizing based on risk %
✅ **Signal Timing** - Prevents duplicate signals
✅ **Stop Losses** - Always set on trades
✅ **Graceful Shutdown** - Ctrl+C stops safely

### Your Responsibilities

⚠️ **Start with Demo** - Test thoroughly first
⚠️ **Monitor Trades** - Don't leave unattended initially
⚠️ **Low Risk** - Use 1% risk per trade
⚠️ **Understand Strategy** - Know what it does
⚠️ **Set Limits** - Max positions, max loss

## Troubleshooting

### "Dependencies check failed"
```bash
pip install MetaTrader5 numpy pandas
```

### "MT5 terminal not running"
- Launch MetaTrader 5
- Log in to your account
- Run script again

### "Connection failed"
- Verify credentials are correct
- Check MT5 is running and logged in
- Confirm server name (case-sensitive)
- Check internet connection

### "Symbol not available"
- Open MT5 Market Watch
- Right-click → Show All
- Find your symbol and enable it
- Run script again

### "Import errors"
```bash
# Ensure you're in project directory
cd /path/to/TradingMTQ

# Run from root
python run.py
```

## Tips for Success

### 🎯 Best Practices

1. **Always test on demo first** - At least 1 week
2. **Start with low risk** - 0.5-1% recommended
3. **Monitor closely** - First 10-20 trades
4. **Keep records** - Track performance
5. **Adjust gradually** - Don't change everything at once

### 📊 Optimal Settings (Beginners)

```
Symbol: EURUSD (most liquid)
Risk %: 1.0 (safe)
Mode: Quick Start (simplest)
Account: Demo (always start here)
```

### ⏰ Best Times to Trade

- **London/NY Overlap**: 1300-1700 UTC (highest volume)
- **Avoid**: Major news events
- **Avoid**: Sunday open, Friday close

## Summary

### To Start Trading:

```bash
python run.py
```

That's all! The system handles everything else.

### Most Common Path:

1. Run `python run.py`
2. Choose `1` (Quick Start)
3. Enter `EURUSD` for symbol
4. Enter `1.0` for risk
5. Type `GO` to start
6. Watch it trade
7. Press `Ctrl+C` to stop

**Simple. Safe. Automated.** 🚀

---

**Need more help?** Check the other docs:
- `START_HERE.md` - Complete overview
- `LIVE_TRADING_GUIDE.md` - Detailed guide
- `READY_TO_RUN.md` - Script reference
