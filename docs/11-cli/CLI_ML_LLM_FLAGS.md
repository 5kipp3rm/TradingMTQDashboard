# ML/LLM Control Flags - Usage Guide

## Overview
You can now enable/disable ML and LLM features directly from the CLI.
Both are **enabled by default**.

## Usage

### Default (ML & LLM enabled)
```bash
tradingmtq trade
```

### Disable ML Enhancement
```bash
tradingmtq trade --disable-ml
```

### Disable LLM Sentiment
```bash
tradingmtq trade --disable-llm
```

### Disable Both
```bash
tradingmtq trade --disable-ml --disable-llm
```

### Enable (explicit)
```bash
tradingmtq trade --enable-ml --enable-llm
```

## Combined with Other Options

```bash
# Aggressive mode without ML
tradingmtq trade --aggressive --disable-ml

# Demo mode without LLM
tradingmtq trade --demo --disable-llm

# Custom config with ML only
tradingmtq trade -c config/custom.yaml --disable-llm

# Override settings, ML disabled
tradingmtq trade -i 60 -m 15 --disable-ml
```

## What Gets Disabled

### When `--disable-ml` is used:
- ❌ ML model predictions
- ❌ ML confidence scoring
- ❌ Ensemble model evaluation
- ✅ Base strategy signals still work

### When `--disable-llm` is used:
- ❌ LLM sentiment analysis
- ❌ News interpretation
- ❌ Market commentary
- ✅ Technical analysis still works

## Status Display

When starting trading, you'll see:
```
Starting trading...
   Config: config/currencies.yaml
   ML Enhancement: ENABLED
   LLM Sentiment: ENABLED
```

Or if disabled:
```
Starting trading...
   Config: config/currencies_aggressive.yaml
   Mode: AGGRESSIVE
   ML Enhancement: DISABLED
   LLM Sentiment: DISABLED
```

## Why Disable?

### Disable ML when:
- Testing base strategy performance
- Reducing computational load
- ML models not trained/available
- Want faster execution

### Disable LLM when:
- No API key configured
- Reducing API costs
- Testing without sentiment
- Offline trading

## Default Behavior

If not specified, both ML and LLM:
1. Check if libraries are available
2. Check if models/API keys exist
3. Enable if all requirements met
4. Gracefully disable if not available

The CLI flags **override** config file settings.
