# Automatic Database Seeding

**Date**: January 1, 2026
**Feature**: Auto-seed currency data on database initialization

---

## Problem Statement

When setting up a new TradingMTQ environment from scratch, users had to manually run separate seeding scripts after database initialization:

```bash
# Old process - 3 separate steps required
python -c "from src.database import init_db; init_db()"  # Creates tables only
python seed_currencies.py                                  # Seed currency configs
python scripts/seed_available_currencies.py               # Seed available currencies
```

This was error-prone and led to empty currency tables in fresh installations.

---

## Solution

The database initialization now **automatically seeds default data** when tables are empty.

### New Behavior

```python
from src.database import init_db

# Automatically creates tables AND seeds currencies if empty
init_db()
```

**Output on fresh database:**
```
✅ Seeded 4 currency configurations
✅ Seeded 25 available currencies
```

**Output on subsequent calls:**
```
(No output - data already exists, skipping seed)
```

---

## Implementation

### 1. New Module: `src/database/seed_data.py`

Created comprehensive seeding functions:

- `seed_currency_configurations()` - Seeds 4 default trading currencies
  - EURUSD, GBPUSD, USDJPY, AUDUSD
  - Each with default risk management settings

- `seed_available_currencies()` - Seeds 25+ available currencies
  - Major pairs (EURUSD, GBPUSD, USDJPY, etc.)
  - Cross pairs (EURJPY, GBPJPY, EURGBP, etc.)
  - Exotic pairs (USDTRY, USDZAR, USDMXN)
  - Commodities (XAUUSD, XAGUSD, USOIL, UKOIL)
  - Crypto (BTCUSD, ETHUSD)
  - Indices (US30, US500, NAS100)

- `seed_all()` - Seeds everything in one call

### 2. Enhanced `init_db()` Function

Updated `src/database/connection.py`:

```python
def init_db(
    database_url: Optional[str] = None,
    echo: bool = False,
    seed: Optional[bool] = None  # NEW parameter
) -> Engine:
    """
    Initialize database connection

    Args:
        seed: Whether to populate database with default data
              - None (default): Auto-seed if tables are empty ✅
              - True: Force seeding (will skip existing records)
              - False: Never seed
    """
```

**Auto-detection Logic:**
1. After creating tables, check if currency tables are empty
2. If empty OR `seed=True`, populate with default data
3. If data exists, skip seeding (logged in debug mode)

---

## Usage

### Default Behavior (Recommended)

```python
# Automatically seeds if database is empty
from src.database import init_db
init_db()
```

### Force Seeding

```python
# Always run seeding (skips existing records)
from src.database import init_db
init_db(seed=True)
```

### Disable Seeding

```python
# Never seed, even if tables are empty
from src.database import init_db
init_db(seed=False)
```

### Command Line

**Old way (still works):**
```bash
python seed_currencies.py
python scripts/seed_available_currencies.py
```

**New way (recommended):**
```bash
# Using the convenient wrapper script
python init_database.py --seed

# Or directly
python -c "from src.database import init_db; init_db()"
```

---

## Data Seeded

### Currency Configurations (4 pairs)

| Symbol | Strategy | Timeframe | SL/TP Pips | Risk % | Status |
|--------|----------|-----------|------------|--------|--------|
| EURUSD | Crossover | M15 | 50/100 | 1.0% | ✅ Enabled |
| GBPUSD | Crossover | M15 | 60/120 | 1.0% | ✅ Enabled |
| USDJPY | Crossover | M15 | 40/80 | 1.0% | ✅ Enabled |
| AUDUSD | Crossover | M15 | 50/100 | 1.0% | ✅ Enabled |

### Available Currencies (25+ pairs)

| Category | Count | Examples |
|----------|-------|----------|
| Major | 7 | EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD |
| Cross | 6 | EURJPY, GBPJPY, EURGBP, AUDJPY, EURAUD, EURCHF |
| Exotic | 3 | USDTRY, USDZAR, USDMXN |
| Commodity | 4 | XAUUSD (Gold), XAGUSD (Silver), USOIL, UKOIL |
| Crypto | 2 | BTCUSD, ETHUSD |
| Index | 3 | US30 (Dow), US500 (S&P), NAS100 (NASDAQ) |

---

## Benefits

### 1. Zero-Config Setup ✅
- New environments work out-of-the-box
- No manual seeding steps required
- Currency data automatically populated

### 2. Idempotent Operations ✅
- Safe to call `init_db()` multiple times
- Automatically skips existing records
- No duplicate data created

### 3. Development Friendly ✅
- Fresh test databases automatically populated
- CI/CD pipelines simplified
- Consistent data across environments

### 4. Backward Compatible ✅
- Old seeding scripts still work
- Explicit `seed=False` disables auto-seeding
- No breaking changes to existing code

---

## Migration Guide

### For Existing Projects

**No changes required!** Your existing code continues to work:

```python
# This still works exactly as before
from src.database import init_db
init_db()
```

**But now it also seeds currency data automatically** if the database is empty.

### For New Projects

**Just call `init_db()` and you're done:**

```python
from src.database import init_db
init_db()  # Creates tables AND seeds currencies
```

### For CI/CD Pipelines

**Simplified setup:**

```yaml
# Before: Multiple steps
- python -c "from src.database import init_db; init_db()"
- python seed_currencies.py
- python scripts/seed_available_currencies.py

# After: Single step
- python -c "from src.database import init_db; init_db()"
```

---

## Configuration

### Environment Variables

No new environment variables required. Uses existing configuration:

- `DATABASE_URL` - Database connection string (optional, defaults to SQLite)
- `ENVIRONMENT` - Environment name (development/production/test)

### Manual Seeding (if needed)

You can still manually seed specific data:

```python
from src.database import get_session
from src.database.seed_data import seed_currency_configurations, seed_available_currencies

with get_session() as session:
    # Seed only currency configurations
    count = seed_currency_configurations(session)
    print(f"Seeded {count} configs")

    # Seed only available currencies
    count = seed_available_currencies(session)
    print(f"Seeded {count} currencies")
```

---

## Testing

### Test Auto-Seeding

```bash
# Create fresh database and verify auto-seeding
rm -f trading_mtq.db
python -c "from src.database import init_db; init_db()"

# Should see:
# ✅ Seeded 4 currency configurations
# ✅ Seeded 25 available currencies
```

### Test Idempotency

```bash
# Run again - should skip seeding
python -c "from src.database import init_db; init_db()"

# No seeding output (data already exists)
```

### Verify Data

```python
from src.database import get_session, CurrencyConfiguration, AvailableCurrency

with get_session() as session:
    configs = session.query(CurrencyConfiguration).count()
    available = session.query(AvailableCurrency).count()

    print(f"Currency Configurations: {configs}")  # Should be 4
    print(f"Available Currencies: {available}")   # Should be 25+
```

---

## Troubleshooting

### Issue: No Data Seeded

**Problem**: `init_db()` doesn't seed data

**Solutions**:
1. Check if database already has data
2. Try with `init_db(seed=True)` to force seeding
3. Check logs for errors during seeding

### Issue: Duplicate Key Errors

**Problem**: Error about duplicate records

**Solution**: This shouldn't happen as seeding checks for existing records. If it does:
```python
# Clear and re-seed
rm trading_mtq.db
python -c "from src.database import init_db; init_db()"
```

### Issue: Custom Currency Data

**Problem**: Need different default currencies

**Solution**: Modify `src/database/seed_data.py`:
```python
# Edit the default_configs list
default_configs = [
    {
        "symbol": "YOUR_PAIR",
        "enabled": True,
        # ... your settings ...
    }
]
```

---

## Related Files

| File | Purpose |
|------|---------|
| `src/database/connection.py` | Enhanced `init_db()` with auto-seeding |
| `src/database/seed_data.py` | NEW - Seeding functions |
| `init_database.py` | NEW - Convenient CLI script |
| `seed_currencies.py` | LEGACY - Still works |
| `scripts/seed_available_currencies.py` | LEGACY - Still works |

---

## Future Enhancements

Potential improvements for future versions:

1. **Custom Seed Data** - Load from YAML/JSON files
2. **Seed Profiles** - Different sets for development/production
3. **Migration System** - Track seed data versions
4. **CLI Commands** - `python -m src.database seed --profile=production`
5. **Partial Seeding** - `init_db(seed=['currencies', 'accounts'])`

---

## Summary

**Before:**
```bash
python -c "from src.database import init_db; init_db()"  # Tables only ❌
python seed_currencies.py                                 # Manual step
python scripts/seed_available_currencies.py              # Manual step
```

**After:**
```bash
python -c "from src.database import init_db; init_db()"  # Tables + Data ✅
```

**One command. Zero hassle. Just works.** 🎉

---

**Status**: ✅ Implemented and Tested
**Version**: 1.0
**Compatibility**: Backward compatible with all existing code
