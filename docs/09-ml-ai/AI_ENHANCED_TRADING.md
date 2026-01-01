# 🧠 AI-Enhanced Trading System

## Overview

The TradingMTQ system now features **intelligent position management** using ML and LLM to make smarter trading decisions. Instead of hard position limits, the bot uses AI to decide:

- ✅ **When to open** new positions (opportunity vs risk)
- ✅ **When to close** losing positions early (cut losses)
- ✅ **When to take profits** (exit winners strategically)
- ✅ **How many** positions to hold (dynamic limits based on performance)

---

## 🚀 Key Features

### 1. **Intelligent Position Manager**

Replaces the hard 3-5 position limit with smart decision-making:

```python
# Old way (hard limit)
if positions >= 5:
    skip_trade()  # ❌ Rigid

# New way (intelligent)
if portfolio_losing_badly:
    close_worst_performer()
    skip_new_trades()  # 🧠 Smart
elif portfolio_winning:
    allow_more_positions()  # Up to 20!
```

**Decision Factors:**
- Current portfolio P/L
- Number of winning vs losing positions
- Symbol correlation (avoid too much EUR exposure)
- ML prediction confidence
- LLM sentiment alignment
- Position count (soft scaling, not hard limit)

### 2. **ML Signal Enhancement**

Machine Learning models enhance technical signals:

```
Technical Signal: BUY (50% confidence)
    ↓
ML Prediction: BUY (85% confidence)
    ↓
Combined Signal: BUY (72% confidence) ✅ Trade!

---

Technical Signal: BUY (50% confidence)
    ↓
ML Prediction: SELL (90% confidence)
    ↓
Override: SELL (72% confidence) 🔄 ML wins!
```

### 3. **LLM Sentiment Filter**

Large Language Models analyze market sentiment:

```
Signal: BUY EURUSD
    ↓
News Sentiment: "ECB dovish, EUR weakness expected"
    ↓
Sentiment Result: BEARISH (-1, 82% confidence)
    ↓
Decision: SKIP BUY ⚠️ Sentiment conflict
```

---

## 📊 How It Works

### Trading Cycle with AI

```
Every 30 seconds:

1. Get Market Data (MT5)
   ↓
2. Technical Analysis
   - Calculate indicators
   - Generate signal (BUY/SELL/HOLD)
   ↓
3. ML Enhancement (if enabled) 🧠
   - Extract 40+ features
   - Predict with Random Forest/LSTM
   - Combine with technical signal
   ↓
4. LLM Sentiment (if enabled) 🤖
   - Analyze recent news
   - Check sentiment alignment
   - Filter conflicting signals
   ↓
5. Intelligent Position Manager 🎯
   - Analyze portfolio health
   - Check exposure/correlation
   - Decide: Open, Close, or Hold
   ↓
6. Execute Trade (if approved)
   ↓
7. Position Management
   - Breakeven after +20 pips
   - Trailing stop at -15 pips
   - Partial close at +50 pips
```

### Decision Tree Example

```
New Signal: BUY EURUSD @ 1.0850

Portfolio Analysis:
├─ Total Positions: 4
├─ P/L: +$125.50 💚
├─ Winning: 3
├─ Losing: 1
└─ EURUSD already in portfolio? No

ML Enhancement:
├─ Feature Engineering: 42 features
├─ RF Prediction: BUY (confidence: 0.87)
├─ Technical + ML: BUY (confidence: 0.76)
└─ ✅ Signals agree

LLM Sentiment:
├─ News: "USD jobs data weak"
├─ Sentiment: BULLISH for EUR
├─ Signal alignment: ✅ Aligned
└─ Confidence boost: +20%

Intelligent Manager Decision:
├─ Portfolio healthy (+$125)
├─ Confidence high (0.76 + 0.20 = 0.96)
├─ Position count acceptable (4 < dynamic limit)
├─ No correlation risk
└─ ✅ APPROVED - Open position!

Final Decision: EXECUTE BUY
```

---

## ⚙️ Configuration

### Enable AI Features in `config/currencies.yaml`:

```yaml
global:
  # Position limits
  max_concurrent_trades: 15  # Soft limit - AI manages dynamically
  
  # AI Features
  use_intelligent_position_manager: true  # Smart position decisions
  use_ml_enhancement: true                # ML signal enhancement  
  use_sentiment_filter: true              # LLM sentiment analysis
```

### Setup ML Models

1. **Train a model** (one-time):
   ```bash
   python examples/phase3_ml_demo.py
   ```

2. **Model saved** to `models/rf_model.pkl`

3. **Auto-loaded** on startup if found

### Setup LLM (OpenAI)

1. **Get API key** from https://platform.openai.com/api-keys

2. **Set in config**:
   ```yaml
   # config/api_keys.yaml
   openai:
     api_key: "sk-..."
   ```

3. **Or environment variable**:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

---

## 🎯 Smart Position Limits

### Dynamic Limits Based on Performance

```python
# Portfolio losing badly (-$200)
→ Max positions: 3 (conservative)

# Portfolio losing (-$100)
→ Max positions: 5 (cautious)

# Portfolio neutral
→ Max positions: 15 (normal)

# Portfolio winning (+$200)
→ Max positions: 20 (aggressive)
```

### Position Closing Logic

```python
# Close losing positions if:
- Single position loss > $50
- Portfolio drawdown > $150 (close worst)
- Too many losers (close worst 2)

# Close winning positions if:
- High exposure (8+ positions) AND profitable position exists
- Take profit to reduce risk
```

---

## 📈 Real Example Output

```
════════════════════════════════════════════════════════════════
🔄 CYCLE #15 - 2025-12-06 15:30:00
════════════════════════════════════════════════════════════════

📊 Portfolio Analysis:
   Positions: 6
   P/L: $-75.50
   Winning: 3, Losing: 3

🔍 Close Decision: Close positions: #123456 GBPUSD: Large loss $-55.20
✅ Closed position #123456

📊 Portfolio Analysis (updated):
   Positions: 5
   P/L: $-20.30

[EURUSD] Analyzing market...
  🧠 ML agrees: BUY (confidence 0.82)
  🤖 LLM sentiment filter active
🔍 Open Decision: Open new position: Portfolio improving, ML high confidence
   Final Confidence: 0.82
✅ [EURUSD] BUY 0.12 lots @ 1.08502 (Order #789123)

[USDJPY] Analyzing market...
  🧠 ML disagrees - reduced confidence to 0.45
🔍 Open Decision: Wait for better opportunity: ML low confidence, 5 positions
⏸️  [USDJPY] Signal too weak - waiting

💼 Portfolio P/L: 💚 $8.75 (6 positions)
📊 Cycle Summary: 1 trades executed
```

---

## 🔧 Advanced Configuration

### Fine-Tune ML Settings

```python
# src/trading/intelligent_position_manager.py

# Adjust confidence thresholds
STRONG_SIGNAL_THRESHOLD = 0.65  # Open position
MARGINAL_SIGNAL_THRESHOLD = 0.45  # Hold/wait
WEAK_SIGNAL_THRESHOLD = 0.0  # Skip

# Adjust ML weight
ML_WEIGHT = 0.6  # 60% ML, 40% technical
TECHNICAL_WEIGHT = 0.4

# Position limits
BASE_POSITION_LIMIT = 15
MAX_POSITION_LIMIT = 20
MIN_POSITION_LIMIT = 3
```

### Customize Decision Factors

```python
# Portfolio health multipliers
if total_profit < -100:
    confidence *= 0.5  # Reduce in drawdown
elif total_profit > 50:
    confidence *= 1.2  # Boost when winning

# Correlation penalty
if symbol_in_portfolio:
    confidence *= 0.7  # Reduce for same symbol

# High exposure scaling
if positions >= 5:
    confidence *= 0.8
elif positions >= 8:
    confidence *= 0.6
elif positions >= 10:
    confidence *= 0.4
```

---

## 📚 API Reference

### IntelligentPositionManager

```python
from src.trading import IntelligentPositionManager

manager = IntelligentPositionManager(connector)

# Enable components
manager.set_ml_predictor(ml_model)
manager.set_llm_analyst(market_analyst)
manager.set_sentiment_analyzer(sentiment_analyzer)

# Make decision
decision = manager.make_decision(signal)

# Properties
decision.action           # OPEN_NEW, CLOSE_LOSING, HOLD, etc.
decision.confidence       # 0.0 to 1.0
decision.reasoning        # "Portfolio healthy, high ML confidence"
decision.allow_new_trade  # True/False
decision.positions_to_close  # [ticket_numbers]

# Get recommended limit
limit = manager.get_position_limit_recommendation()
```

### Enable ML for Currency Trader

```python
trader.enable_ml_enhancement(ml_model)
trader.enable_sentiment_filter(sentiment_analyzer, market_analyst)
```

### Enable for All Traders

```python
orchestrator.enable_ml_for_all(ml_model)
orchestrator.enable_llm_for_all(sentiment_analyzer, market_analyst)
```

---

## ⚠️ Important Notes

### ML Model Training

- **Train before use**: Run `python examples/phase3_ml_demo.py`
- **Re-train periodically**: Market conditions change
- **Symbol-specific**: Train one model per symbol for best results
- **Data requirements**: Need 1000+ historical candles

### LLM Costs

- **OpenAI pricing**: ~$0.01 per 1000 tokens
- **Typical usage**: ~500 tokens per cycle
- **Daily cost**: ~$0.10-0.50 (depending on pairs)
- **Free tier**: 100,000 tokens/month

### Fallback Behavior

```python
# If ML fails
→ Use technical signals only (Phase 2)

# If LLM fails
→ Use neutral sentiment (no filtering)

# If intelligent manager fails
→ Use hard position limit (max_concurrent_trades)
```

---

## 🎓 How to Use

### Beginner (No AI)

```yaml
# config/currencies.yaml
global:
  use_intelligent_position_manager: false
  use_ml_enhancement: false
  use_sentiment_filter: false
  max_concurrent_trades: 5  # Hard limit
```

### Intermediate (ML Only)

```yaml
global:
  use_intelligent_position_manager: true
  use_ml_enhancement: true
  use_sentiment_filter: false  # No LLM costs
  max_concurrent_trades: 15
```

### Advanced (Full AI)

```yaml
global:
  use_intelligent_position_manager: true
  use_ml_enhancement: true
  use_sentiment_filter: true  # Requires OpenAI API key
  max_concurrent_trades: 15
```

---

## 📊 Performance Comparison

| Feature | Hard Limit | Intelligent AI |
|---------|-----------|----------------|
| Max Positions | 5 (fixed) | 3-20 (dynamic) |
| Decision Basis | Count only | Portfolio health + ML + Sentiment |
| Losing Position Management | Manual | Auto-close worst |
| Signal Quality | Technical only | Technical + ML + LLM |
| Risk Management | Fixed % | Adaptive based on performance |
| Correlation Awareness | None | Checks symbol exposure |
| Market Sentiment | Ignored | Analyzed and filtered |

---

## 🔗 Related Documentation

- [COMPLETE_SYSTEM_FLOW.md](./COMPLETE_SYSTEM_FLOW.md) - Full system flow
- [Phase 3: ML Integration](./phases/PHASE3_COMPLETE.md)
- [Phase 4: LLM Integration](./phases/PHASE4_COMPLETE.md)
- [Config Reference](./guides/QUICK_REFERENCE_CONFIG.md)

---

## 🤝 Contributing

Want to improve the AI logic? Check:
- `src/trading/intelligent_position_manager.py` - Main AI decision logic
- `src/ml/` - ML models and feature engineering
- `src/llm/` - LLM sentiment and market analysis

---

**The bot is now smart enough to manage its own risk! 🚀**
