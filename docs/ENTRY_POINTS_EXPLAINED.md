# TradingMTQ Entry Points Explained

**Date**: January 1, 2026
**Question**: Why do we have multiple entry points?

---

## 📋 Current Entry Points

You currently have **3 different ways** to start the application:

| File | Purpose | When to Use |
|------|---------|-------------|
| **main.py** | CLI application (modern) | Trading bot with CLI interface |
| **run.py** | Legacy launcher (old) | Windows with full system checks |
| **start-dev.sh** | Dashboard development | Web UI development mode |

---

## 🤔 The Problem: Too Many Entry Points

You're right to question this! Having 3 entry points is confusing and redundant.

### Current Situation

```bash
# Method 1: Using main.py (modern CLI)
python main.py

# Method 2: Using run.py (legacy)
python run.py

# Method 3: Using start-dev.sh (dashboard)
./start-dev.sh

# Method 4: Using installed CLI
tradingmtq
```

**This is confusing!** 😵

---

## 🎯 Recommended Simplification

### Keep Only What's Needed

| Keep | Purpose | Reason |
|------|---------|--------|
| ✅ **main.py** | CLI entry point | Modern, well-structured, uses Click framework |
| ✅ **start-dev.sh** | Dashboard launcher | Unique purpose: starts FastAPI + React dashboard |
| ❌ **run.py** | Remove/Archive | Redundant - same as `python main.py trade` |

---

## 📊 Detailed Analysis

### 1. main.py (KEEP) ✅

**Purpose**: Modern CLI application with Click framework

**What it does**:
- Loads environment variables
- Launches CLI with commands: `trade`, `test`, `config`, etc.
- Windows encoding fix
- Delegates to `src.cli:cli`

**Usage**:
```bash
python main.py            # Interactive CLI
python main.py trade      # Start trading
tradingmtq trade          # After pip install -e .
```

**Verdict**: **KEEP** - This is your primary, modern entry point

---

### 2. run.py (ARCHIVE?) ❓

**Purpose**: Legacy launcher with comprehensive system checks

**What it does**:
- Checks dependencies (numpy, pandas, MT5)
- Finds MT5 executable (Windows only)
- Tests MT5 connection
- Offers menu-driven interface
- Launches trading

**Problems**:
- Windows-specific (winreg usage)
- Redundant functionality (same as `python main.py trade`)
- More complex but doesn't add value
- Not maintained (legacy code)

**Verdict**: **ARCHIVE** - Functionality covered by `main.py`

**Alternative**: Keep if you need Windows-specific MT5 checks, but move to `scripts/`

---

### 3. start-dev.sh (KEEP) ✅

**Purpose**: Development mode for dashboard

**What it does**:
- Activates virtual environment
- Installs dashboard dependencies (yarn)
- Starts FastAPI backend (port 8000)
- Starts React dashboard (port 8080)
- Manages both processes

**Usage**:
```bash
./start-dev.sh
```

**Verdict**: **KEEP** - Unique purpose, can't be replaced by main.py

---

## 💡 Recommended Actions

### Option 1: Minimal (Recommended)

**Keep**:
- `main.py` - Primary entry point
- `start-dev.sh` - Dashboard development

**Archive**:
- `run.py` → `scripts/run.py.old`

**Result**: 2 clear entry points with distinct purposes

---

### Option 2: Keep run.py for Windows Users

**Keep**:
- `main.py` - Primary entry point
- `run.py` - Windows-specific launcher with MT5 checks
- `start-dev.sh` - Dashboard development

**Rename**:
- `run.py` → `run_windows.py` (clarify Windows-only)

**Result**: 3 entry points, but clearer naming

---

### Option 3: Consolidate Everything

**Keep**:
- `main.py` - Enhanced to include all features
- `start-dev.sh` - Dashboard only

**Enhance main.py** to include:
- MT5 connection checks (from run.py)
- Dependency verification
- Menu-driven interface option

**Archive**:
- `run.py` → scripts/run.py.old

**Result**: 1 entry point + dashboard launcher

---

## 🎯 My Recommendation: **Option 1 (Minimal)**

### Why?

1. **main.py** is modern, uses Click CLI framework, well-maintained
2. **run.py** is legacy code, Windows-specific, redundant
3. **start-dev.sh** has unique purpose (dashboard), must keep

### Implementation

```bash
# Archive run.py
mv run.py scripts/run.py.old

# Update documentation
# Only reference: python main.py or ./start-dev.sh
```

### After Cleanup

**For Trading**:
```bash
# Option 1: Direct
python main.py trade

# Option 2: Installed CLI
pip install -e .
tradingmtq trade
```

**For Dashboard Development**:
```bash
./start-dev.sh
```

**Simple and Clear!** ✨

---

## 📝 Comparison Table

| Feature | main.py | run.py | start-dev.sh |
|---------|---------|--------|--------------|
| **CLI Framework** | ✅ Click | ❌ Manual | N/A |
| **Trading** | ✅ Yes | ✅ Yes | ❌ No |
| **Dashboard** | ❌ No | ❌ No | ✅ Yes |
| **MT5 Checks** | Basic | ✅ Advanced | N/A |
| **Windows Only** | ❌ Cross-platform | ⚠️ Yes | ❌ Cross-platform |
| **Maintained** | ✅ Yes | ❌ Legacy | ✅ Yes |
| **Dependency Check** | ❌ No | ✅ Yes | ⚠️ Partial |

---

## 🚀 Migration Guide

### If We Archive run.py

**Old Usage**:
```bash
python run.py
```

**New Usage**:
```bash
python main.py trade

# Or after installation
tradingmtq trade
```

**For Windows MT5 Checks**:
```bash
# Check MT5 connection
python scripts/check_status.py

# Check dependencies
python scripts/check_readiness.py
```

---

## 🎓 Best Practice

### Standard Python Project Structure

```
project/
├── main.py              # Single primary entry point ✅
├── setup.py/pyproject.toml  # Package configuration
├── src/                 # Source code
│   └── cli/            # CLI commands
├── scripts/             # Utility scripts
│   ├── check_*.py      # Health checks
│   └── run.py.old      # Archived legacy launcher
└── start-dev.sh         # Development mode launcher
```

**One clear entry point** is industry standard!

---

## ❓ FAQs

### Q: Will I lose functionality if I archive run.py?
**A**: No! All functionality is available through:
- `python main.py trade` - Trading
- `scripts/check_status.py` - MT5 checks
- `scripts/check_readiness.py` - Dependency checks

### Q: What about Windows users who need MT5 checks?
**A**: Two options:
1. Use `scripts/check_status.py` before trading
2. Keep `run.py` but rename to `run_windows.py` for clarity

### Q: Can I still use the old way?
**A**: Yes, if you keep run.py.old, you can restore it anytime:
```bash
cp scripts/run.py.old run.py
python run.py
```

---

## 📚 Related Documentation

- [PYTHON_FILES_ORGANIZATION.md](PYTHON_FILES_ORGANIZATION.md) - Python file structure
- [MODERN_PYTHON_SETUP.md](01-setup/MODERN_PYTHON_SETUP.md) - Modern packaging
- [COMPLETE_SETUP_AND_RUN_GUIDE.md](01-setup/COMPLETE_SETUP_AND_RUN_GUIDE.md) - Setup guide

---

## ✅ Conclusion

**Current**: 3 entry points (confusing)
**Recommended**: 2 entry points (clear)

1. **main.py** - Trading bot (primary)
2. **start-dev.sh** - Dashboard development

**Action**: Archive `run.py` to `scripts/run.py.old`

**Result**: Simpler, clearer, easier to maintain! 🎉

---

**Status**: Recommendation Ready
**Decision**: Awaiting user confirmation
**Impact**: Zero (run.py archived, not deleted)
