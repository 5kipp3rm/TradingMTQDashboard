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

### Phase 3 (Coming Soon)
- 📅 Machine Learning models (LSTM, Random Forest, XGBoost)
- 📅 Parameter optimization & walk-forward analysis
- 📅 Multi-symbol portfolio management
- 📅 Advanced risk management & position correlation

## 🚀 Quick Start

### 🎯 **SIMPLEST WAY - Just Run This:**

```bash
python run.py
```

That's it! The script will:
- ✅ Check all dependencies and MT5 installation
- ✅ Test your MT5 connection
- ✅ Show you a menu of trading modes
- ✅ Guide you through everything

**See [USAGE.md](USAGE.md) for complete step-by-step guide.**

### Three Ways to Get Started:

#### 1️⃣ Main Entry Point (RECOMMENDED)
```bash
python run.py
```
**Interactive menu with pre-flight checks** - Best for first-time users!

#### 2️⃣ Test Connection (SAFE - No Trading)
```bash
python examples/test_connection.py
```
Interactive script - tests MT5 connection, shows account info, verifies everything works.

#### 3️⃣ Quick Start Trading (Fastest Way)
```bash
python examples/quick_start.py
```
Interactive prompts for credentials - starts trading in 2 minutes! (Use demo account)

#### 4️⃣ Full Trading Bot (Professional)
```bash
# Edit credentials in examples/live_trading.py first
python examples/live_trading.py
```
Full-featured automated trading with all controls and monitoring.

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

**🚀 NEW USERS START HERE:**
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
├── examples/                # 👈 START HERE! Ready-to-run scripts
│   ├── test_connection.py   # ⚪ Test MT5 (SAFE)
│   ├── quick_start.py       # 🟡 Quick trading (LIVE)
│   ├── live_trading.py      # 🟡 Full bot (LIVE)
│   ├── manage_positions.py  # 🟠 Position manager
│   └── preflight_check.py   # ⚪ System check (SAFE)
│
├── src/                     # Source code
│   ├── connectors/          # MT5 connection & utilities
│   │   ├── mt5_connector.py # Core connector
│   │   ├── account_utils.py # Risk management ⭐
│   │   └── error_descriptions.py # 800+ error codes
│   ├── strategies/          # 5+ trading strategies
│   │   ├── simple_ma.py     # MA Crossover
│   │   ├── rsi_strategy.py  # RSI mean reversion
│   │   └── (3+ more...)
│   ├── indicators/          # 12+ technical indicators
│   │   ├── trend.py         # SMA, EMA
│   │   ├── momentum.py      # RSI, MACD
│   │   └── volatility.py    # Bollinger Bands, ATR
│   ├── backtest/            # Backtesting engine
│   └── analysis/            # Performance analytics
│
├── tests/                   # 60+ unit tests (90%+ coverage)
│
├── docs/                    # Original documentation
│
└── *.md                     # NEW: Ready-to-run guides
    ├── START_HERE.md        # 👈 Complete system overview
    ├── READY_TO_RUN.md      # Script quick reference
    ├── LIVE_TRADING_GUIDE.md # Full trading guide
    └── (more...)
```

## 🛠️ Technology Stack

- **MetaTrader Integration**: MetaTrader5 Python API
- **Backend**: Python 3.10+
- **Data Processing**: Pandas, NumPy
- **ML/AI** (Future): TensorFlow/PyTorch, scikit-learn, XGBoost
- **LLM** (Future): OpenAI API, LangChain
- **Database** (Future): PostgreSQL
- **Web** (Future): FastAPI, React/Next.js

## 📊 Development Roadmap

| Phase | Timeline | Status | Description |
|-------|----------|--------|-------------|
| Phase 1 | Weeks 1-2 | ✅ **COMPLETE** | MT5 connector, 60 tests, 90%+ coverage |
| Phase 2 | Weeks 3-6 | ✅ **COMPLETE** | Indicators, strategies, backtesting |
| **Phase 2+** | **Week 7** | ✅ **COMPLETE** | **Risk management, pending orders, live trading** |
| Phase 3 | Weeks 8-12 | 📋 Planned | Machine Learning & optimization |
| Phase 4 | Future | 📋 Planned | Multi-symbol portfolio management |

**Current Status:** Phase 2 Enhanced - **System is production-ready for live trading!**

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
