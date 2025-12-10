# Quick Reference - Configuration-Based Trading

## Files Overview

| File | Purpose |
|------|---------|
| `config/currencies.yaml` | **Main configuration** - Edit this for all settings |
| `main.py` | **Start trading** - Reads from YAML config |
| `examples/modify_positions.py` | **Modify existing positions** - Change SL/TP on open trades |
| `docs/MODIFY_SETTINGS_ONTHEFLY.md` | **Complete guide** - How to modify settings |

## Quick Commands

```bash
# Start configuration-based trading
python main.py

# Modify existing open positions
python examples/modify_positions.py

# Install required dependency
pip install pyyaml
```

## Common Modifications

### Change SL/TP
```yaml
EURUSD:
  sl_pips: 30  # ← Change this
  tp_pips: 60  # ← Change this
```
**Effect:** New trades use new values (save file, wait 60s)

### Disable Currency
```yaml
GBPUSD:
  enabled: false  # ← Set to false
```
**Effect:** Stops trading this pair on next reload

### Change Risk
```yaml
EURUSD:
  risk_percent: 0.5  # ← Reduce risk
```
**Effect:** New trades risk 0.5% instead of 1%

### Emergency Stop
```yaml
emergency:
  emergency_stop: true  # ← Activate
```
**Effect:** Stops all trading within ~30-60s

## Configuration Structure

```yaml
global:
  max_concurrent_trades: 5
  portfolio_risk_percent: 10.0
  interval_seconds: 30
  auto_reload_config: true

currencies:
  EURUSD:
    enabled: true
    risk_percent: 1.0
    strategy_type: "position"  # or "crossover"
    timeframe: "M5"
    fast_period: 10
    slow_period: 20
    sl_pips: 20
    tp_pips: 40
    cooldown_seconds: 60

emergency:
  emergency_stop: false
  close_all_on_stop: true

modifications:
  enable_trailing_stop: false
  trailing_stop_pips: 15
  breakeven_trigger_pips: 20
  breakeven_offset_pips: 2
```

## TradingController Usage

```python
from src.trading import TradingController

controller = TradingController(connector)

# Get open positions
positions = controller.get_open_positions()

# Modify position
result = controller.modify_trade(
    ticket=123456,
    sl=1.16000,
    tp=1.16400
)

# Close position
result = controller.close_trade(ticket=123456)

# Close all
results = controller.close_all_positions()

# Get account summary
summary = controller.get_account_summary()
```

## What Changes Immediately?

| Setting | Applies To | Restart Needed? |
|---------|-----------|-----------------|
| SL/TP | New trades | ❌ No |
| Risk % | New trades | ❌ No |
| Enable/Disable currency | Next cycle | ❌ No |
| Strategy type | New trades | ❌ No |
| Emergency stop | Immediately | ❌ No |
| Add new currency | N/A | ✅ Yes |
| Modify existing SL/TP | N/A | Use modify_positions.py |

## Hot-Reload Settings

```yaml
global:
  auto_reload_config: true    # Enable hot-reload
  reload_check_interval: 60   # Check every 60 seconds
```

Bot automatically:
1. Checks config file every 60s
2. Reloads if changed
3. Applies to new trades
4. Prints reload message

## Safety Checklist

- [ ] Test with small risk_percent first
- [ ] Keep backup: `cp config/currencies.yaml config/currencies.yaml.backup`
- [ ] Monitor free margin
- [ ] Set max_concurrent_trades appropriately
- [ ] Know how to emergency stop
- [ ] Validate YAML syntax before saving
- [ ] Test config changes on demo first

## Emergency Procedures

### Stop All Trading
```yaml
emergency:
  emergency_stop: true
  close_all_on_stop: true
```

### Disable All Currencies
```yaml
EURUSD:
  enabled: false
GBPUSD:
  enabled: false
# ... etc
```

### Close All Positions Manually
```bash
python examples/modify_positions.py
# Select option 6, then close all
```

Or via TradingController:
```python
controller.close_all_positions()
```

## File Locations

```
TradingMTQ/
├── config/
│   └── currencies.yaml          # ← EDIT THIS
├── main.py                      # ← RUN THIS
├── examples/
│   └── modify_positions.py      # ← MODIFY TOOL
└── docs/
    ├── CONFIG_BASED_TRADING.md     # Full docs
    └── MODIFY_SETTINGS_ONTHEFLY.md # Modification guide
```

## Example Workflow

1. **Start bot:**
   ```bash
   python main.py
   ```

2. **Market becomes volatile:**
   - Open `config/currencies.yaml`
   - Change `sl_pips: 40` (wider)
   - Save file
   - Wait 60s - new trades use wider stops

3. **Want to stop GBPUSD:**
   - Set `GBPUSD: enabled: false`
   - Save
   - Wait 60s - GBPUSD stops trading

4. **Modify existing position:**
   ```bash
   python examples/modify_positions.py
   ```
   - Select option 4 (breakeven)
   - Enter offset pips
   - All profitable positions move to breakeven

5. **End of day:**
   - Set `emergency_stop: true`
   - Bot stops within 60s
   - All positions closed if `close_all_on_stop: true`

## Links

- **Full Configuration Guide:** `docs/CONFIG_BASED_TRADING.md`
- **Modification Guide:** `docs/MODIFY_SETTINGS_ONTHEFLY.md`
- **Example Config:** `config/currencies.yaml`
- **OOP Demo:** `demo_multi_currency_oop.py`
