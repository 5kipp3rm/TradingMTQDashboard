# Utility Scripts

Standalone utility scripts for managing and monitoring the trading system.

## 🛠️ Utility Scripts

### MT5 Connection & Management
- **`start_mt5.py`** - Launch MetaTrader 5 terminal programmatically
- **`check_env.py`** - Verify environment variables and configuration

### Position Management
- **`check_positions.py`** - View all open positions
- **`close_all_positions.py`** - Close all open positions (emergency use)
- **`check_signal.py`** - Check current trading signals

### Monitoring
- **`check_autotrading.py`** - Verify auto-trading is enabled in MT5

### Development Tools
- **`pip_calculator.py`** - Calculate pip values for different instruments

## 📖 Usage

### Check Current Positions
```bash
python scripts/check_positions.py
```

### Close All Positions (DANGER!)
```bash
python scripts/close_all_positions.py
```

### Verify Environment
```bash
python scripts/check_env.py
```

### Check Trading Signals
```bash
python scripts/check_signal.py
```

## ⚠️ Important Notes

- **`close_all_positions.py`** will close ALL open positions - use with caution!
- Make sure MT5 is running before using position-related scripts
- These scripts are for manual management and debugging

## 🔗 Related

- Main trading bot: `../main.py`
- Example scripts: `../examples/`
- Tests: `../tests/`
