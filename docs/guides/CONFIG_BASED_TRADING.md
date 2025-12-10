# Configuration-Based Trading System

## Overview

The TradingMTQ system now supports full YAML-based configuration with hot-reload capability. You can modify trading parameters, SL/TP, risk percentages, and more **without restarting the bot**.

## Files Created

### 1. **config/currencies.yaml**
Complete trading configuration file with:
- Global settings (max trades, portfolio risk, intervals)
- Per-currency configuration (risk%, SL/TP, strategy type, MA periods)
- Emergency controls
- Position modification rules (trailing stop, breakeven)
- Notifications and logging settings

### 2. **src/config_manager.py**
Configuration manager with hot-reload support:
- Loads YAML configuration
- Detects file changes automatically
- Provides typed access to all settings
- Validates configuration structure

### 3. **main.py**
- Main entry point for configuration-based trading
- Reads all settings from YAML
- Auto-reloads config changes
- Supports emergency stop
- Monitors for disabled currencies

### 4. **docs/MODIFY_SETTINGS_ONTHEFLY.md**
Complete guide for on-the-fly modifications:
- How to change SL/TP while running
- Enable/disable currencies
- Emergency stop procedures
- Real-world examples

### 5. **examples/modify_positions.py**
Tool for modifying existing open positions:
- Widen/tighten stops
- Set breakeven
- Remove SL/TP
- Modify specific positions

## Quick Start

### 1. Setup Configuration

Edit `config/currencies.yaml`:

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
    strategy_type: "position"
    timeframe: "M5"
    fast_period: 10
    slow_period: 20
    sl_pips: 20
    tp_pips: 40
    cooldown_seconds: 60
```

### 2. Run the Bot

```bash
python run_from_config.py
```

### 3. Modify Settings On-The-Fly

While bot is running, edit `config/currencies.yaml`:

```yaml
EURUSD:
  sl_pips: 30  # ← Changed from 20
  tp_pips: 60  # ← Changed from 40
```

Save the file. Changes apply within 60 seconds!

## How It Works

### Configuration Flow

```
config/currencies.yaml
         ↓
  ConfigurationManager
         ↓ (loads & monitors)
  MultiCurrencyOrchestrator
         ↓ (creates traders)
  CurrencyTrader (per symbol)
         ↓ (executes)
    MT5 Connector
```

### Hot-Reload Process

1. Bot runs trading cycles (every 30s default)
2. Every 60s, checks if config file changed
3. If changed, reloads configuration
4. New settings apply to **new trades only**
5. Existing positions keep original SL/TP

### What Changes Immediately?

✅ **Apply automatically:**
- Enabling/disabling currencies
- SL/TP for new trades
- Risk percentage for new trades
- Strategy parameters (MA periods, type)
- Emergency stop
- Global limits

❌ **Require restart:**
- Adding completely new currencies
- Structural configuration changes

⚠️ **Don't affect existing:**
- Open positions keep original SL/TP
- Use `modify_positions.py` or MT5 terminal to modify existing trades

## Configuration Options

### Global Settings

```yaml
global:
  max_concurrent_trades: 5        # Max positions across all pairs
  portfolio_risk_percent: 10.0    # Total portfolio risk limit
  interval_seconds: 30            # Trading cycle interval
  parallel_execution: false       # Run currencies in parallel
  auto_reload_config: true        # Enable hot-reload
  reload_check_interval: 60       # Check config every 60s
```

### Per-Currency Settings

```yaml
EURUSD:
  enabled: true                   # Trade this pair
  risk_percent: 1.0               # Risk per trade
  max_position_size: 1.0          # Max lot size
  min_position_size: 0.01         # Min lot size
  
  strategy_type: "position"       # "position" or "crossover"
  timeframe: "M5"                 # M1, M5, M15, M30, H1, H4, D1
  
  fast_period: 10                 # Fast MA period
  slow_period: 20                 # Slow MA period
  
  sl_pips: 20                     # Stop loss in pips
  tp_pips: 40                     # Take profit in pips
  
  cooldown_seconds: 60            # Min time between trades
  trade_on_signal_change: true    # Only trade on signal change
```

### Emergency Controls

```yaml
emergency:
  emergency_stop: false           # Set true to STOP IMMEDIATELY
  close_all_on_stop: true         # Close all positions on stop
  max_daily_loss_percent: 5.0     # Daily loss limit
  stop_on_daily_loss: true        # Stop if limit reached
  max_drawdown_percent: 10.0      # Max drawdown limit
  stop_on_max_drawdown: true      # Stop if exceeded
```

### Position Modifications

```yaml
modifications:
  enable_trailing_stop: false     # Auto trailing stop
  trailing_stop_pips: 15          # Trail distance
  
  breakeven_trigger_pips: 20      # Move SL when profit reaches
  breakeven_offset_pips: 2        # SL = entry + offset
  
  enable_partial_close: false     # Partial profit taking
  partial_close_percent: 50       # Close 50% at trigger
  partial_close_trigger_pips: 30  # Trigger at X pips profit
```

## Common Use Cases

### 1. Widen Stops During High Volatility

```yaml
# Before NFP or major news
EURUSD:
  sl_pips: 40   # From 20
  tp_pips: 80   # From 40
```

### 2. Reduce Risk End of Week

```yaml
# Friday afternoon
EURUSD:
  risk_percent: 0.5  # From 1.0

GBPUSD:
  enabled: false     # Stop trading GBP
```

### 3. Emergency Stop All Trading

```yaml
emergency:
  emergency_stop: true        # ACTIVATE
  close_all_on_stop: true     # Close all positions
```

### 4. Switch to Conservative Mode

```yaml
# Change all to crossover (less frequent)
EURUSD:
  strategy_type: "crossover"  # From "position"
```

### 5. Pause Specific Pair During News

```yaml
EURUSD:
  enabled: false  # Disable temporarily
```

## Modifying Existing Positions

### Option 1: Configuration-Based (Future Trades)

Edit `config/currencies.yaml` - affects **new trades only**

### Option 2: Manual via MT5 Terminal

1. Open MetaTrader 5
2. Right-click position → Modify
3. Change SL/TP

### Option 3: Programmatic

Run the modification tool:

```bash
python examples/modify_positions.py
```

Options:
- Modify specific position
- Widen all stops by X pips
- Tighten all stops by X pips
- Set breakeven for profitable positions
- Remove all SL/TP

### Option 4: TradingController API

```python
from src.trading import TradingController

controller = TradingController(connector)

# Modify position
result = controller.modify_trade(
    ticket=123456,
    sl=1.16000,
    tp=1.16400
)
```

## Monitoring

### Config Reload Messages

```
✓ Configuration reloaded from config/currencies.yaml
🔄 Configuration reloaded - new settings will apply to new trades
   ⏸️  USDJPY disabled in config - will skip
```

### Emergency Stop

```
🚨 EMERGENCY STOP ACTIVATED!
Closing all positions...
```

### Position Modifications

```
✓ EURUSD #123456 - Moved to breakeven +2
✓ GBPUSD #123457 - Widened by 10 pips
```

## Safety Recommendations

1. **Test First**
   - Start with small risk_percent
   - Enable one currency at a time
   - Monitor for 1 hour

2. **Keep Backups**
   ```bash
   cp config/currencies.yaml config/currencies.yaml.backup
   ```

3. **Use Emergency Stop**
   - Set `emergency_stop: true` if needed
   - Bot stops within ~30-60s

4. **Monitor Margin**
   - Don't enable too many currencies
   - Watch max_concurrent_trades

5. **Validate YAML**
   - Check syntax before saving
   - Bot prints errors if invalid

## File Locations

```
TradingMTQ/
├── config/
│   └── currencies.yaml          ← Main configuration
├── src/
│   └── config_manager.py        ← Config loader
├── run_from_config.py           ← Main entry point
├── examples/
│   └── modify_positions.py      ← Position modifier
└── docs/
    └── MODIFY_SETTINGS_ONTHEFLY.md  ← Complete guide
```

## Dependencies

Install PyYAML:
```bash
pip install pyyaml
```

Or add to `requirements.txt`:
```
pyyaml>=6.0
```

## Next Steps

1. **Run config-based trading:**
   ```bash
   python run_from_config.py
   ```

2. **Read the modification guide:**
   - See `docs/MODIFY_SETTINGS_ONTHEFLY.md`

3. **Customize your config:**
   - Edit `config/currencies.yaml`
   - Add your preferred currencies
   - Set risk levels

4. **Test modifications:**
   - Change SL/TP while running
   - Enable/disable pairs
   - Try emergency stop

5. **Implement advanced features:**
   - Trailing stop logic
   - Breakeven automation
   - Partial profit taking

## Support

For questions or issues:
1. Check `docs/MODIFY_SETTINGS_ONTHEFLY.md`
2. Review example configurations in `config/currencies.yaml`
3. Test with `examples/modify_positions.py`
