# Soft Delete Design for Currency Management

## Overview

The currency management system implements a **smart delete strategy** that preserves data integrity for currencies with trade history while allowing clean removal of unused configurations.

## Design Principles

### 1. Data Integrity First

- **Never delete currencies with trade history** - Historical data must remain accessible for:
  - Performance analysis
  - Audit trails
  - Tax reporting
  - Compliance requirements

### 2. User Experience

- **Hide deleted currencies from UI** - Users shouldn't see currencies they've removed
- **Prevent accidental re-trading** - Deleted currencies are also disabled

### 3. Database Efficiency

- **Hard delete when possible** - Remove unused configurations completely to keep database lean
- **Soft delete when necessary** - Mark as deleted but keep record when trade history exists

## Implementation

### Database Schema

Added `is_deleted` column to `account_currency_configs` table:

```sql
ALTER TABLE account_currency_configs
ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0;
```

### Delete Logic (Backend)

**File**: `src/api/routes/accounts.py:1120-1184`

```python
@router.delete("/accounts/{account_id}/currencies/{symbol}")
async def delete_account_currency(account_id: int, symbol: str, db: Session):
    # 1. Verify account and currency config exist
    # 2. Check if currency has trade history
    has_trades = db.execute(
        select(Trade).where(
            Trade.account_id == account_id,
            Trade.symbol == symbol
        ).limit(1)
    ).scalar_one_or_none()

    if has_trades:
        # SOFT DELETE: Mark as deleted, keep for historical data
        account_config.is_deleted = True
        account_config.enabled = False  # Prevent accidental trading
        db.commit()
    else:
        # HARD DELETE: Remove completely (no trade history)
        db.delete(account_config)
        db.commit()
```

### Query Filtering

**File**: `src/api/routes/accounts.py:920-925`

All currency list queries filter out deleted currencies:

```python
account_configs_query = select(AccountCurrencyConfig).where(
    AccountCurrencyConfig.account_id == account_id,
    AccountCurrencyConfig.is_deleted == False  # Hide deleted from UI
)
```

### Model Update

**File**: `src/database/account_currency_models.py:67-68`

```python
# Soft delete flag (for currencies with trade history)
is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

## Deletion Flow

### Scenario 1: Currency WITHOUT Trade History (Hard Delete)

```
User clicks delete → Backend checks trades → No trades found →
DELETE FROM account_currency_configs → Success (204 No Content)
```

**Result**: Currency completely removed from database

**Log**: `"Hard deleted currency EURUSD for account 3 (no trade history)"`

### Scenario 2: Currency WITH Trade History (Soft Delete)

```
User clicks delete → Backend checks trades → Trades found →
UPDATE account_currency_configs SET is_deleted=1, enabled=0 →
Success (204 No Content)
```

**Result**: Currency marked as deleted, hidden from UI, but preserved in database

**Log**: `"Soft deleted currency EURUSD for account 3 (has trade history)"`

## UI Behavior

### Before Soft Delete Implementation

**Problem**: Deleted currencies remained visible in UI because endpoint returned all global currencies

**Issue**:
```
DELETE request → 204 Success → Currency still shown in UI →
User confused → Tries to delete again → Same result
```

### After Soft Delete Implementation

**Solution**: Only return currencies explicitly added to account (excluding deleted)

**Flow**:
```
1. User adds EURUSD → Shows in UI
2. User trades EURUSD → Trade history created
3. User deletes EURUSD → Soft deleted (is_deleted=1)
4. GET /accounts/3/currencies → Filters out is_deleted=1
5. UI shows EURUSD removed → Success!
```

## Benefits

### ✅ Data Integrity
- Trade history always has valid currency reference
- No orphaned trade records
- Complete audit trail

### ✅ Database Efficiency
- Unused currencies hard deleted (no wasted space)
- Only currencies with history kept (minimal overhead)

### ✅ User Experience
- Deleted currencies immediately disappear from UI
- No confusion about delete status
- Clean interface showing only active currencies

### ✅ Safety
- Soft-deleted currencies also disabled (`enabled=0`)
- Prevents accidental re-trading of removed currencies
- Can be "undeleted" if needed (future enhancement)

## API Endpoints

### DELETE /api/accounts/{account_id}/currencies/{symbol}

**Status Code**: `204 No Content` (both hard and soft delete)

**Behavior**:
- Checks for trade history
- Hard delete if no trades
- Soft delete if trades exist
- Logs action with context

### GET /api/accounts/{account_id}/currencies

**Returns**: Only non-deleted currencies

**Filters**:
- `is_deleted = False` (always applied)
- `enabled_only = true` (optional query param)

## Testing Scenarios

### Test 1: Delete Currency Without Trades

```bash
# Add currency
POST /api/accounts/3/currencies/GBPUSD

# Verify it shows
GET /api/accounts/3/currencies → Contains GBPUSD

# Delete it
DELETE /api/accounts/3/currencies/GBPUSD

# Verify it's gone
GET /api/accounts/3/currencies → Does NOT contain GBPUSD

# Check database
SELECT * FROM account_currency_configs WHERE account_id=3 AND currency_symbol='GBPUSD'
→ No rows (hard deleted)
```

### Test 2: Delete Currency With Trades

```bash
# Add currency and trade it
POST /api/accounts/3/currencies/EURUSD
# ... execute trades ...

# Delete it
DELETE /api/accounts/3/currencies/EURUSD

# Verify it's hidden from UI
GET /api/accounts/3/currencies → Does NOT contain EURUSD

# Check database - record still exists but marked deleted
SELECT * FROM account_currency_configs WHERE account_id=3 AND currency_symbol='EURUSD'
→ id=1, is_deleted=1, enabled=0

# Verify trades still accessible
SELECT * FROM trades WHERE account_id=3 AND symbol='EURUSD'
→ All trades intact with valid currency reference
```

## Future Enhancements

### 1. Undelete Functionality

Allow users to restore soft-deleted currencies:

```python
@router.post("/accounts/{account_id}/currencies/{symbol}/restore")
async def restore_currency(account_id: int, symbol: str):
    # Set is_deleted = False, enabled = True
```

### 2. Archive Old Trades

For currencies deleted long ago with old trades, archive to separate table:

```python
# After 1 year, move soft-deleted currencies with old trades to archive
if account_config.is_deleted and last_trade > 365_days_ago:
    archive_currency_config(account_config)
```

### 3. Bulk Operations

```python
@router.delete("/accounts/{account_id}/currencies/bulk")
async def bulk_delete_currencies(account_id: int, symbols: List[str]):
    # Delete multiple currencies at once
```

## Migration Notes

### From Old System

If migrating from a system without `is_deleted` column:

```sql
-- Add column with default value
ALTER TABLE account_currency_configs
ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0;

-- All existing records are NOT deleted by default
-- No data migration needed
```

### Cleanup Old Deleted Records

If you had previously hard-deleted currencies but want to maintain history:

```sql
-- Check for orphaned trades (trades without currency config)
SELECT DISTINCT t.symbol, t.account_id
FROM trades t
LEFT JOIN account_currency_configs acc
  ON t.account_id = acc.account_id AND t.symbol = acc.currency_symbol
WHERE acc.id IS NULL;

-- Create soft-deleted entries for orphaned trades
INSERT INTO account_currency_configs
  (account_id, currency_symbol, enabled, is_deleted, created_at, updated_at)
SELECT DISTINCT
  t.account_id,
  t.symbol,
  0,
  1,
  MIN(t.entry_time),
  NOW()
FROM trades t
LEFT JOIN account_currency_configs acc
  ON t.account_id = acc.account_id AND t.symbol = acc.currency_symbol
WHERE acc.id IS NULL
GROUP BY t.account_id, t.symbol;
```

## Monitoring and Logging

All delete operations are logged with context:

```python
logger.info(
    f"Soft deleted currency {symbol} for account {account_id} (has trade history)",
    account_id=account_id,
    symbol=symbol,
    action="soft_delete"
)

logger.info(
    f"Hard deleted currency {symbol} for account {account_id} (no trade history)",
    account_id=account_id,
    symbol=symbol,
    action="hard_delete"
)
```

Monitor ratio of soft vs hard deletes:
- High soft delete ratio → Users trading many currencies
- High hard delete ratio → Users experimenting with configurations

## Related Documentation

- [Add Currency Feature](./ADD_CURRENCY_FEATURE.md)
- [Database Schema](./DATABASE_SCHEMA.md)
- [API Documentation](./API.md)
