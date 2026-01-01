# Python Files Organization

**Date**: January 1, 2026
**Status**: ✅ Organized

---

## 📋 Summary

All Python files have been organized into their appropriate locations. Root directory now contains only essential entry points.

---

## 📂 Final Structure

```
/
├── main.py                    # Main CLI entry point ✅
├── run.py                     # Alternative entry point ✅
│
├── scripts/                   # Utility scripts
│   ├── init_database.py
│   ├── check_readiness.py
│   ├── check_status.py
│   ├── seed_currencies.py.old  # Archived (superseded)
│   └── [30+ other utility scripts]
│
├── tests/                     # Test scripts
│   ├── test_database.py
│   ├── test_trading_with_db.py
│   └── [50+ other test files]
│
└── src/                       # Source code
    └── [application modules]
```

---

## 🔄 What Was Moved

### From Root → scripts/ (Utilities)

| File | Purpose | Size |
|------|---------|------|
| `init_database.py` | Database initialization | 3.4 KB |
| `check_readiness.py` | ML/LLM readiness check | 1.4 KB |
| `check_status.py` | MT5 connection status | 0.7 KB |

### From Root → tests/ (Test Scripts)

| File | Purpose | Size |
|------|---------|------|
| `test_database.py` | Database integration tests | 12.8 KB |
| `test_trading_with_db.py` | Trading cycle tests | 12.4 KB |

### Archived (Obsolete)

| File | Reason | New Location |
|------|--------|--------------|
| `seed_currencies.py` | Superseded by `init_db(seed=True)` | `scripts/seed_currencies.py.old` |

---

## ✅ Files Kept in Root

### main.py (17.8 KB)
**Purpose**: Main CLI application entry point

**Usage**:
```bash
python main.py
```

**Features**:
- CLI interface via Click
- Multi-currency trading orchestration
- ML/LLM integration
- Configuration management

### run.py (23.3 KB)
**Purpose**: Alternative entry point for automated trading

**Usage**:
```bash
python run.py
```

**Features**:
- Direct trading execution
- Background worker management
- Monitoring and logging
- Legacy compatibility

---

## 📁 scripts/ Directory

### Utility Scripts (Now Organized)

**Database Management**:
- `init_database.py` - Initialize database with auto-seeding
- `create_available_currencies_table.py` - Create currency tables
- `seed_available_currencies.py` - Seed currencies (alternative method)

**System Checks**:
- `check_readiness.py` - Verify ML/LLM readiness
- `check_status.py` - Check MT5 connection
- `check_env.py` - Verify environment setup
- `check_autotrading.py` - Check auto-trading status

**Trading Utilities**:
- `check_positions.py` - View open positions
- `check_signal.py` - Test trading signals
- `close_all_positions.py` - Emergency position closure
- `pip_calculator.py` - Calculate pip values

**ML/Training**:
- `train_ml_model.py` - Train machine learning models
- `train_models.py` - Model training pipeline
- `train_all.py` - Train all models
- `collect_data.py` - Collect historical data
- `prepare_features.py` - Feature engineering

**Testing**:
- `test_ml_integration.py` - Test ML integration
- `test_intelligent_trading.py` - Test intelligent trading
- `test_live_intelligent.py` - Live intelligent trading test
- `test_signals.py` - Signal generation tests
- `test_simple.py` - Simple integration tests

**Account Management**:
- `add_account.py` - Add trading accounts
- `create_account_currency_configs_table.py` - Setup account configs

**Other**:
- `calculate_profit_scenarios.py` - Profit scenario analysis
- `start_mt5.py` - Start MetaTrader 5
- `activate_aggressive.sh` - Enable aggressive trading

### Archived Scripts

- `seed_currencies.py.old` - Old seeding script (use `init_db(seed=True)` instead)

---

## 🧪 tests/ Directory

### Test Scripts (Properly Organized)

**New Additions from Root**:
- `test_database.py` - Phase 5.1 database integration tests
- `test_trading_with_db.py` - Complete trading cycle tests

**Existing Tests** (50+ files):
- `test_*.py` - Unit and integration tests
- Organized by module/feature
- Run with `pytest`

---

## 🎯 Usage Guide

### Running Entry Points

**Main CLI Application**:
```bash
# Recommended method
python main.py

# Or using installed CLI
tradingmtq
mtq
```

**Alternative Entry Point**:
```bash
python run.py
```

### Running Utility Scripts

**Database Initialization**:
```bash
python scripts/init_database.py --seed
```

**Check System Readiness**:
```bash
python scripts/check_readiness.py
```

**Check MT5 Status**:
```bash
python scripts/check_status.py
```

**Train ML Models**:
```bash
python scripts/train_ml_model.py
```

### Running Tests

**All Tests**:
```bash
pytest
```

**Specific Test**:
```bash
pytest tests/test_database.py
```

**With Coverage**:
```bash
pytest --cov=src --cov-report=html
```

---

## 📝 Migration Notes

### For Developers

**If you had scripts referencing root Python files**:

**Before**:
```bash
python check_readiness.py
python seed_currencies.py
python test_database.py
```

**After**:
```bash
python scripts/check_readiness.py
# seed_currencies.py is obsolete - use: python -c "from src.database import init_db; init_db(seed=True)"
pytest tests/test_database.py
```

### For CI/CD

**Update pipeline scripts**:
```yaml
# Before
- python test_database.py

# After
- pytest tests/test_database.py
```

### For Documentation

**Update script references**:
- `init_database.py` → `scripts/init_database.py`
- `seed_currencies.py` → Use `init_db(seed=True)` instead
- Test scripts → Run via `pytest tests/`

---

## 🔍 Finding Scripts

### By Purpose

**Need to initialize database?**
→ `scripts/init_database.py --seed`

**Need to check system status?**
→ `scripts/check_status.py` or `scripts/check_readiness.py`

**Need to train models?**
→ `scripts/train_ml_model.py`

**Need to run tests?**
→ `pytest tests/`

### By Location

```bash
# List all utility scripts
ls scripts/*.py

# List all test scripts
ls tests/test_*.py

# List entry points
ls *.py
```

---

## ✅ Benefits

### Before Organization
- 8 Python files cluttering root directory
- Mixed purposes (entry points, utilities, tests)
- Unclear which files are essential
- Hard to find specific scripts

### After Organization
- 2 Python files in root (entry points only)
- Clear categorization by purpose
- scripts/ for utilities
- tests/ for test scripts
- Professional structure

---

## 🛠️ Maintenance

### Adding New Scripts

**Utility Scripts**:
```bash
# Add to scripts/
cp my_new_utility.py scripts/
```

**Test Scripts**:
```bash
# Add to tests/ with test_ prefix
cp test_my_feature.py tests/
```

**Entry Points**:
```bash
# Only add to root if it's a main entry point
# Otherwise, use scripts/ or add to src/
```

### Archiving Old Scripts

**When script becomes obsolete**:
```bash
mv scripts/old_script.py scripts/old_script.py.old
```

**Document replacement**:
```markdown
## Archived Scripts

- `old_script.py.old` - Superseded by [new method]
```

---

## 📚 Related Documentation

- [MODERN_PYTHON_SETUP.md](01-setup/MODERN_PYTHON_SETUP.md) - Modern packaging with pyproject.toml
- [COMPLETE_SETUP_AND_RUN_GUIDE.md](01-setup/COMPLETE_SETUP_AND_RUN_GUIDE.md) - Complete setup guide
- [DATABASE_SEEDING_AUTO.md](07-implementation/features/DATABASE_SEEDING_AUTO.md) - Auto-seeding feature

---

## 🎓 Best Practices

### 1. Keep Root Minimal
- Only entry points (main.py, run.py)
- No utility or test scripts

### 2. Organize by Purpose
- Utilities → scripts/
- Tests → tests/
- Source code → src/

### 3. Use Descriptive Names
- Utilities: `check_*.py`, `test_*.py`, etc.
- Tests: Always prefix with `test_`
- Clear, action-oriented names

### 4. Archive Obsolete Files
- Don't delete immediately
- Rename with `.old` suffix
- Document replacement in README

### 5. Update References
- Check documentation for script references
- Update CI/CD pipelines
- Update setup guides

---

**Status**: ✅ Organization Complete
**Impact**: Minimal - entry points unchanged
**Breaking Changes**: None (all scripts still accessible)
