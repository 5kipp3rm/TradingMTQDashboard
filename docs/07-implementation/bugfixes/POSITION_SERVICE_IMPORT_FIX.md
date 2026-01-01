# Position Service Import Scope Fix

## Issue

When selecting a specific account in the dashboard, the positions API failed with:

```
ERROR Error getting open positions: cannot access local variable 'TradingAccount' where it is not associated with a value
Traceback (most recent call last):
  File ".../src/services/position_service.py", line 761, in get_open_positions
    account = db.get(TradingAccount, account_id)
                     ^^^^^^^^^^^^^^
```

## Root Cause

The `get_open_positions` method had a **variable scoping issue** caused by a shadowing import:

```python
# Module-level import at line 26
from src.database.models import TradingAccount

# ...

async def get_open_positions(self, account_id: Optional[int], db: Session, ...):
    try:
        # If no account_id specified, get positions from all active accounts
        if account_id is None:
            from sqlalchemy import select
            from src.database import TradingAccount  # ❌ LOCAL IMPORT - SHADOWS MODULE-LEVEL

            # Get all active accounts
            stmt = select(TradingAccount).where(TradingAccount.is_active == True)
            # ... code using TradingAccount within if block
            return all_positions

        # Single account mode
        # Get account from database
        account = db.get(TradingAccount, account_id)  # ❌ ERROR: TradingAccount not in scope!
```

### Why This Failed

1. **Line 723**: Local import `from src.database import TradingAccount` creates a **new variable** `TradingAccount` that only exists within the `if account_id is None:` block
2. **Line 26**: The module-level import is **shadowed** by the local import inside the if block
3. **Line 761**: When code execution reaches this line (outside the if block), Python thinks `TradingAccount` was defined in the if block but never assigned before this point
4. **Result**: `UnboundLocalError` - "cannot access local variable 'TradingAccount' where it is not associated with a value"

## Fix Applied

**File**: [src/services/position_service.py](../src/services/position_service.py)

**Solution**: Remove the local import and rely on the module-level import

```python
# Module-level import at line 26 (unchanged)
from src.database.models import TradingAccount

# ...

async def get_open_positions(self, account_id: Optional[int], db: Session, ...):
    try:
        # If no account_id specified, get positions from all active accounts
        if account_id is None:
            from sqlalchemy import select
            # ✅ REMOVED: from src.database import TradingAccount

            # Get all active accounts - uses module-level TradingAccount
            stmt = select(TradingAccount).where(TradingAccount.is_active == True)
            # ... code using TradingAccount within if block
            return all_positions

        # Single account mode
        # Get account from database - now uses module-level TradingAccount
        account = db.get(TradingAccount, account_id)  # ✅ WORKS: Uses module-level import
```

## Testing

### Before Fix
```bash
curl 'http://localhost:8000/api/positions/open?account_id=1'
# Result: 500 Internal Server Error
# Error: cannot access local variable 'TradingAccount' where it is not associated with a value
```

### After Fix
```bash
curl 'http://localhost:8000/api/positions/open?account_id=1'
# Result: []  (empty array - correct response when no positions exist)
```

### Test Cases Verified

1. ✅ **All accounts** (`account_id=None`): Returns positions from all active accounts
2. ✅ **Specific account** (`account_id=1`): Returns positions for that account
3. ✅ **No connection**: Returns empty array instead of crashing
4. ✅ **Dashboard integration**: Account selection dropdown works correctly

## Python Scope Rules Explanation

This issue demonstrates Python's **LEGB (Local, Enclosing, Global, Built-in)** scope rule:

```python
# Global scope
from module import Variable  # Variable available globally

def function():
    if condition:
        from module import Variable  # Creates LOCAL variable
        # Variable is LOCAL to this if block

    # Outside if block, Python sees Variable was assigned locally (in if block)
    # but hasn't been assigned in this execution path
    use(Variable)  # ❌ UnboundLocalError
```

### Correct Pattern

```python
# Global scope
from module import Variable  # Variable available globally

def function():
    if condition:
        # Use the global Variable directly
        stmt = select(Variable)

    # Variable is still available from global scope
    use(Variable)  # ✅ Works correctly
```

## Related Issues

This same pattern could cause issues in other methods if local imports shadow module-level imports. Consider auditing for similar patterns:

```bash
# Search for local imports that might shadow module-level imports
grep -r "from.*import.*TradingAccount" src/
```

## Best Practices

1. **Prefer module-level imports** over function-level imports
2. **Avoid shadowing imports** - don't re-import at function/block scope
3. **Use function-level imports only** when:
   - Avoiding circular imports
   - Lazy loading for performance
   - Import is truly only needed in that scope
4. **Never shadow module-level imports** with local imports

## Files Modified

- [src/services/position_service.py](../src/services/position_service.py) - Line 723: Removed local `TradingAccount` import

## Impact

- Dashboard account selector now works correctly
- Positions API no longer crashes when filtering by account
- No functional changes to the multi-account or single-account position fetching logic
- Only fixed the variable scoping issue

## Related Documentation

- [Dashboard API Fixes](./DASHBOARD_API_FIXES_2025-12-28.md) - Previous fix for dashboard API endpoints
- [Accounts UI Bug Fixes](./ACCOUNTS_UI_BUG_FIXES_2025-12-28.md) - Initial accounts page fixes
