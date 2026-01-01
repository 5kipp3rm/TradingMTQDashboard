# Trading Account Fields Guide

Complete reference for adding MT5 trading accounts to TradingMTQ.

## Quick Start

### Add a Demo Account (Fastest)
```bash
python scripts/add_account.py --demo
```

### Add a Live Account (Interactive)
```bash
python scripts/add_account.py --live
```

### Interactive Mode (Full Control)
```bash
python scripts/add_account.py --interactive
```

### List All Accounts
```bash
python scripts/add_account.py --list
```

---

## Field Reference

### ✅ Required Fields

#### 1. `account_number` (integer, unique)
- **What:** Your MT5 account login number
- **Example:** `12345678`
- **Purpose:** Unique identifier for the MT5 account
- **Validation:** Must be unique across all accounts
- **Where to find:** MT5 platform → Tools → Options → Server tab

#### 2. `account_name` (string, max 100 chars)
- **What:** Human-readable name for the account
- **Example:** `"Main Trading Account"`, `"EUR/USD Scalping"`, `"Demo ICMarkets"`
- **Purpose:** Displayed in dashboard dropdowns and account selector
- **Best practice:** Use descriptive names that help you identify the account's purpose
- **Used in:** Dashboard navigation, account selector, reports

#### 3. `broker` (string, max 100 chars)
- **What:** Name of your forex broker
- **Example:** `"IC Markets"`, `"Pepperstone"`, `"FTMO"`, `"XM"`, `"Exness"`
- **Purpose:** Groups accounts by broker in reports and analytics
- **Best practice:** Use consistent naming (e.g., always "IC Markets", not "ICMarkets")
- **Used in:** Account filtering, broker comparison reports

#### 4. `server` (string, max 100 chars)
- **What:** MT5 server address for connection
- **Example:**
  - Demo: `"ICMarkets-Demo"`, `"Pepperstone-Demo01"`
  - Live: `"ICMarkets-Live03"`, `"Pepperstone-Live01"`
- **Purpose:** Required by MT5 API for establishing connection
- **Where to find:** MT5 platform → File → Login to Trade Account → Server dropdown
- **Important:** Must match exactly as shown in MT5

#### 5. `login` (integer)
- **What:** MT5 login number (authentication credential)
- **Example:** `12345678`
- **Purpose:** Used by MT5 API for authentication
- **Note:** Usually same as `account_number`, but can differ in some broker setups
- **Default:** If not provided, uses `account_number`

---

### 🔧 Optional Fields (With Defaults)

#### 6. `is_active` (boolean, default: `true`)
- **What:** Whether the account is enabled for trading operations
- **Values:** `true` (enabled) or `false` (disabled)
- **Purpose:** Temporarily disable accounts without deleting them
- **Use cases:**
  - Pause trading during vacation
  - Disable underperforming accounts
  - Stop trading on accounts pending review
- **Effect when `false`:**
  - Account hidden from active account lists
  - Cannot open new positions
  - Existing positions remain visible
  - Historical data preserved

#### 7. `is_default` (boolean, default: `false`)
- **What:** Marks this as the default account
- **Values:** `true` or `false`
- **Purpose:** Dashboard auto-selects this account on page load
- **Best practice:** Set only ONE account as default
- **Use case:** Your primary trading account
- **Effect:**
  - Pre-selected in account dropdown
  - Used for quick access features
  - Dashboard loads this account's data first

#### 8. `is_demo` (boolean, default: `true`)
- **What:** Account type indicator
- **Values:**
  - `true` = Demo/Paper trading account
  - `false` = Live/Real money account
- **Purpose:** Safety feature to differentiate demo from live accounts
- **Display:**
  - `true` → Shows "🟢 DEMO" badge
  - `false` → Shows "🔴 LIVE" badge with red color
- **Best practice:** Double-check this field when adding live accounts!
- **Impact:**
  - Visual indicators in dashboard
  - Filter accounts by type in reports
  - Extra confirmation prompts for live accounts

#### 9. `password_encrypted` (string, max 255 chars, nullable)
- **What:** Encrypted MT5 password for auto-login
- **Example:** Encrypted string (implementation-specific)
- **Purpose:** Enable automatic MT5 connection without manual password entry
- **Security notes:**
  - ⚠️ Should be encrypted in production
  - ⚠️ Never store plain text passwords
  - Optional: Can be left `null` for manual login
- **When to use:**
  - Automated trading systems
  - Headless server deployments
  - When running as a service
- **When to skip:**
  - Development environments
  - Manual trading setups
  - Security-sensitive scenarios

#### 10. `initial_balance` (decimal, nullable)
- **What:** Starting account balance when account was opened
- **Example:** `10000.00` (for $10,000)
- **Purpose:** Calculate performance metrics:
  - ROI (Return on Investment)
  - Absolute drawdown
  - Relative drawdown percentage
  - Account growth rate
- **Format:** Numeric with 2 decimal places
- **Optional:** Can be added later if unknown initially
- **Use in reports:**
  - "Account started with $10,000"
  - "Current balance: $12,500 (+25% ROI)"

#### 11. `currency` (string, max 10 chars, default: `"USD"`)
- **What:** Account base currency
- **Example:** `"USD"`, `"EUR"`, `"GBP"`, `"AUD"`, `"JPY"`
- **Purpose:**
  - Currency conversion in aggregated reports
  - Accurate multi-currency account comparison
  - Display currency symbols correctly
- **Important:** Must match MT5 account currency
- **Multi-account impact:**
  - Aggregated reports convert all to USD
  - Allows comparison across different currency accounts

#### 12. `description` (text, nullable)
- **What:** Free-text notes about the account
- **Example:**
  - `"Conservative EUR/USD scalping strategy"`
  - `"High-frequency trading on London session"`
  - `"Prop firm challenge account - funded by FTMO"`
  - `"Backup account - use only when primary is down"`
- **Character limit:** No strict limit (text field)
- **Purpose:**
  - Document trading strategy
  - Add reminders or restrictions
  - Note account purpose or goals
- **Use cases:**
  - Strategy documentation
  - Risk management notes
  - Account-specific rules
  - Performance goals

---

### 🤖 Auto-Generated Fields

#### 13. `id` (integer, auto-increment)
- **What:** Internal database ID
- **Generated:** Automatically by database
- **Purpose:** Primary key for database operations
- **Usage:** Used in API calls (`account_id=1`)
- **Note:** Never set this manually

#### 14. `created_at` (datetime, auto)
- **What:** Timestamp when account was added to database
- **Generated:** Automatically on INSERT
- **Format:** `YYYY-MM-DD HH:MM:SS.ffffff`
- **Purpose:** Audit trail and account history
- **Timezone:** UTC
- **Example:** `2025-12-15 14:23:45.123456`

#### 15. `updated_at` (datetime, auto)
- **What:** Timestamp of last account modification
- **Generated:** Automatically on UPDATE
- **Updated when:** Any field changes
- **Purpose:** Track when settings were last changed
- **Usage:** "Account settings last updated 2 days ago"

#### 16. `last_connected` (datetime, nullable, auto)
- **What:** Last successful MT5 connection timestamp
- **Generated:** Automatically by session manager
- **Updated when:** Successful MT5 login
- **Purpose:**
  - Monitor connection activity
  - Detect inactive accounts
  - Track connection frequency
- **Usage:** "Last connected 15 minutes ago"

---

## Field Combinations & Examples

### Example 1: Basic Demo Account
```python
{
    "account_number": 12345678,
    "account_name": "My First Demo Account",
    "broker": "IC Markets",
    "server": "ICMarkets-Demo",
    "login": 12345678,
    "is_demo": True,      # Demo account
    "is_active": True,    # Active
    "is_default": True,   # Default account
    "currency": "USD"
}
```

### Example 2: Live Account with Tracking
```python
{
    "account_number": 87654321,
    "account_name": "Live EUR/USD Scalping",
    "broker": "Pepperstone",
    "server": "Pepperstone-Live03",
    "login": 87654321,
    "is_demo": False,           # LIVE account
    "is_active": True,
    "is_default": False,
    "initial_balance": 5000.00, # Starting balance
    "currency": "USD",
    "description": "Conservative scalping strategy on EUR/USD, M5 timeframe"
}
```

### Example 3: Prop Firm Challenge Account
```python
{
    "account_number": 11223344,
    "account_name": "FTMO Challenge #1",
    "broker": "FTMO",
    "server": "FTMO-Server3",
    "login": 11223344,
    "is_demo": True,              # Challenge accounts are demo
    "is_active": True,
    "initial_balance": 100000.00, # Challenge size
    "currency": "USD",
    "description": "FTMO $100k challenge - Phase 1. Max daily loss: 5%. Target: 10% in 30 days"
}
```

### Example 4: Backup Account (Inactive)
```python
{
    "account_number": 99887766,
    "account_name": "Backup Account",
    "broker": "XM",
    "server": "XM-Real3",
    "login": 99887766,
    "is_demo": False,
    "is_active": False,    # Disabled - only for emergencies
    "is_default": False,
    "currency": "EUR",
    "description": "Emergency backup account - DO NOT USE unless primary account is down"
}
```

---

## Using the Script

### Interactive Mode - Full Walkthrough
```bash
$ python scripts/add_account.py --interactive

=== Add Trading Account ===

MT5 Account Number: 12345678
Account Name (e.g., 'Main Trading Account'): My Trading Account
Broker Name (e.g., 'IC Markets'): IC Markets
MT5 Server (e.g., 'ICMarkets-Demo'): ICMarkets-Demo
Login Number (default: 12345678): [press Enter]
Is this a demo account? (y/n, default: y): y
Activate account? (y/n, default: y): y
Set as default account? (y/n, default: n): y
Initial Balance (optional, e.g., 10000): 10000
Currency (default: USD): USD
Description (optional): My first trading account

✅ Account created successfully!
   ID: 1
   Account Number: 12345678
   Name: My Trading Account
   Broker: IC Markets
   Server: ICMarkets-Demo
   Type: DEMO
   Active: True
   Default: True
   Initial Balance: 10000.00 USD
```

### Demo Account - One Command
```bash
$ python scripts/add_account.py --demo

✅ Account created successfully!
   ID: 1
   Account Number: 12345678
   Name: Demo Account
   Broker: Demo Broker
   Server: DemoServer-MT5
   Type: DEMO
   Active: True
   Default: True
   Initial Balance: 10000.00 USD
```

### Live Account - Safety Prompts
```bash
$ python scripts/add_account.py --live

=== Add LIVE Trading Account ===
⚠️  WARNING: This will add a LIVE trading account!

Are you sure you want to add a LIVE account? (yes/no): yes
MT5 Account Number: 87654321
Account Name: Live Account
Broker Name: Pepperstone
MT5 Server: Pepperstone-Live03
...
```

### List All Accounts
```bash
$ python scripts/add_account.py --list

=== Trading Accounts (3) ===

ID: 1 | 12345678 | Demo Account
  Broker: Demo Broker | Server: DemoServer-MT5
  Type: DEMO | Status: ✓ ACTIVE [DEFAULT]
  Balance: 10000.00 USD

ID: 2 | 87654321 | Live EUR/USD Scalping
  Broker: Pepperstone | Server: Pepperstone-Live03
  Type: LIVE | Status: ✓ ACTIVE
  Balance: 5000.00 USD

ID: 3 | 99887766 | Backup Account
  Broker: XM | Server: XM-Real3
  Type: LIVE | Status: ✗ INACTIVE
  Balance: 2000.00 EUR
```

---

## API Usage

### Get Open Positions
```bash
curl 'http://localhost:8000/api/positions/open?account_id=1'
```

### Preview Position
```bash
curl -X POST 'http://localhost:8000/api/positions/preview' \
  -H 'Content-Type: application/json' \
  -d '{
    "account_id": 1,
    "symbol": "EURUSD",
    "order_type": "BUY",
    "volume": 0.1,
    "stop_loss": 1.0850,
    "take_profit": 1.0950
  }'
```

### Open Position
```bash
curl -X POST 'http://localhost:8000/api/positions/open' \
  -H 'Content-Type: application/json' \
  -d '{
    "account_id": 1,
    "symbol": "EURUSD",
    "order_type": "BUY",
    "volume": 0.1,
    "stop_loss": 1.0850,
    "take_profit": 1.0950,
    "comment": "Test position"
  }'
```

---

## Common Questions

### Q: Can I have multiple accounts with the same account_number?
**A:** No. `account_number` must be unique across all accounts.

### Q: What happens if I set multiple accounts as default?
**A:** Only the most recently set account will be treated as default. Best practice: keep only one account as default.

### Q: Can I change account fields after creation?
**A:** Yes, all fields except `id` and `created_at` can be updated. Use the accounts API or modify directly in the database.

### Q: Should I store passwords in the database?
**A:** For development: optional. For production: only if properly encrypted. Consider using environment variables or secure vault instead.

### Q: How do I delete an account?
**A:** Instead of deleting, set `is_active=false`. This preserves historical data while disabling the account.

### Q: Can I import accounts from a CSV file?
**A:** Not yet implemented. You can modify `scripts/add_account.py` to add CSV import functionality.

### Q: What's the difference between account_number and login?
**A:** Usually they're the same. Some brokers use different values for account identification vs. authentication. When in doubt, use the same value for both.

---

## Troubleshooting

### Error: "Account already exists"
- Check if account_number is already in database
- Use `--list` to see existing accounts
- Use a different account_number or update the existing account

### Error: "Database not initialized"
- Ensure server is running: `uvicorn src.api.app:app`
- Server should call `init_db()` on startup
- Check server logs for initialization errors

### Error: "Invalid server name"
- Verify server name matches exactly as shown in MT5
- Check for typos or extra spaces
- Server names are case-sensitive

---

## Next Steps

1. **Add your accounts** using the script
2. **Connect to MT5** via the accounts page in dashboard
3. **Open positions** using the positions page
4. **Monitor performance** in the analytics dashboard

For more information:
- [Position Execution Guide](POSITION_EXECUTION_GUIDE.md)
- [Multi-Account Setup](MULTI_ACCOUNT_SETUP.md)
- [API Documentation](http://localhost:8000/api/docs)
