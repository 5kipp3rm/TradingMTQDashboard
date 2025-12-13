# Windows Quick Start Guide

**Estimated Time:** 15 minutes
**For:** Windows 10/11 with MetaTrader 5

---

## 🚀 One-Command Deployment

### Method 1: Double-Click Setup (Easiest)

1. **Clone the repository** (if you haven't already):
   ```powershell
   git clone https://github.com/5kipp3rm/TradingMTQ.git
   cd TradingMTQ
   git checkout initial-claude-refactor
   ```

2. **Double-click** `deploy\windows\quick-start.bat`

3. **That's it!** The script will:
   - Check Python version
   - Create virtual environment
   - Install all dependencies
   - Initialize database
   - Run tests
   - Create `.env` template

---

### Method 2: PowerShell Command

```powershell
# Navigate to project directory
cd C:\Path\To\TradingMTQ

# Run setup script
powershell -ExecutionPolicy Bypass -File deploy\windows\setup.ps1

# Or with options:
powershell -ExecutionPolicy Bypass -File deploy\windows\setup.ps1 -UsePostgreSQL -SkipTests
```

---

## ⚙️ Configuration (5 minutes)

### 1. Edit `.env` File

The setup script created `.env` from the template. Now edit it:

```powershell
notepad .env
```

**Update these required values:**

```bash
# Your MT5 credentials
MT5_LOGIN=your_actual_login
MT5_PASSWORD=your_actual_password
MT5_SERVER=your_actual_server

# Database (SQLite is fine for start)
TRADING_MTQ_DATABASE_URL=sqlite:///./tradingmtq.db

# Optional: LLM API keys (set ENABLE_LLM=true if you use these)
# OPENAI_API_KEY=sk-your-key
# ANTHROPIC_API_KEY=your-key
```

**Save and close.**

---

### 2. Review Trading Configuration (Optional)

```powershell
notepad config\currencies.yaml
```

**Key settings to check:**
- `interval_seconds`: How often to check for signals (default: 30)
- `max_concurrent_trades`: Portfolio limit (default: 15)
- Currency pairs: Enable/disable pairs, adjust risk

**For first run, recommend:**
- Start with 1-2 currency pairs
- Use conservative settings
- Test in demo mode first

---

## 🔍 Verify MetaTrader 5

### 1. Open MT5 Terminal

- Login to your demo or live account
- Ensure "Algo Trading" button is **enabled** (green, top toolbar)

### 2. Check Settings

Go to **Tools → Options → Expert Advisors**:
- ✅ Allow automated trading
- ✅ Allow DLL imports
- ✅ Allow WebRequest for listed URLs (if needed)

### 3. Test Connection

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Test MT5 connection
python -c "import MetaTrader5 as mt5; print('MT5 Available:', mt5.initialize()); mt5.shutdown()"

# Expected output: MT5 Available: True
```

**If False:**
- Check MT5 is running
- Verify "Algo Trading" is enabled
- Check DLL imports are allowed
- Try restarting MT5

---

## 🎯 Start Trading

### Demo Mode First (Recommended)

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start in demo mode
tradingmtq trade --demo

# Let it run for 15-30 minutes
# Watch for trade executions
# Verify database is being populated
```

**What you should see:**
```
[2025-12-13 14:00:00] INFO - Starting trading cycle #1
[2025-12-13 14:00:01] INFO - EURUSD: Signal BUY (confidence: 0.85)
[2025-12-13 14:00:02] INFO - Trade executed: Ticket=123456
[2025-12-13 14:00:02] DEBUG - Signal saved to database (ID: 1)
[2025-12-13 14:00:02] DEBUG - Trade saved to database (ID: 1)
[2025-12-13 14:00:05] INFO - Portfolio snapshot saved
```

**Stop with:** `Ctrl+C`

---

### Production Mode (When Ready)

```powershell
# Make sure .env has your live account credentials

# Start with default settings
tradingmtq trade

# Or with aggressive mode
tradingmtq trade --aggressive

# Or with custom settings
tradingmtq trade -i 30 -m 15 --enable-ml --enable-llm
```

---

## 📊 Monitor Trading

### Option 1: Watch Logs

```powershell
# In new PowerShell window
Get-Content logs\trading.log -Wait
```

### Option 2: Create Monitor Script

Create `monitor.ps1`:

```powershell
# Simple monitoring script
while ($true) {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  TradingMTQ Monitor" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Get latest log lines
    Get-Content logs\trading.log -Tail 20

    Write-Host ""
    Write-Host "Press Ctrl+C to exit" -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
```

Run: `powershell .\monitor.ps1`

---

## 🔍 Verify Database

```powershell
# Check trades in database
python -c "from src.database.repository import TradeRepository; from src.database.connection import get_session; repo = TradeRepository(); s = get_session().__enter__(); trades = repo.get_all_trades(s); print(f'Total trades: {len(trades)}'); s.close()"

# Check signals
python -c "from src.database.repository import SignalRepository; from src.database.connection import get_session; repo = SignalRepository(); s = get_session().__enter__(); signals = repo.get_recent_signals(s, limit=10); print(f'Recent signals: {len(signals)}'); s.close()"

# Get statistics
python -c "from src.database.repository import TradeRepository; from src.database.connection import get_session; repo = TradeRepository(); s = get_session().__enter__(); stats = repo.get_trade_statistics(s); print(f\"Win Rate: {stats['win_rate']:.2f}%\"); print(f\"Profit: ${stats['total_profit']:.2f}\"); s.close()"
```

---

## 🛠️ Useful Commands

```powershell
# System check
tradingmtq check

# Show version
tradingmtq version

# Run with specific config
tradingmtq trade -c config\custom.yaml

# Disable ML
tradingmtq trade --disable-ml

# Disable LLM
tradingmtq trade --disable-llm

# Both disabled
tradingmtq trade --disable-ml --disable-llm

# Custom interval and max positions
tradingmtq trade -i 60 -m 20

# Help
tradingmtq --help
tradingmtq trade --help
```

---

## 🆘 Troubleshooting

### Issue: "Python not found"

**Solution:**
```powershell
# Download Python 3.9+ from python.org
# Or use Chocolatey:
choco install python

# Verify:
python --version
```

---

### Issue: "MT5 initialization failed"

**Solution:**
1. Open MetaTrader 5
2. Login to account
3. Enable "Algo Trading" button (top toolbar, should be green)
4. Tools → Options → Expert Advisors:
   - Check "Allow automated trading"
   - Check "Allow DLL imports"
5. Restart MT5 if needed

---

### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution:**
```powershell
# Reinstall package
pip install -e .

# Or set PYTHONPATH
$env:PYTHONPATH = (Get-Location).Path
```

---

### Issue: "No trades executing"

**Check:**
1. Are signals being generated? (check logs or database)
2. Is margin sufficient?
3. Is market open?
4. Is "Algo Trading" enabled in MT5?
5. Check configuration in `config/currencies.yaml`

---

### Issue: "Database connection failed"

**For SQLite:**
- No server needed, file created automatically
- Check write permissions in project directory

**For PostgreSQL:**
```powershell
# Check PostgreSQL is running
pg_ctl status

# Start service
net start postgresql-x64-13
```

---

## 📦 PostgreSQL Setup (Optional)

If you want to use PostgreSQL instead of SQLite:

### 1. Install PostgreSQL

```powershell
# Download from: https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql
```

### 2. Create Database

```powershell
# Open psql
psql -U postgres

# Create database
CREATE DATABASE tradingmtq;

# Create user
CREATE USER tradingmtq_user WITH ENCRYPTED PASSWORD 'YourSecurePassword123';
GRANT ALL PRIVILEGES ON DATABASE tradingmtq TO tradingmtq_user;

# Exit
\q
```

### 3. Update `.env`

```bash
TRADING_MTQ_DATABASE_URL=postgresql://tradingmtq_user:YourSecurePassword123@localhost:5432/tradingmtq
```

### 4. Reinitialize Database

```powershell
python src\database\migration_utils.py init
```

---

## ✅ Deployment Checklist

- [ ] Repository cloned
- [ ] Python 3.9+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` configured with MT5 credentials
- [ ] Database initialized
- [ ] MT5 running with Algo Trading enabled
- [ ] Tests passing (optional)
- [ ] Demo mode tested
- [ ] Production started

---

## 📚 Next Steps

**After deployment is stable:**

1. **Monitor for 24-48 hours**
   - Check logs regularly
   - Verify trades are executing
   - Monitor database growth

2. **Setup automated backups**
   - Database backups
   - Configuration backups

3. **Begin Phase 5.2** (Analytics Dashboard)
   - See: `docs\PHASE_5.2_ANALYTICS_PLAN.md`

---

## 🔗 Resources

- **Full Guide:** `docs\PRODUCTION_DEPLOYMENT_CHECKLIST.md`
- **Database Guide:** `src\database\README.md`
- **General Deployment:** `docs\DEPLOYMENT_GUIDE.md`
- **Current Status:** `docs\CURRENT_STATUS.md`

---

## 🎯 Success Indicators

**You're ready when:**
- ✅ System runs without errors
- ✅ Trades are executing
- ✅ Database is growing (trades, signals, snapshots)
- ✅ MT5 shows active orders
- ✅ Logs show trading cycles
- ✅ No critical errors

---

**Quick support:** Check logs first, then review troubleshooting section above.

**Estimated total time:** 15-30 minutes from start to first trade

Good luck with your trading! 🚀
