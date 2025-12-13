# TradingMTQ Deployment Package

This directory contains deployment scripts and configurations for different platforms.

---

## 📁 Directory Structure

```
deploy/
├── windows/                    # Windows deployment files
│   ├── quick-start.bat        # One-click setup (double-click this!)
│   ├── setup.ps1              # PowerShell setup script
│   ├── .env.template          # Environment configuration template
│   └── WINDOWS_QUICK_START.md # Quick start guide for Windows
│
└── README.md                  # This file
```

---

## 🚀 Quick Start

### For Windows + MetaTrader5

**Option 1: Double-Click Setup (Easiest)**

1. Navigate to: `deploy/windows/`
2. Double-click: `quick-start.bat`
3. Follow the prompts
4. Edit `.env` with your MT5 credentials
5. Run: `tradingmtq trade --demo`

**Option 2: PowerShell**

```powershell
cd TradingMTQ
powershell -ExecutionPolicy Bypass -File deploy\windows\setup.ps1
```

**Full guide:** See [windows/WINDOWS_QUICK_START.md](windows/WINDOWS_QUICK_START.md)

---

### For macOS/Linux (Testing/Development Only)

**Note:** MetaTrader5 is Windows-only, but you can test the database layer:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Initialize database
python src/database/migration_utils.py init

# Run tests
pytest tests/test_models.py tests/test_repositories.py -v
```

---

## 📋 What the Setup Script Does

1. ✅ Checks Python version (3.9+ required)
2. ✅ Creates virtual environment (`venv/`)
3. ✅ Installs all dependencies from `requirements.txt`
4. ✅ Installs TradingMTQ CLI commands
5. ✅ Checks for MetaTrader5 package
6. ✅ Creates `.env` from template
7. ✅ Initializes database schema
8. ✅ Runs unit tests (optional)
9. ✅ Verifies CLI installation

---

## ⚙️ Configuration Files

### `.env.template` → `.env`

The setup script creates `.env` from the template. You must edit it with your credentials:

```bash
# Required
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server

# Database (SQLite for quick start)
TRADING_MTQ_DATABASE_URL=sqlite:///./tradingmtq.db

# Optional: LLM API keys
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=...
```

### `config/currencies.yaml`

Trading configuration (already configured, review if needed):
- Trading interval
- Risk management
- Currency pairs
- Strategy parameters

---

## 🔍 Verification Steps

After running setup, verify:

```powershell
# 1. Check Python version
python --version
# Expected: Python 3.9.x or higher

# 2. Verify CLI installation
tradingmtq version
# Expected: TradingMTQ v2.0.0

# 3. Test database connection
python -c "from src.database.connection import check_database_health; print('DB Health:', check_database_health())"
# Expected: DB Health: True

# 4. Test MT5 (on Windows)
python -c "import MetaTrader5 as mt5; print('MT5:', mt5.initialize()); mt5.shutdown()"
# Expected: MT5: True
```

---

## 🎯 Next Steps After Setup

1. **Configure `.env`** with your MT5 credentials
2. **Review** `config/currencies.yaml` (optional)
3. **Test** in demo mode: `tradingmtq trade --demo`
4. **Monitor** for 15-30 minutes
5. **Deploy** to production when ready: `tradingmtq trade`

---

## 📚 Documentation

- **Quick Start (Windows):** [windows/WINDOWS_QUICK_START.md](windows/WINDOWS_QUICK_START.md)
- **Full Deployment Guide:** [../docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md](../docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md)
- **Database Guide:** [../src/database/README.md](../src/database/README.md)
- **General Deployment:** [../docs/DEPLOYMENT_GUIDE.md](../docs/DEPLOYMENT_GUIDE.md)

---

## 🆘 Troubleshooting

### Setup Script Fails

**Check:**
1. Python 3.9+ installed: `python --version`
2. Running from project root (where `main.py` is)
3. PowerShell execution policy (may need admin rights)

**Solution:**
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### MT5 Not Available

**This is normal on non-Windows systems.** MetaTrader5 only works on Windows.

**On Windows:**
1. Download MT5 from your broker
2. Install and login
3. Enable "Algo Trading"
4. Rerun setup script

---

### Database Initialization Fails

**For SQLite:** No setup needed, file created automatically

**For PostgreSQL:**
```powershell
# Ensure PostgreSQL is running
pg_ctl status

# Start if needed
net start postgresql-x64-13

# Verify connection string in .env
```

---

## 🔒 Security Notes

- `.env` file contains sensitive credentials
- `.env` is already in `.gitignore` (won't be committed)
- Keep your API keys secure
- Use strong database passwords
- Don't share your deployment package with credentials

---

## 📦 Package Contents

```
deploy/
└── windows/
    ├── quick-start.bat        # 29 lines - Batch launcher
    ├── setup.ps1              # 184 lines - PowerShell setup automation
    ├── .env.template          # 68 lines - Configuration template
    └── WINDOWS_QUICK_START.md # 485 lines - Comprehensive guide
```

**Total:** ~766 lines of deployment automation and documentation

---

## ✅ Deployment Checklist

Use this to track your deployment:

- [ ] Cloned repository to Windows machine
- [ ] Ran `quick-start.bat` or `setup.ps1`
- [ ] Edited `.env` with MT5 credentials
- [ ] Reviewed `config/currencies.yaml`
- [ ] Verified MT5 connection
- [ ] Tested in demo mode
- [ ] Monitored for 15-30 minutes
- [ ] Started production trading

---

## 🎉 Success!

When you see this in the logs, you're running:

```
[2025-12-13 14:00:00] INFO - Starting trading cycle #1
[2025-12-13 14:00:01] INFO - EURUSD: Signal BUY (confidence: 0.85)
[2025-12-13 14:00:02] INFO - Trade executed: Ticket=123456
[2025-12-13 14:00:02] DEBUG - Signal saved to database (ID: 1)
[2025-12-13 14:00:05] INFO - Portfolio snapshot saved
```

**Congratulations!** Your TradingMTQ system is live! 🚀

---

**Questions?** Check the [troubleshooting sections](windows/WINDOWS_QUICK_START.md#-troubleshooting) in the guides.
