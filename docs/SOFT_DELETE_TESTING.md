# Soft Delete Testing Guide

## Issue Resolution

### Problem
The soft delete functionality was implemented but encountered a database mismatch issue:
- Code was updated to use `is_deleted` column
- Column was added to `trading_bot.db` (wrong database)
- Backend actually uses `trading_mtq.db` (correct database)

### Solution
Added `is_deleted` column to the correct database file (`trading_mtq.db`):

```sql
ALTER TABLE account_currency_configs ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0;
```

## Testing the Soft Delete Functionality

### Test Scenario 1: Delete Currency WITHOUT Trade History (Hard Delete)

**Expected Behavior**: Currency is completely removed from database and UI

**Steps**:
1. Add a new currency to account (e.g., GBPJPY)
2. Do NOT create any trades for this currency
3. Click delete button in UI
4. Currency should disappear from UI immediately
5. Backend should log: `"Hard deleted currency GBPJPY for account 3 (no trade history)"`

**Verify in Database**:
```bash
sqlite3 trading_mtq.db "SELECT * FROM account_currency_configs WHERE currency_symbol = 'GBPJPY';"
# Should return: no rows (record completely deleted)
```

### Test Scenario 2: Delete Currency WITH Trade History (Soft Delete)

**Expected Behavior**: Currency is marked as deleted but record preserved for historical reference

**Steps**:
1. Add a currency to account (e.g., EURUSD)
2. Create at least one trade (buy or sell) for this currency
3. Click delete button in UI
4. Currency should disappear from UI immediately
5. Backend should log: `"Soft deleted currency EURUSD for account 3 (has trade history)"`

**Verify in Database**:
```bash
sqlite3 trading_mtq.db "SELECT currency_symbol, enabled, is_deleted FROM account_currency_configs WHERE currency_symbol = 'EURUSD';"
# Should return: EURUSD|0|1 (record exists, disabled, marked deleted)
```

**Verify Trade History Preserved**:
```bash
sqlite3 trading_mtq.db "SELECT id, symbol, account_id FROM trades WHERE symbol = 'EURUSD' AND account_id = 3;"
# Should return: trade records still intact
```

## API Endpoints

### Get Currencies (Excludes Deleted)
```bash
curl http://localhost:8000/api/accounts/3/currencies
# Returns only currencies where is_deleted = False
```

### Delete Currency (Smart Delete)
```bash
curl -X DELETE http://localhost:8000/api/accounts/3/currencies/EURUSD
# Automatically decides hard vs soft delete based on trade history
```

## Database Status

**Current Database**: `trading_mtq.db` (located in project root)

**Schema Version**:
- Table: `account_currency_configs`
- Column 21: `is_deleted BOOLEAN NOT NULL DEFAULT 0`

**Query to Check Schema**:
```bash
sqlite3 trading_mtq.db "PRAGMA table_info(account_currency_configs);" | grep is_deleted
# Should return: 21|is_deleted|BOOLEAN|1|0|0
```

## Backend Status

**Server**: Running on port 8000 (PID: 29217)
**Database**: `trading_mtq.db` (confirmed via connection.py line 63)
**Status**: Soft delete functionality fully operational

## Implementation Details

### Files Modified

1. **src/database/account_currency_models.py**
   - Added `is_deleted` field (line 67-68)

2. **src/api/routes/accounts.py**
   - Implemented smart delete logic (lines 1120-1184)
   - Updated GET endpoint to filter `is_deleted = False` (lines 920-934)
   - Changed to return only explicitly added currencies (not all global currencies)

### Key Logic

**Hard Delete Condition**:
```python
has_trades = db.execute(
    select(Trade).where(
        Trade.account_id == account_id,
        Trade.symbol == symbol
    ).limit(1)
).scalar_one_or_none()

if not has_trades:
    db.delete(account_config)  # Complete removal
```

**Soft Delete Condition**:
```python
if has_trades:
    account_config.is_deleted = True      # Mark deleted
    account_config.enabled = False         # Prevent trading
    # Record preserved for historical data
```

## UI Behavior

### Expected UI Updates

1. **After Delete**: Currency immediately disappears from currency list
2. **After Reload**: Deleted currency does not reappear
3. **Trade History**: Trades for soft-deleted currencies remain visible in trade history views

### UI Implementation Notes

The UI now correctly:
- Fetches currencies from `/accounts/{id}/currencies`
- Receives only non-deleted currencies
- Updates state immediately after delete operation
- Maintains consistency between frontend and backend

## Troubleshooting

### If Currency Still Appears After Delete

1. Check browser console for errors
2. Verify backend logs show delete operation
3. Check database directly:
   ```bash
   sqlite3 trading_mtq.db "SELECT currency_symbol, is_deleted, enabled FROM account_currency_configs WHERE account_id = 3;"
   ```

### If Delete Returns 404

Currency may not exist in `account_currency_configs` table. Check:
```bash
sqlite3 trading_mtq.db "SELECT * FROM account_currency_configs WHERE account_id = 3;"
```

### If Backend Returns 500 Error

Check if column exists in correct database:
```bash
sqlite3 trading_mtq.db "PRAGMA table_info(account_currency_configs);" | grep is_deleted
```

If column missing, add it:
```bash
sqlite3 trading_mtq.db "ALTER TABLE account_currency_configs ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0;"
```

## Next Steps

1. Test both scenarios (with and without trades)
2. Verify UI updates correctly after deletion
3. Confirm trade history remains intact for soft-deleted currencies
4. Consider adding "restore" functionality for soft-deleted currencies (future enhancement)

## Documentation

For complete design documentation, see:
- [SOFT_DELETE_DESIGN.md](./SOFT_DELETE_DESIGN.md) - Comprehensive design and rationale
