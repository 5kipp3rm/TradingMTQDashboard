# Add Currency Feature Implementation

## Date: December 28, 2025

## Overview

Implemented the ability to dynamically add new currency pairs to trading accounts through a modal interface. This allows users to expand their tradable currency pairs without manual database modifications.

## What Was Done

### 1. Created Add Currency Modal Component ✅

**File**: `dashboard/src/components/currencies/AddCurrencyModal.tsx`

**Features**:
- Full form for currency pair configuration
- Symbol selection (manual input + common pairs dropdown)
- Risk management settings (risk %, position size, SL/TP)
- Strategy configuration (type, timeframe, MA periods)
- Form validation (slow period > fast period, required fields)
- Enable/disable toggle for the currency
- Common currency pairs: EURUSD, GBPUSD, USDJPY, etc.

**Form Fields**:
```typescript
{
  symbol: string;              // Currency pair (e.g., EURUSD)
  enabled: boolean;            // Enable trading
  risk_percent: number;        // Risk per trade (0.1-10%)
  max_position_size: number;   // Max lots
  min_position_size: number;   // Min lots
  strategy_type: string;       // Strategy (simple_ma, rsi_divergence, etc.)
  timeframe: string;           // M1, M5, M15, M30, H1, H4, D1
  fast_period: number;         // Fast MA period
  slow_period: number;         // Slow MA period
  sl_pips: number;            // Stop loss in pips
  tp_pips: number;            // Take profit in pips
}
```

### 2. Updated Currencies Page ✅

**File**: `dashboard/src/pages/Currencies.tsx`

**Changes**:
1. **Added Imports**:
   ```typescript
   import { AddCurrencyModal } from "@/components/currencies/AddCurrencyModal";
   import { currenciesApi } from "@/lib/api";
   import { Plus } from "lucide-react";
   ```

2. **Added State**:
   ```typescript
   const [addCurrencyOpen, setAddCurrencyOpen] = useState(false);
   ```

3. **Added Handler**: `handleAddCurrency()` function that:
   - Creates global currency configuration via `currenciesApi.create()`
   - Updates per-account currency settings via `accountsApi.updateCurrency()`
   - Refreshes the currencies list
   - Shows success/error toast notifications
   - Handles duplicate currency errors gracefully

4. **Updated UI**:
   - Added "Add Currency" button next to "Save Changes"
   - Added modal at bottom of component
   - Button includes Plus icon

### 3. API Integration ✅

**Existing APIs Used**:
- `currenciesApi.create(currency)` - Creates global currency configuration
- `accountsApi.updateCurrency(accountId, symbol, config)` - Updates per-account settings
- `accountsApi.getCurrencies(accountId)` - Refreshes currency list

**Two-Step Process**:
1. **Global Configuration**: Creates the currency in the global currencies table (if doesn't exist)
2. **Per-Account Settings**: Links the currency to the specific account with custom settings

## User Flow

### Adding a New Currency

1. **Navigate to Currencies Page**
2. **Click "Add Currency" Button** (top-right, next to "Save Changes")
3. **Fill Out Modal Form**:
   - Enter or select currency symbol (e.g., EURUSD)
   - Configure risk settings (risk %, position sizes, SL/TP)
   - Configure strategy (type, timeframe, MA periods)
   - Toggle "Enable trading" checkbox
4. **Click "Add Currency"**
5. **System Actions**:
   - Creates global currency configuration
   - Links currency to current account
   - Refreshes the currencies list
   - Shows "Currency Added" success message
6. **New Currency Appears** in the list (can now toggle, edit, save)

### Form Validation

The modal validates:
- ✅ Symbol is required
- ✅ Slow period must be > fast period
- ✅ Stop loss and take profit must be > 0
- ✅ Fast period must be > 0

**Submit button is disabled** until all validations pass.

## UI Examples

### Add Currency Button
```
┌─────────────────────────────────────────────────────────┐
│ Trading Strategies                                      │
│ Configuring: My Demo Account                           │
│                                   [+ Add Currency] [Save Changes] │
└─────────────────────────────────────────────────────────┘
```

### Add Currency Modal
```
┌────────────────────────────────────────────────────────┐
│ + Add Currency Pair                            [X]     │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Currency Pair Symbol                                  │
│ [EURUSD_______________] [Common Pairs ▼]             │
│                                                        │
│ ☑ Enable trading for this currency pair              │
│                                                        │
│ ⚠️ Risk Management                                    │
│ Risk % per Trade        Max Position Size (lots)     │
│ [1.0___]               [0.1___]                       │
│                                                        │
│ Stop Loss (pips)       Take Profit (pips)            │
│ [50___]                [100___]                       │
│                                                        │
│ 📈 Strategy Configuration                             │
│ Strategy Type                                         │
│ [Simple MA Crossover_________________________]       │
│                                                        │
│ Timeframe              Fast MA Period                │
│ [5 Minutes ▼]         [10___]                        │
│                                                        │
│ Slow MA Period                                        │
│ [20___]                                               │
│                                                        │
│                              [Cancel] [Add Currency]  │
└────────────────────────────────────────────────────────┘
```

## Backend Requirements

The feature relies on existing backend endpoints:

### POST /currencies
Creates a global currency configuration:
```json
{
  "symbol": "EURUSD",
  "enabled": true,
  "risk_percent": 1.0,
  "max_position_size": 0.1,
  "min_position_size": 0.01,
  "strategy_type": "simple_ma",
  "timeframe": "M5",
  "fast_period": 10,
  "slow_period": 20,
  "sl_pips": 50,
  "tp_pips": 100,
  "cooldown_seconds": 300,
  "trade_on_signal_change": true,
  "allow_position_stacking": false,
  "max_positions_same_direction": 1,
  "max_total_positions": 5,
  "stacking_risk_multiplier": 1.0,
  "description": "EURUSD trading configuration"
}
```

### PUT /accounts/{account_id}/currencies/{symbol}
Updates per-account currency settings:
```json
{
  "symbol": "EURUSD",
  "enabled": true,
  "risk_percent": 1.0,
  "max_position_size": 0.1,
  "min_position_size": 0.01,
  "strategy_type": "simple_ma",
  "timeframe": "M5",
  "fast_period": 10,
  "slow_period": 20,
  "sl_pips": 50,
  "tp_pips": 100
}
```

## Error Handling

### Duplicate Currency
If currency already exists globally:
- **Error is ignored** (proceeds to update per-account settings)
- **User sees**: "Currency Added" success message

### API Failures
If global currency creation fails:
- **User sees**: Error toast with specific message
- **Process stops**: Per-account update is not attempted

If per-account update fails:
- **User sees**: Error toast with specific message
- **List not refreshed**: User can retry

## Common Currency Pairs Included

The modal includes a dropdown with 21 common forex pairs:

**Major Pairs**:
- EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD

**Cross Pairs**:
- EURJPY, GBPJPY, EURGBP, AUDJPY, EURAUD, EURCHF, AUDNZD
- NZDJPY, GBPAUD, GBPCAD, EURNZD, AUDCAD, GBPCHF, EURCAD

**Users can also manually type** any other currency pair not in the list.

## Default Values

When adding a new currency, sensible defaults are applied:

**Risk Management**:
- Risk percent: 1.0%
- Max position size: 0.1 lots
- Min position size: 0.01 lots
- Stop loss: 50 pips
- Take profit: 100 pips

**Strategy**:
- Strategy type: Simple MA Crossover
- Timeframe: M5 (5 minutes)
- Fast period: 10
- Slow period: 20

**Trading Rules** (auto-applied):
- Cooldown: 300 seconds
- Trade on signal change: true
- Position stacking: false
- Max positions same direction: 1
- Max total positions: 5
- Stacking risk multiplier: 1.0

## Files Modified

1. ✅ `dashboard/src/components/currencies/AddCurrencyModal.tsx` (NEW - 290 lines)
2. ✅ `dashboard/src/pages/Currencies.tsx` (MODIFIED - added state, handler, button, modal)

## Testing

### Manual Testing Steps

1. **Open Currencies Page**
2. **Click "Add Currency"**
3. **Try Empty Form**:
   - Verify "Add Currency" button is disabled
4. **Fill Form with Valid Data**:
   - Symbol: GBPJPY
   - Risk %: 1.5
   - Strategy: Trend Following
   - Verify button is enabled
5. **Set Slow Period = Fast Period**:
   - Verify validation error appears
   - Verify button is disabled
6. **Fix Validation**:
   - Set slow period > fast period
7. **Submit Form**:
   - Verify success toast appears
   - Verify GBPJPY appears in currencies list
   - Verify modal closes
8. **Try Adding Duplicate**:
   - Add same currency again
   - Verify it still works (updates existing)
9. **Try Common Pairs Dropdown**:
   - Select EURUSD from dropdown
   - Verify symbol field updates

## Benefits

✅ **User-Friendly**: No need to manually edit database or config files
✅ **Dynamic**: Add currencies on-the-fly without server restart
✅ **Validated**: Form prevents invalid configurations
✅ **Flexible**: Support both common pairs and custom symbols
✅ **Per-Account**: Each account can have different currency settings
✅ **Global + Local**: Maintains both global and per-account configurations
✅ **Error Handling**: Graceful handling of duplicates and errors

## Future Enhancements

Potential improvements:

1. **Bulk Import**: Import multiple currencies from CSV/JSON
2. **Currency Templates**: Save/load currency configuration presets
3. **Delete Currency**: Add button to remove currency from account
4. **Currency Search**: Filter currencies list by symbol
5. **Currency Groups**: Group currencies by type (majors, crosses, exotics)
6. **Copy Settings**: Copy settings from one currency to another
7. **Market Hours**: Add trading hours configuration per currency

## Related Documentation

- [Unified Logger Implementation](./UNIFIED_LOGGER_IMPLEMENTATION_SUMMARY.md)
- [Correlation ID Implementation](./CORRELATION_ID_IMPLEMENTATION.md)
- [Account Broker Validation Fix](./ACCOUNT_BROKER_VALIDATION_FIX.md)

## Phase 2: Database-Backed Currency List (COMPLETED)

### Overview

Instead of hardcoding 21 currency pairs in the AddCurrencyModal, the system now loads available currencies dynamically from a master database table. This allows:

- Dynamic currency management (60+ pairs included)
- Currency categorization (major, cross, exotic, commodity, crypto, index)
- Rich metadata (pip value, spread, trading hours, descriptions)
- Easy addition of new currency pairs without code changes
- Filtering by category and active status

### Database Schema

**Table**: `available_currencies`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| symbol | VARCHAR(20) | Currency pair symbol (e.g., EURUSD) |
| description | VARCHAR(200) | Human-readable description |
| category | ENUM | Category: major, cross, exotic, commodity, crypto, index |
| base_currency | VARCHAR(10) | Base currency code (e.g., EUR) |
| quote_currency | VARCHAR(10) | Quote currency code (e.g., USD) |
| pip_value | DECIMAL(10,5) | Pip value for position sizing |
| decimal_places | INTEGER | Number of decimal places for pricing |
| min_lot_size | DECIMAL(10,2) | Minimum lot size |
| max_lot_size | DECIMAL(10,2) | Maximum lot size |
| typical_spread | DECIMAL(10,5) | Typical spread in pips |
| is_active | BOOLEAN | Whether currency is active for trading |
| trading_hours_start | VARCHAR(5) | Trading hours start (HH:MM) |
| trading_hours_end | VARCHAR(5) | Trading hours end (HH:MM) |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Indices**:
- `symbol` (unique)
- `category`
- `is_active`

### Implementation Details

#### 1. Database Model

**File**: [src/database/models.py:608-689](src/database/models.py#L608-L689)

```python
class CurrencyCategory(enum.Enum):
    MAJOR = "major"
    CROSS = "cross"
    EXOTIC = "exotic"
    COMMODITY = "commodity"
    CRYPTO = "crypto"
    INDEX = "index"

class AvailableCurrency(Base):
    __tablename__ = 'available_currencies'
    # ... fields as described in schema above
```

#### 2. Database Migration

**File**: [alembic/versions/b7c8e9f1d2a3_add_available_currencies_table.py](alembic/versions/b7c8e9f1d2a3_add_available_currencies_table.py)

Creates the table with proper indices and enum type.

#### 3. Seed Script

**File**: [scripts/seed_available_currencies.py](scripts/seed_available_currencies.py)

Populates database with 60+ currency pairs:
- 7 major pairs
- 14 cross pairs
- 11 exotic pairs
- 6 commodity pairs
- 2 crypto pairs
- 6 index pairs

#### 4. API Endpoint

**File**: [src/api/routes/currencies.py:369-422](src/api/routes/currencies.py#L369-L422)

**Endpoint**: `GET /available`

**Query Parameters**:
- `category` (optional): Filter by category (major, cross, exotic, etc.)
- `active_only` (optional, default=true): Show only active currencies

**Response**:
```json
{
  "currencies": [
    {
      "id": 1,
      "symbol": "EURUSD",
      "description": "Euro vs US Dollar",
      "category": "major",
      "base_currency": "EUR",
      "quote_currency": "USD",
      "pip_value": 0.0001,
      "decimal_places": 5,
      "min_lot_size": 0.01,
      "max_lot_size": 100.0,
      "typical_spread": 0.8,
      "is_active": true,
      "trading_hours_start": null,
      "trading_hours_end": null
    }
  ],
  "total": 60
}
```

#### 5. Frontend API Client

**File**: [dashboard/src/lib/api.ts:210-215](dashboard/src/lib/api.ts#L210-L215)

Added `getAvailable()` method to `currenciesApi`:

```typescript
currenciesApi.getAvailable({
  category?: string,
  active_only?: boolean
})
```

#### 6. Updated AddCurrencyModal

**File**: [dashboard/src/components/currencies/AddCurrencyModal.tsx](dashboard/src/components/currencies/AddCurrencyModal.tsx)

**Changes**:
- Removed hardcoded `commonCurrencyPairs` array
- Added category selector dropdown (All, Major, Cross, Exotic, Commodity, Crypto, Index)
- Added `useEffect` to load currencies from API when modal opens or category changes
- Added loading state with spinner
- Updated currency dropdown to show filtered currencies based on selected category
- Shows currency descriptions in dropdown
- Shows count of available currencies (filtered by category)

**Features**:
- **Category-based filtering**: Select a category first to narrow down options
- Dynamic loading of 60+ currency pairs
- Real-time filtering when category changes
- Currency descriptions displayed in dropdown
- Loading indicator while fetching
- Empty state when no currencies match filter
- Fallback to manual input if API fails
- Responsive layout with improved spacing

### Setup Instructions

#### Option 1: Using Alembic Migration (Recommended)

```bash
# Run migration
python -m alembic upgrade head

# Seed the database
python scripts/seed_available_currencies.py
```

#### Option 2: Using Direct SQL (Fallback)

```bash
# Create table directly
python scripts/create_available_currencies_table.py

# Seed the database
python scripts/seed_available_currencies.py
```

#### Verify Setup

```bash
# Check table was created
sqlite3 trading_bot.db "SELECT COUNT(*) FROM available_currencies;"

# Expected output: 60+

# Check categories
sqlite3 trading_bot.db "SELECT category, COUNT(*) FROM available_currencies GROUP BY category;"
```

### Currency Pairs Included

**Major Pairs (7)**:
- EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD

**Cross Pairs (14)**:
- EURJPY, GBPJPY, EURGBP, AUDJPY, EURAUD, EURCHF, AUDNZD, NZDJPY, GBPAUD, GBPCAD, EURNZD, AUDCAD, GBPCHF, EURCAD

**Exotic Pairs (11)**:
- USDTRY, USDZAR, USDMXN, USDSEK, USDNOK, USDDKK, USDPLN, USDHUF, USDCZK, USDSGD, USDHKD

**Commodity Pairs (6)**:
- XAUUSD (Gold), XAGUSD (Silver), XPTUSD (Platinum), XPDUSD (Palladium), USOIL (WTI), UKOIL (Brent)

**Crypto Pairs (2)**:
- BTCUSD (Bitcoin), ETHUSD (Ethereum)

**Index Pairs (6)**:
- US30 (Dow Jones), US500 (S&P 500), NAS100 (NASDAQ), GER40 (DAX), UK100 (FTSE), JPN225 (Nikkei)

### Benefits

✅ **Scalable**: Add new currencies without modifying frontend code
✅ **Rich Metadata**: Includes pip values, spreads, lot sizes, descriptions
✅ **Categorized**: Filter by major, cross, exotic, commodity, crypto, index
✅ **Flexible**: Can activate/deactivate currencies via database
✅ **Comprehensive**: 60+ currency pairs vs 21 hardcoded
✅ **Future-Proof**: Easy to add more pairs or metadata fields

### Future Enhancements

1. **Admin UI**: Web interface to add/edit/remove currency pairs
2. **Broker Integration**: Sync available currencies from broker API
3. **Custom Pairs**: Allow users to add broker-specific currency pairs
4. **Metadata Updates**: Automatically update spreads and pip values from market data
5. **Trading Sessions**: Show active trading sessions per currency
6. **Historical Data**: Link to market data for backtesting

## Status

✅ **PHASE 1 COMPLETE**: Add Currency Modal
✅ **PHASE 2 COMPLETE**: Database-Backed Currency List

Users can now:
1. Dynamically add currency pairs to their trading accounts
2. Choose from 60+ currency pairs loaded from database
3. See currency categories and metadata
4. Benefit from a scalable, maintainable currency management system
