# TradingMTQ Documentation

Complete documentation for the TradingMTQ AI-powered trading system.

## Ì≥ö Documentation Structure

### Quick Start
- **[../README.md](../README.md)** - Main project README (start here!)

### Ì≥ñ Guides
Located in `guides/`:
- **[Getting Started](guides/GETTING_STARTED.md)** - Installation and setup
- **[Live Trading Guide](guides/LIVE_TRADING_GUIDE.md)** - Complete live trading walkthrough
- **[Config-Based Trading](guides/CONFIG_BASED_TRADING.md)** - Configuration system
- **[Auto SL/TP Management](guides/AUTOMATIC_SLTP_MANAGEMENT.md)** - Automated position management
- **[Modify Settings On-The-Fly](guides/MODIFY_SETTINGS_ONTHEFLY.md)** - Hot-reload configuration
- **[Quick Reference](guides/QUICK_REFERENCE.md)** - Code snippets and examples

### Ì¥¨ Phase Documentation
Located in `phases/`:
- **[Phase 1 - MT5 Integration](phases/PHASE1_COMPLETE.md)** - Core MT5 connector
- **[Phase 2 - Trading Strategies](phases/PHASE2_COMPLETE.md)** - Indicators & backtesting
- **[Phase 3 - Machine Learning](phases/PHASE3_COMPLETE.md)** - LSTM, Random Forest, feature engineering
- **[Phase 4 - LLM Integration](phases/PHASE4_COMPLETE.md)** - GPT-4o, Claude, sentiment analysis

### Ì¥å API Documentation
Located in `api/`:
- **[API Setup Guide](api/API_SETUP.md)** - OpenAI/Anthropic API configuration
- **[MT5 Connector API](api/MT5_CONNECTOR.md)** - MetaTrader 5 integration
- **[Strategy API](api/STRATEGIES.md)** - Creating custom strategies
- **[Indicator API](api/INDICATORS.md)** - Technical indicators reference

### ÌøóÔ∏è Architecture
Located in `architecture/`:
- **[System Architecture](architecture/SYSTEM_ARCHITECTURE.md)** - Overall design
- **[Data Flow](architecture/DATA_FLOW.md)** - How data moves through the system
- **[Module Overview](architecture/MODULES.md)** - Component breakdown

## ÌæØ By Use Case

### I want to...

**Get started quickly**
‚Üí Read [../README.md](../README.md) then [guides/GETTING_STARTED.md](guides/GETTING_STARTED.md)

**Run live trading**
‚Üí [guides/LIVE_TRADING_GUIDE.md](guides/LIVE_TRADING_GUIDE.md)

**Use machine learning**
‚Üí [phases/PHASE3_COMPLETE.md](phases/PHASE3_COMPLETE.md)

**Use AI sentiment analysis**
‚Üí [phases/PHASE4_COMPLETE.md](phases/PHASE4_COMPLETE.md) + [api/API_SETUP.md](api/API_SETUP.md)

**Build custom strategies**
‚Üí [api/STRATEGIES.md](api/STRATEGIES.md)

**Understand the system**
‚Üí [architecture/SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md)

## Ì≥ã Quick Reference

### Configuration Files
- `config/currencies.yaml` - Trading settings for all pairs
- `config/api_keys.yaml` - LLM API keys (OpenAI, Anthropic)
- `.env` - MT5 credentials

### Key Scripts
- `main.py` - Main trading bot (config-based)
- `examples/test_connection.py` - Test MT5 connection
- `examples/phase3_ml_demo.py` - ML demonstration
- `examples/phase4_llm_demo.py` - LLM demonstration

### Core Modules
- `src/connectors/` - MT5 integration
- `src/strategies/` - Trading strategies
- `src/ml/` - Machine learning
- `src/llm/` - LLM integration
- `src/trading/` - Multi-currency orchestrator

## ÔøΩÔøΩ External Resources

- [MetaTrader 5 Python API](https://www.mql5.com/en/docs/python_metatrader5)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic Claude Docs](https://docs.anthropic.com/)

## Ì≥û Support

- **Issues**: [GitHub Issues](https://github.com/5kipp3rm/TradingMTQ/issues)
- **Discussions**: [GitHub Discussions](https://github.com/5kipp3rm/TradingMTQ/discussions)

---

**Last Updated**: December 6, 2025  
**Version**: 4.0 (LLM Integration Complete)
