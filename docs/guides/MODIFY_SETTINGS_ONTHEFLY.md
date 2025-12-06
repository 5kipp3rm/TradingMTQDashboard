# How to Modify SL/TP and Other Settings On-The-Fly

## Quick Start

1. **Start the bot:**
   ```bash
   python main.py
   ```

2. **Modify settings while running:**
   - Open `config/currencies.yaml` in any text editor
   - Make your changes (see examples below)
   - Save the file
   - Changes apply automatically within 60 seconds (default reload interval)

## Common Modifications

### 1. Change Stop Loss / Take Profit

**Before:**
```yaml
EURUSD:
  enabled: true
  sl_pips: 20
  tp_pips: 40
```

**After (wider stops):**
```yaml
EURUSD:
  enabled: true
  sl_pips: 30    # ← Changed from 20
  tp_pips: 60    # ← Changed from 40
```

**Effect:** New EURUSD trades will use 30/60 pips (existing positions unchanged)

---

### 2. Change Risk Percentage

**Before:**
```yaml
GBPUSD:
  risk_percent: 1.0
```

**After:**
```yaml
GBPUSD:
  risk_percent: 0.5  # ← Reduce risk to 0.5%
```

**Effect:** New GBPUSD trades will risk only 0.5% of account

---

### 3. Disable a Currency Temporarily

**Before:**
```yaml
USDJPY:
  enabled: true
```

**After:**
```yaml
USDJPY:
  enabled: false  # ← Disable trading
```

**Effect:** USDJPY will be skipped on next reload (existing position remains open)

---

### 4. Enable a Disabled Currency

**Before:**
```yaml
XAUUSD:
  enabled: false
```

**After:**
```yaml
XAUUSD:
  enabled: true  # ← Enable trading
```

**Note:** You need to RESTART the bot for new currencies (not just reload)

---

### 5. Change Strategy Type

**Before:**
```yaml
EURUSD:
  strategy_type: "position"  # Trades on MA position
```

**After:**
```yaml
EURUSD:
  strategy_type: "crossover"  # Wait for MA crossover
```

**Effect:** Changes signal generation logic for new trades

---

### 6. Adjust MA Periods

**Before:**
```yaml
EURUSD:
  fast_period: 10
  slow_period: 20
```

**After (slower strategy):**
```yaml
EURUSD:
  fast_period: 20   # ← Slower MAs
  slow_period: 50
```

**Effect:** Less frequent but potentially more reliable signals

---

### 7. Enable Trailing Stop

**Before:**
```yaml
modifications:
  enable_trailing_stop: false
```

**After:**
```yaml
modifications:
  enable_trailing_stop: true
  trailing_stop_pips: 15  # Trail by 15 pips
```

**Effect:** All positions will have trailing stop applied (implementation required)

---

### 8. Enable Breakeven

**Before:**
```yaml
modifications:
  breakeven_trigger_pips: 0
```

**After:**
```yaml
modifications:
  breakeven_trigger_pips: 20  # Move SL when 20 pips profit
  breakeven_offset_pips: 2     # SL = entry + 2 pips
```

**Effect:** SL moves to breakeven when profit reaches 20 pips (implementation required)

---

### 9. Emergency Stop All Trading

**Immediate stop:**
```yaml
emergency:
  emergency_stop: true        # ← ACTIVATE EMERGENCY STOP
  close_all_on_stop: true     # ← Close all positions
```

**Effect:** Trading stops immediately on next cycle check (~30s)

---

### 10. Change Global Settings

**Portfolio limits:**
```yaml
global:
  max_concurrent_trades: 3    # ← Reduce from 5 to 3
  portfolio_risk_percent: 5.0 # ← Reduce from 10% to 5%
  interval_seconds: 60        # ← Slower cycles (60s instead of 30s)
```

**Effect:** Applies to all currencies on next reload

---

## Important Notes

### What Changes Apply Immediately?
- ✅ Enabling/disabling currencies
- ✅ SL/TP for **new** trades
- ✅ Risk percentage for **new** trades
- ✅ Strategy parameters for **new** trades
- ✅ Emergency stop
- ✅ Global limits (max trades, portfolio risk)

### What Requires Restart?
- ❌ Adding completely new currencies
- ❌ Changing connector settings
- ❌ Structural config changes

### What Doesn't Affect Existing Positions?
- Existing open positions keep their original SL/TP
- To modify existing positions, use MT5 terminal manually
- OR implement trailing stop / breakeven features

---

## Advanced: Modifying Existing Positions

### Option 1: Manual via MT5 Terminal
1. Open MetaTrader 5
2. Right-click position → Modify
3. Change SL/TP manually

### Option 2: Programmatic (TradingController)

```python
from src.trading import TradingController

controller = TradingController(connector)

# Get all open positions
positions = controller.get_open_positions()

# Modify each position
for pos in positions:
    if pos.symbol == "EURUSD":
        new_sl = pos.price_open - 0.0030  # 30 pips
        new_tp = pos.price_open + 0.0060  # 60 pips
        
        result = controller.modify_trade(
            ticket=pos.ticket,
            sl=new_sl,
            tp=new_tp
        )
        
        if result.success:
            print(f"✓ Modified {pos.symbol} #{pos.ticket}")
```

### Option 3: Implement Auto-Modification

The config has these settings ready:
```yaml
modifications:
  enable_trailing_stop: true
  trailing_stop_pips: 15
  
  breakeven_trigger_pips: 20
  breakeven_offset_pips: 2
```

**Implementation needed in orchestrator:**
- Check each open position's profit
- If profit > breakeven_trigger → move SL to breakeven
- If trailing_stop enabled → adjust SL as price moves

---

## Real-World Examples

### Example 1: Market Becomes More Volatile
```yaml
# Widen stops during high volatility (e.g., NFP day)
EURUSD:
  sl_pips: 40   # ← From 20
  tp_pips: 80   # ← From 40
```

### Example 2: Reduce Risk at End of Week
```yaml
# Lower risk on Friday
EURUSD:
  risk_percent: 0.5  # ← From 1.0

GBPUSD:
  enabled: false     # ← Stop trading GBP before weekend
```

### Example 3: Switch to Conservative Mode
```yaml
# Change all to crossover (less frequent trades)
EURUSD:
  strategy_type: "crossover"  # ← From "position"
  
GBPUSD:
  strategy_type: "crossover"
```

### Example 4: Pause Specific Pair
```yaml
# News event for EUR - pause EURUSD
EURUSD:
  enabled: false  # ← Temporarily disable
```

---

## Monitoring Changes

The bot prints when config is reloaded:
```
✓ Configuration reloaded from config/currencies.yaml
🔄 Configuration reloaded - new settings will apply to new trades
   ⏸️  USDJPY disabled in config - will skip
```

Check logs to see:
- Which currencies are active
- Current SL/TP values
- Risk percentages
- Emergency stop status

---

## Safety Tips

1. **Test changes first:**
   - Start with small risk_percent
   - Enable one currency at a time
   - Monitor for 1 hour before full deployment

2. **Keep backups:**
   ```bash
   cp config/currencies.yaml config/currencies.yaml.backup
   ```

3. **Use emergency stop:**
   - Set `emergency_stop: true` if things go wrong
   - Bot stops on next cycle (within ~30-60s)

4. **Monitor free margin:**
   - Don't enable too many currencies
   - Watch max_concurrent_trades limit

5. **Document changes:**
   - Add comments in YAML
   - Track what works and what doesn't

---

## File Location

**Configuration file:**
```
TradingMTQ/
└── config/
    └── currencies.yaml  ← Edit this file
```

**Run script:**
```bash
python main.py
```

**Auto-reload settings:**
```yaml
global:
  auto_reload_config: true    # ← Must be true
  reload_check_interval: 60   # ← Check every 60 seconds
```

---

## Questions?

**Q: Do I need to restart for SL/TP changes?**
A: No! Just edit and save the YAML file. New trades use new values.

**Q: What about existing positions?**
A: They keep original SL/TP. Modify via MT5 or use TradingController.

**Q: How fast do changes apply?**
A: Within 60 seconds (default reload_check_interval).

**Q: Can I add new currencies without restart?**
A: Not yet - restart required for new currencies. Disabling/enabling existing ones works.

**Q: How do I know if config is valid?**
A: Bot prints errors if YAML is invalid. Keep a backup!
