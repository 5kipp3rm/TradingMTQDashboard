# TradingMTQ - AI-Powered MetaTrader Currency Trading Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MetaTrader 5](https://img.shields.io/badge/MetaTrader-5-green.svg)](https://www.metatrader5.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent trading application that connects to MetaTrader 5 to execute currency trades based on AI/LLM-driven decision logic.

## 🎯 Project Vision

TradingMTQ combines traditional technical analysis with cutting-edge AI/ML models to create an automated forex trading system. The platform analyzes market data in real-time and executes trades based on sophisticated algorithms, from simple rule-based strategies to advanced deep learning models.

## ✨ Features

### Phase 1 ✅ COMPLETE
- ✅ MetaTrader 5 connection with pooling support
- ✅ Real-time market data (ticks, OHLC bars)
- ✅ Order execution (market & pending orders)
- ✅ Position management and tracking
- ✅ Comprehensive error handling (800+ error codes)
- ✅ 60+ unit tests with 90%+ coverage
- ✅ Production-ready logging

### Phase 2 ✅ COMPLETE + ENHANCED
- ✅ 12+ Technical Indicators (RSI, MACD, BB, ATR, ADX, etc.)
- ✅ 5+ Trading Strategies (MA Crossover, RSI, MACD, BB, Multi-indicator)
- ✅ Full Backtesting Engine with performance analytics
- ✅ **Risk Management System** (margin calc, position sizing)
- ✅ **Pending Orders** (limit, stop, modify, delete)
- ✅ **Account Utilities** (risk-based lot sizing ⭐)
- ✅ **Live Trading Scripts** ready to run
- ✅ Automated trading with safety limits

### Phase 3 ✅ COMPLETE
- ✅ **Machine Learning Integration** (LSTM, Random Forest)
- ✅ **Feature Engineering** (40+ technical features)
- ✅ **ML-Enhanced Strategy** (combines ML + technical signals)
- ✅ **Model Training Framework** (save/load models)
- ✅ **Performance Metrics** (accuracy, precision, F1-score)
- 📖 See [PHASE3_COMPLETE.md](PHASE3_COMPLETE.md)

### Phase 4 ✅ COMPLETE
- ✅ **LLM Integration** (OpenAI GPT-4o, Anthropic Claude)
- ✅ **Sentiment Analysis** (news/social media → trading signals)
- ✅ **AI Market Analyst** (automated market reports)
- ✅ **Grid Search Optimization** (automated parameter tuning)
- ✅ **Config-based API Keys** (secure key management)
- ✅ Cost: ~$0.40/month for sentiment analysis
- 📖 See [PHASE4_COMPLETE.md](PHASE4_COMPLETE.md)

### Phase 5 (In Progress)
- 🔄 Walk-forward analysis framework
- 🔄 News-based trading signals
- 🔄 Natural language trade interface
- 📅 Web dashboard & monitoring UI
- 📅 REST API for external integrations

## 🚀 Quick Start

### 🎯 **SIMPLEST WAY - Just Run This:**

```bash
python main.py
```

That's it! The script will:
- ✅ Load configuration from `config/currencies.yaml`
- ✅ Connect to MetaTrader 5
- ✅ Start trading 6 currency pairs automatically
- ✅ Apply automatic SL/TP management (breakeven, trailing, partial profits)
- ✅ Hot-reload configuration changes every 60 seconds

**See documentation below for configuration and features.**

### Alternative Scripts:

#### Test Connection (SAFE - No Trading)
```bash
python examples/test_connection.py
```
Interactive script - tests MT5 connection, shows account info, verifies everything works.

#### Modify Open Positions
```bash
python examples/modify_positions.py
```
Interactive tool to modify SL/TP on existing positions.

#### Original Trading Bot
```bash
python run.py
```
Original entry point with menu and pre-flight checks.

### Prerequisites

- **Windows OS** (MT5 Python API is Windows-only)
- **Python 3.10+**
- **MetaTrader 5** terminal installed
- **Demo account** from a broker (e.g., MetaQuotes, IC Markets)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd TradingMTQ

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows with bash

# Install dependencies
pip install -r requirements.txt

# Configure credentials (edit .env file)
cp .env.example .env
# Add your MT5 login, password, and server
```

### Configuration

Create a `.env` file in the project root:

```env
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
```

### Run the Application

```bash
# Make sure MT5 terminal is running and logged in
python src/main.py
```

## 📖 Documentation

**🚀 CONFIGURATION-BASED TRADING (NEW!):**
- **[AUTOMATIC_SLTP_QUICKSTART.md](AUTOMATIC_SLTP_QUICKSTART.md)** - Quick start for auto SL/TP features
- **[docs/AUTOMATIC_SLTP_MANAGEMENT.md](docs/AUTOMATIC_SLTP_MANAGEMENT.md)** - Complete guide with examples
- **[docs/CONFIG_BASED_TRADING.md](docs/CONFIG_BASED_TRADING.md)** - Configuration system documentation
- **[docs/MODIFY_SETTINGS_ONTHEFLY.md](docs/MODIFY_SETTINGS_ONTHEFLY.md)** - Hot-reload settings guide
- **[QUICK_REFERENCE_CONFIG.md](QUICK_REFERENCE_CONFIG.md)** - One-page quick reference

**🤖 AI/ML FEATURES (NEW!):**
- **[PHASE3_COMPLETE.md](PHASE3_COMPLETE.md)** - Machine Learning integration guide
- **[PHASE4_COMPLETE.md](PHASE4_COMPLETE.md)** - LLM integration & sentiment analysis
- **[docs/API_SETUP.md](docs/API_SETUP.md)** - OpenAI/Anthropic API setup guide
- **[examples/phase3_ml_demo.py](examples/phase3_ml_demo.py)** - ML demo (LSTM, Random Forest)
- **[examples/phase4_llm_demo.py](examples/phase4_llm_demo.py)** - LLM demo (sentiment, market analysis)

**Original Documentation:**
- **[START_HERE.md](START_HERE.md)** - Complete overview of ready-to-run system
- **[READY_TO_RUN.md](READY_TO_RUN.md)** - Quick reference for all 5 trading scripts
- **[LIVE_TRADING_GUIDE.md](LIVE_TRADING_GUIDE.md)** - Complete guide to live trading (60+ pages)

**Core Documentation:**
- **[PHASE1_STATUS.md](PHASE1_STATUS.md)** - Core infrastructure (MT5 connector, 60 tests)
- **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)** - Enhanced features documentation
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Code snippets and examples

**Original Docs** (in `docs/` directory):
- [Quick Start Guide](docs/build/quick-start.md) - Original getting started
- [System Architecture](docs/design/architecture.md) - Technical design
- [Phase Roadmap](docs/build/phase2-plus-roadmap.md) - Future features
- [Documentation Index](docs/INDEX.md) - Complete documentation overview

## 🏗️ Project Structure

```
TradingMTQ/
├── main.py                  # 👈 START HERE! Configuration-based trading
├── config/
│   ├── currencies.yaml      # ⚙️ Edit this for all settings
│   └── api_keys.yaml        # 🔑 LLM API keys (OpenAI, Anthropic)
│
├── examples/                # Ready-to-run scripts & demos
│   ├── test_connection.py   # ⚪ Test MT5 (SAFE)
│   ├── modify_positions.py  # 🟠 Modify open positions
│   ├── phase3_ml_demo.py    # 🤖 ML demo (LSTM, Random Forest)
│   └── phase4_llm_demo.py   # 🧠 LLM demo (sentiment, AI analyst)
│
├── src/                     # Source code
│   ├── connectors/          # MT5 connection & utilities
│   │   ├── mt5_connector.py # Core connector
│   │   └── account_utils.py # Risk management ⭐
│   ├── strategies/          # 5+ trading strategies
│   │   ├── simple_ma.py     # MA Crossover
│   │   ├── ml_strategy.py   # 🆕 ML-enhanced strategy
│   │   └── (4+ more...)
│   ├── ml/                  # 🆕 Machine Learning module
│   │   ├── feature_engineer.py  # 40+ technical features
│   │   ├── lstm_model.py        # LSTM price predictor
│   │   └── random_forest.py     # Random Forest classifier
│   ├── llm/                 # 🆕 LLM integration
│   │   ├── openai_provider.py   # GPT-4o integration
│   │   ├── anthropic_provider.py # Claude integration
│   │   ├── sentiment.py         # Sentiment analyzer
│   │   └── market_analyst.py    # AI market reports
│   ├── optimization/        # 🆕 Parameter optimization
│   │   └── grid_search.py       # Grid search optimizer
│   ├── trading/             # Multi-currency orchestrator
│   │   ├── currency_trader.py    # Individual currency trader
│   │   ├── orchestrator.py       # Multi-currency manager
│   │   └── position_manager.py   # Auto SL/TP management
│   ├── indicators/          # 12+ technical indicators
│   ├── backtest/            # Backtesting engine
│   └── utils/
│       └── config_loader.py # 🆕 Config & API key loader
│
├── docs/                    # Enhanced documentation
│   ├── AUTOMATIC_SLTP_MANAGEMENT.md  # Auto SL/TP guide
│   ├── CONFIG_BASED_TRADING.md       # Configuration system
│   ├── API_SETUP.md                  # 🆕 LLM API setup guide
│   └── (more...)
│
├── tests/                   # 60+ unit tests (90%+ coverage)
│
├── requirements.txt         # Core dependencies
├── requirements-ml.txt      # 🆕 ML dependencies
├── requirements-llm.txt     # 🆕 LLM dependencies
│
└── *.md                     # Quick reference guides
    ├── PHASE3_COMPLETE.md   # 🆕 ML documentation
    ├── PHASE4_COMPLETE.md   # 🆕 LLM documentation
    └── (more...)
```

## 🛠️ Technology Stack

- **MetaTrader Integration**: MetaTrader5 Python API
- **Backend**: Python 3.10+
- **Data Processing**: Pandas, NumPy
- **Machine Learning**: TensorFlow/Keras, scikit-learn ✅
- **LLM/AI**: OpenAI GPT-4o, Anthropic Claude ✅
- **Configuration**: YAML, environment variables
- **Testing**: pytest (60+ tests, 90%+ coverage)
- **Database** (Future): PostgreSQL
- **Web** (Future): FastAPI, React/Next.js

## 📊 Development Roadmap

| Phase | Timeline | Status | Description |
|-------|----------|--------|-------------|
| Phase 1 | Weeks 1-2 | ✅ **COMPLETE** | MT5 connector, 60 tests, 90%+ coverage |
| Phase 2 | Weeks 3-6 | ✅ **COMPLETE** | Indicators, strategies, backtesting, risk management |
| Phase 3 | Week 7-8 | ✅ **COMPLETE** | Machine Learning (LSTM, Random Forest, feature engineering) |
| Phase 4 | Week 9 | ✅ **COMPLETE** | LLM Integration (GPT-4o, Claude, sentiment analysis) |
| Phase 5 | Week 10+ | 🔄 **IN PROGRESS** | Advanced optimization, news signals, web dashboard |

**Current Status:** Phase 4 Complete - **AI-powered trading system with ML & LLM!**

**Latest Release:** [v4.0](https://github.com/5kipp3rm/TradingMTQ/releases/tag/v4.0) - LLM Integration

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_mt5_connector.py
```

## ⚠️ Risk Disclaimer

**IMPORTANT**: This software is for educational and research purposes.

- **Trading involves substantial risk** of loss
- **Past performance is not indicative** of future results
- **Always test on demo accounts** before live trading
- **Never invest more than you can afford to lose**
- **The authors are not responsible** for any financial losses
- **Comply with all applicable regulations** in your jurisdiction

## 🔒 Security

- Never commit credentials or API keys to version control
- Store sensitive data in `.env` file (added to `.gitignore`)
- Use environment variables for production deployments
- Regularly update dependencies for security patches
- Enable two-factor authentication on broker accounts

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- MetaQuotes for the MetaTrader 5 platform and Python API
- The open-source community for excellent ML/AI libraries
- All contributors and testers

## 📧 Contact

For questions or support:
- Open an issue on GitHub
- Check the [documentation](docs/INDEX.md)
- Review [troubleshooting guide](docs/build/quick-start.md#troubleshooting)

## 🌟 Star History

If you find this project helpful, please consider giving it a star! ⭐

---

**Built with ❤️ for algorithmic trading enthusiasts**
