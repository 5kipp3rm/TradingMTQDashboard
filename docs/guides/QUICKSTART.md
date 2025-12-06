# 🚀 TradingMTQ - Quick Reference Card

## One-Command Start

```bash
python run.py
```

## What You Get

- ✅ Automatic system checks
- ✅ MT5 connection testing
- ✅ Interactive menu
- ✅ Multiple trading modes
- ✅ Safe operation

## Menu Options

| # | Mode | Description | Safe? |
|---|------|-------------|-------|
| 1 | Quick Start | Interactive trading | 🟡 LIVE |
| 2 | Full Bot | Advanced features | 🟡 LIVE |
| 3 | Position Manager | View/close positions | 🟠 Management |
| 4 | Test Only | Connection test | ⚪ SAFE |
| 5 | Exit | Quit application | ⚪ SAFE |

## First Time Setup

```bash
# 1. Install dependencies (if needed)
pip install MetaTrader5 numpy pandas

# 2. Run the system
python run.py

# 3. Choose option 4 (Test Only) first
Choice: 4

# 4. If successful, run again and choose option 1
python run.py
Choice: 1
```

## Common Commands

### Start Trading
```bash
python run.py
# Choose: 1 (Quick Start)
```

### Check Positions
```bash
python run.py
# Choose: 3 (Position Manager)
```

### Test Connection
```bash
python run.py
# Choose: 4 (Test Only)
```

## Direct Scripts (Alternative)

```bash
# Test connection
python examples/test_connection.py

# Quick start trading
python examples/quick_start.py

# Full automated bot
python examples/live_trading.py

# Manage positions
python examples/manage_positions.py

# System check
python examples/preflight_check.py
```

## Environment Variables (Optional)

```bash
# Windows (PowerShell)
$env:MT5_LOGIN="12345678"
$env:MT5_PASSWORD="your_password"
$env:MT5_SERVER="Broker-Demo"

# Linux/Mac
export MT5_LOGIN=12345678
export MT5_PASSWORD=your_password
export MT5_SERVER=Broker-Demo
```

## Typical Workflow

```
Run python run.py
    ↓
System checks pass
    ↓
Enter credentials
    ↓
Connection successful
    ↓
Choose mode (1-5)
    ↓
Start trading or managing
    ↓
Press Ctrl+C to stop
    ↓
Positions remain open
```

## Safety Checklist

- [ ] Using DEMO account?
- [ ] Risk set to 1% or less?
- [ ] Understand the strategy?
- [ ] Monitoring first trades?
- [ ] Have stop-loss limits?

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't find MT5 | Install MetaTrader 5 |
| Connection fails | Check credentials, MT5 running |
| Symbol not found | Add to Market Watch in MT5 |
| Import error | `pip install -r requirements.txt` |
| Insufficient margin | Reduce risk % or lot size |

## Key Features

- 🛡️ Risk-based position sizing
- 📊 12+ technical indicators
- 🤖 5+ trading strategies
- 📈 Real-time monitoring
- 🔒 Stop-loss enforcement
- ⚡ Automated execution
- 📝 Comprehensive logging

## Default Settings (Quick Start)

```
Symbol: EURUSD
Timeframe: M5 (5 minutes)
Risk: 1.0% per trade
Strategy: MA Crossover (10/20)
Stop Loss: 20 pips
Take Profit: 40 pips
Check Interval: 30 seconds
```

## Documentation Quick Links

| Document | Purpose |
|----------|---------|
| `USAGE.md` | Complete usage guide |
| `START_HERE.md` | System overview |
| `LIVE_TRADING_GUIDE.md` | Full trading guide |
| `READY_TO_RUN.md` | Script reference |
| `README.md` | Project readme |

## Support

1. Check error message (they're descriptive!)
2. Review `USAGE.md` troubleshooting
3. Run `python examples/preflight_check.py`
4. Verify MT5 is running
5. Test with demo account

## Remember

⚠️ **Always:**
- Start with DEMO
- Use low risk (1%)
- Monitor closely
- Set stop losses
- Trade responsibly

🚀 **To Start:**
```bash
python run.py
```

That's all you need to know! 🎯
