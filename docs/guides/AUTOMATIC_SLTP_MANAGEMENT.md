# Automatic SL/TP Management System

## 🎯 Overview

The automatic SL/TP management system monitors your open positions and automatically adjusts stop losses and take profits to maximize profit and minimize risk.

**All features are enabled by default** and work independently - no manual intervention required!

---

## 🚀 Features

### 1. **Breakeven Protection** 🛡️
**Automatically moves SL to entry price + small profit when position is profitable**

- **When**: Position reaches +20 pips profit
- **Action**: Moves SL to entry + 2 pips
- **Benefit**: Guarantees small profit, eliminates loss risk
- **Example**: 
  ```
  Entry: 1.10000
  Profit reaches: +20 pips (1.10200)
  → SL moved to: 1.10020 (entry + 2 pips)
  Result: Risk-free trade with guaranteed +2 pips
  ```

### 2. **Trailing Stop** 📈
**Automatically follows price to lock in increasing profits**

- **Activation**: When position reaches +25 pips profit
- **Distance**: Maintains 15 pips from current price
- **Action**: Moves SL up as price moves favorably
- **Benefit**: Captures big moves while protecting profits
- **Example**:
  ```
  Entry: 1.10000, Initial SL: 1.09800
  
  Price moves to 1.10250 (+25 pips) → Trailing activates
  SL moves to: 1.10100 (price - 15 pips)
  
  Price moves to 1.10400 (+40 pips)
  SL moves to: 1.10250 (price - 15 pips)
  
  Price moves to 1.10600 (+60 pips)
  SL moves to: 1.10450 (price - 15 pips)
  
  Result: Locked in +45 pips instead of original +20 pips
  ```

### 3. **Partial Profit Taking** 💰
**Closes part of your position to secure profits**

- **Trigger**: When profit reaches +30 pips
- **Action**: Closes 50% of position volume
- **Benefit**: Locks in guaranteed profit, keeps remainder running
- **Example**:
  ```
  Position: BUY 0.10 lots @ 1.10000
  Profit reaches: +30 pips
  
  → Closes: 0.05 lots (50%) → Profit locked ✓
  → Remains: 0.05 lots → Can still catch bigger move
  
  If price goes to +60 pips:
  - Locked profit: 0.05 lots × 30 pips
  - Running profit: 0.05 lots × 60 pips
  Total better than closing everything at +30!
  ```

### 4. **Dynamic Take Profit Extension** 🎯
**Extends TP when price is close to target**

- **Trigger**: When price reaches 80% of TP distance
- **Action**: Extends TP by +20 pips
- **Benefit**: Captures extended moves in strong trends
- **Example**:
  ```
  Entry: 1.10000, TP: 1.10400 (+40 pips)
  
  Price reaches: 1.10320 (80% of +40 pips = +32 pips)
  → TP extended to: 1.10600 (+60 pips total)
  
  If strong trend continues:
  Price reaches: 1.10480 (80% of +60 pips = +48 pips)
  → TP extended again to: 1.10800 (+80 pips total)
  
  Result: Rides trend instead of closing prematurely
  ```

---

## ⚙️ Configuration

Edit `config/currencies.yaml`:

```yaml
modifications:
  # 1. Breakeven Protection
  enable_breakeven: true
  breakeven_trigger_pips: 20      # Profit required to trigger
  breakeven_offset_pips: 2        # Profit to lock in
  
  # 2. Trailing Stop
  enable_trailing_stop: true
  trailing_stop_pips: 15          # Distance from current price
  trailing_activation_pips: 25    # Profit to activate
  
  # 3. Partial Profit Taking
  enable_partial_close: true
  partial_close_trigger_pips: 30  # Profit to trigger
  partial_close_percent: 50       # % of position to close
  
  # 4. Dynamic Take Profit
  enable_dynamic_tp: true
  tp_extension_pips: 20           # TP extension amount
  tp_extension_trigger_percent: 80 # Trigger at 80% to TP
```

### How Often It Checks

```yaml
global:
  # Position management runs every 5 seconds
  position_management_interval: 5
```

---

## 📊 Real Trading Examples

### Example 1: Conservative EUR/USD Trade

**Setup:**
- Entry: 1.08500 BUY
- Initial SL: 1.08300 (-20 pips)
- Initial TP: 1.08900 (+40 pips)
- Volume: 0.10 lots

**What Happens:**

1. **Price reaches 1.08700 (+20 pips)**
   - ✅ Breakeven triggered
   - SL moves: 1.08300 → 1.08520
   - Status: Risk-free trade

2. **Price reaches 1.08750 (+25 pips)**
   - ✅ Trailing stop activates
   - SL moves: 1.08520 → 1.08600 (price - 15 pips)

3. **Price reaches 1.08830 (+33 pips)**
   - ✅ Partial close triggers (profit > 30 pips)
   - Closes: 0.05 lots → **+$16.50 locked** ✓
   - Remains: 0.05 lots
   - Trailing SL: 1.08680

4. **Price reaches TP at 1.08900 (+40 pips)**
   - Remaining 0.05 lots closes
   - Final profit: **$20.00 total**
   - Without automation: Same $20
   - **But if price reversed at step 3, you kept $16.50!**

### Example 2: Strong Trend GBP/USD

**Setup:**
- Entry: 1.27000 BUY
- Initial SL: 1.26750 (-25 pips)
- Initial TP: 1.27500 (+50 pips)
- Volume: 0.08 lots

**What Happens:**

1. **Price reaches 1.27200 (+20 pips)** → Breakeven set at 1.27020

2. **Price reaches 1.27250 (+25 pips)** → Trailing activates

3. **Price reaches 1.27300 (+30 pips)** → Partial close 50%
   - **Locked: $12.00** ✓
   - Running: 0.04 lots

4. **Price reaches 1.27400 (+40 pips, 80% to TP)**
   - ✅ Dynamic TP extension triggers
   - TP extended: 1.27500 → 1.27700 (+70 pips)
   - Trailing SL: 1.27250

5. **Price reaches 1.27640 (+64 pips, 80% to new TP)**
   - ✅ TP extended again: 1.27700 → 1.27900 (+90 pips)
   - Trailing SL: 1.27490

6. **Price reverses, hits trailing SL at 1.27490**
   - Remaining 0.04 lots closes at +49 pips
   - Partial profit: $12.00
   - Final close: 0.04 × 49 pips = $19.60
   - **Total profit: $31.60**
   - **Without automation: Only $20.00 (stopped at +50 pips)**
   - **Improvement: +58%** 🚀

---

## 🔧 Customization Examples

### Ultra-Conservative (Lock profits quickly)

```yaml
modifications:
  enable_breakeven: true
  breakeven_trigger_pips: 10      # Very early breakeven
  breakeven_offset_pips: 1        # Minimal profit
  
  enable_trailing_stop: true
  trailing_stop_pips: 10          # Tight trailing
  trailing_activation_pips: 15    # Activate early
  
  enable_partial_close: true
  partial_close_trigger_pips: 15  # Close early
  partial_close_percent: 70       # Close most of it
  
  enable_dynamic_tp: false        # No TP extension
```

### Aggressive Trend Rider

```yaml
modifications:
  enable_breakeven: true
  breakeven_trigger_pips: 30      # Let it breathe
  breakeven_offset_pips: 5        # Good cushion
  
  enable_trailing_stop: true
  trailing_stop_pips: 25          # Wide trailing
  trailing_activation_pips: 40    # Wait for strong move
  
  enable_partial_close: false     # No partial - ride it all
  
  enable_dynamic_tp: true
  tp_extension_pips: 30           # Big extensions
  tp_extension_trigger_percent: 70 # Extend early
```

### Scalper Setup

```yaml
modifications:
  enable_breakeven: true
  breakeven_trigger_pips: 5       # Immediate safety
  breakeven_offset_pips: 1
  
  enable_trailing_stop: true
  trailing_stop_pips: 5           # Very tight
  trailing_activation_pips: 8
  
  enable_partial_close: true
  partial_close_trigger_pips: 10  # Quick partial
  partial_close_percent: 80       # Close most
  
  enable_dynamic_tp: false        # Scalpers don't extend
```

---

## 📈 Benefits Summary

| Feature | Risk Reduction | Profit Enhancement | Best For |
|---------|---------------|-------------------|----------|
| **Breakeven** | ⭐⭐⭐⭐⭐ | ⭐⭐ | All traders |
| **Trailing Stop** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Trend followers |
| **Partial Close** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Conservative traders |
| **Dynamic TP** | ⭐⭐ | ⭐⭐⭐⭐⭐ | Strong trends |

---

## 🎮 How to Use

### 1. Start with defaults (recommended)
```bash
python main.py
```
All features are already enabled with tested values!

### 2. Monitor the logs

You'll see automatic management messages:

```
21:45:12 ✓ INFO 🛡️ [EURUSD] Breakeven set @ 1.08520 (+2 pips)
21:46:30 ✓ INFO 📈 [EURUSD] Trailing stop activated @ 25.0 pips profit
21:47:15 ✓ DEBUG [EURUSD] Trailing SL moved to 1.08600 (15 pips)
21:48:42 ✓ INFO 💰 [EURUSD] Partial close: 50% (0.05 lots) @ 30.2 pips profit
21:51:03 ✓ INFO 🎯 [GBPUSD] TP extended by 20 pips to 1.27700
```

### 3. Adjust settings on-the-fly

Edit `config/currencies.yaml` and save - changes apply immediately!

---

## ⚠️ Important Notes

### What Applies to What

- **Breakeven/Trailing/Partial/Dynamic TP**: Apply to EXISTING open positions
- **SL/TP pips in currency config**: Apply only to NEW trades

### Each Position Tracked Independently

```
Position #12345: Breakeven set ✓, Partial closed ✓
Position #12346: Trailing active, waiting for partial trigger
Position #12347: Just opened, waiting for +20 pips
```

### Safety Features

- **Never moves SL backwards** (protects against losses)
- **Validates minimum lot sizes** (prevents broker errors)
- **Cleans up closed positions** (no memory leaks)
- **Error handling per position** (one error doesn't stop others)

---

## 🧪 Testing Recommendations

### Week 1: Observe Only
- Keep defaults enabled
- Watch how it behaves
- Check logs for patterns

### Week 2: Small Adjustments
- Tweak one parameter at a time
- Compare results
- Note what works for your pairs

### Week 3: Optimize
- Find your optimal settings
- Different settings per currency if needed
- Document your configuration

---

## 💡 Pro Tips

1. **High volatility pairs** (GBP/JPY, XAU/USD):
   - Use wider trailing stops (20-25 pips)
   - Higher breakeven triggers (25-30 pips)

2. **Stable pairs** (EUR/USD, USD/CHF):
   - Tighter trailing stops (10-15 pips)
   - Lower breakeven triggers (15-20 pips)

3. **News events**:
   - Temporarily disable all auto-management
   - Let positions hit original SL/TP
   ```yaml
   modifications:
     enable_breakeven: false
     enable_trailing_stop: false
     enable_partial_close: false
     enable_dynamic_tp: false
   ```

4. **Friday close**:
   - Enable aggressive partial closes
   - Tighten trailing stops
   ```yaml
   partial_close_percent: 80
   trailing_stop_pips: 10
   ```

---

## 📊 Performance Tracking

The system tracks for each position:
- Highest profit reached
- Breakeven status
- Partial close status
- Trailing activation status

Check position state:
```python
from src.trading.orchestrator import orchestrator

state = orchestrator.position_manager.get_position_state(ticket)
print(f"Highest profit: {state['highest_profit_pips']:.1f} pips")
print(f"Breakeven set: {state['breakeven_set']}")
print(f"Trailing active: {state['trailing_active']}")
```

---

## 🚀 Ready to Go!

The system is **already configured and running** with all features enabled. Just monitor the logs and watch it work!

For questions or issues, check the main trading logs in `logs/trading_YYYYMMDD.log`.

Happy automated trading! 🎯📈💰
