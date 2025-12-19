# Phase 4 Worker Account Configuration

This directory contains YAML configuration files for Phase 4 multi-account trading.

## Quick Start

### 1. Copy Example Files

```bash
# Copy and rename for your accounts
cp account-001.yml.example account-5012345678.yml
cp account-002.yml.example account-5098765432.yml
```

**Important**: Use your actual MT5 login number in the filename!

### 2. Edit Your Configuration Files

Open each file and update:

```yaml
account_id: "account-5012345678"       # Match filename
login: 5012345678                      # Your actual login
password: "your_actual_password"       # Your actual password
server: "YourBroker-Demo"              # Your broker's server
```

### 3. Enable/Disable Currency Pairs

```yaml
currencies:
  - symbol: "EURUSD"
    enabled: true                      # Set to false to disable

  - symbol: "GBPUSD"
    enabled: false                     # Disabled - won't trade
```

### 4. Start Trading

```bash
# Start API server
./venv/bin/tradingmtq serve

# Open dashboard
open http://localhost:8000

# Go to Accounts page and click "Connect"
```

## File Structure

```
config/accounts/
├── README.md                          # This file
├── default.yml                        # Default settings for all accounts
├── account-001.yml.example            # Example: Aggressive trading
├── account-002.yml.example            # Example: Conservative trading
├── account-5012345678.yml             # Your actual config (create from example)
└── account-5098765432.yml             # Your actual config (create from example)
```

## Configuration Hierarchy

Settings cascade in this order:

1. **default.yml** - Base defaults for all accounts
2. **account-{login}.yml** - Account-specific overrides
3. **Currency config** - Per-pair overrides within account file

Example:
```yaml
# default.yml
default_risk:
  risk_percent: 1.0                    # Base default

# account-5012345678.yml
risk:
  risk_percent: 0.5                    # Overrides default

currencies:
  - symbol: "EURUSD"
    risk:
      risk_percent: 0.25               # Overrides account setting for EURUSD only
```

## Account Naming Convention

**Format**: `account-{LOGIN_NUMBER}.yml`

Examples:
- Login `5012345678` → `account-5012345678.yml`
- Login `123456` → `account-123456.yml`
- Login `987654321` → `account-987654321.yml`

## Required Settings

Every account configuration MUST have:

```yaml
account_id: "account-{login}"          # Unique ID
login: {your_login}                    # MT5 login number
password: "your_password"              # MT5 password
server: "Broker-Server"                # Broker server name
platform_type: "MT5"                   # MT5 or MT4
portable: true                         # REQUIRED for multi-instance
```

## Risk Management Levels

### Aggressive (Example: account-001.yml.example)
- Risk: 1% per trade
- Max positions: 3-5 per pair
- Max trades: 15 total
- Timeframe: M5 (fast)

### Conservative (Example: account-002.yml.example)
- Risk: 0.5% per trade
- Max positions: 2-3 per pair
- Max trades: 10 total
- Timeframe: M15 (slower)

### Custom
Create your own by adjusting:
- `risk_percent` - How much to risk per trade
- `max_positions` - Positions per currency pair
- `max_concurrent_trades` - Total positions across all pairs
- `stop_loss_pips` / `take_profit_pips` - SL/TP distance

## Available Currency Pairs

Major pairs (low spread):
- EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, USDCHF

Cross pairs:
- EURJPY, GBPJPY, EURGBP, AUDCAD, AUDNZD

Commodities:
- XAUUSD (Gold), XAGUSD (Silver)
- USOIL (Crude Oil), UKOIL (Brent)

Indices:
- US30 (Dow), NAS100 (Nasdaq), SPX500 (S&P 500)
- GER40 (DAX), UK100 (FTSE)

Check with your broker for available symbols!

## Strategy Types

Currently supported:
- `SIMPLE_MA` - Simple Moving Average crossover
- `RSI` - Relative Strength Index (coming soon)
- `MACD` - Moving Average Convergence Divergence (coming soon)
- `CUSTOM` - Custom strategy implementation

## Timeframes

- `M1` - 1 minute
- `M5` - 5 minutes (fast scalping)
- `M15` - 15 minutes (balanced)
- `M30` - 30 minutes
- `H1` - 1 hour (swing trading)
- `H4` - 4 hours
- `D1` - Daily
- `W1` - Weekly
- `MN1` - Monthly

## Testing Your Configuration

### Validate Configuration
```bash
# Check if config is valid
curl http://localhost:8000/api/workers/account-5012345678/validate
```

### Start Worker
```bash
# Start via API
curl -X POST http://localhost:8000/api/workers/account-5012345678/start \
  -H "Content-Type: application/json" \
  -d '{"apply_defaults": true, "validate": true}'
```

### Check Status
```bash
# Get worker info
curl http://localhost:8000/api/workers/account-5012345678

# List all workers
curl http://localhost:8000/api/workers
```

## Troubleshooting

### "No such file or directory"
- Check filename matches pattern: `account-{login}.yml`
- Ensure file is in `config/accounts/` directory

### "Validation failed"
- Check YAML syntax (indentation matters!)
- Ensure all required fields are present
- Verify password doesn't contain special YAML characters

### "Connection failed"
- Verify MT5 credentials are correct
- Check server name matches broker exactly
- Ensure `portable: true` is set

### "Worker already exists"
- Worker is already running
- Disconnect first, then reconnect

## Security Best Practices

1. **Never commit passwords to git**:
   ```bash
   # Add to .gitignore
   echo "config/accounts/account-*.yml" >> .gitignore
   echo "!config/accounts/*.example" >> .gitignore
   ```

2. **Use environment variables** (optional):
   ```yaml
   password: "${MT5_PASSWORD}"         # Reads from environment
   ```

3. **Restrict file permissions**:
   ```bash
   chmod 600 config/accounts/account-*.yml
   ```

## Next Steps

1. ✅ Copy example files
2. ✅ Update with your credentials
3. ✅ Configure currency pairs
4. ✅ Adjust risk settings
5. ✅ Start API server
6. ✅ Connect via UI
7. ✅ Monitor trading bot logs

## Documentation

- Full setup guide: `docs/PHASE4_UI_SETUP_GUIDE.md`
- API reference: `docs/API.md`
- Trading strategies: `docs/STRATEGIES.md`

## Support

For issues or questions, check:
- Logs: `logs/tradingmtq.log`
- API status: `http://localhost:8000/api/health`
- Worker status: `http://localhost:8000/api/workers`
