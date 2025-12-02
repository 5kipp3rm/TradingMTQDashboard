# TradingMTQ - AI-Powered MetaTrader Currency Trading Platform

## Project Overview

TradingMTQ is an intelligent trading application that connects to MetaTrader to execute currency trades based on AI/LLM-driven decision logic. The system analyzes market data and executes buy/sell operations automatically or with user approval.

## Project Goals

1. **Phase 1 (MVP)**: Establish MetaTrader connection and basic trading functionality
   - Connect to MetaTrader 5 (MT5) via API
   - Display available currency pairs
   - Execute manual buy/sell orders
   - Monitor positions and account status

2. **Phase 2**: Implement AI/LLM Trading Logic
   - Integrate machine learning models for price prediction
   - Implement LLM-based market sentiment analysis
   - Create automated trading strategies
   - Backtesting framework

3. **Phase 3**: Advanced Features
   - Risk management system
   - Portfolio optimization
   - Real-time notifications
   - Trading analytics dashboard

## Technology Stack

- **MetaTrader Integration**: MT5 Python API (MetaTrader5 package)
- **Backend**: Python 3.10+
- **AI/ML**: TensorFlow/PyTorch, scikit-learn
- **LLM**: OpenAI API, LangChain
- **Frontend**: React/Next.js (future)
- **Database**: PostgreSQL (for trade history)
- **Visualization**: Plotly, Matplotlib

## Documentation Structure

- `design/` - System architecture and design documents
- `build/` - Implementation guides and build phases
- `api/` - API specifications and integration docs
- `deployment/` - Deployment and configuration guides

## Getting Started

See `build/phase1-implementation.md` for initial setup instructions.

## Repository Structure

```
TradingMTQ/
├── docs/              # Documentation
│   ├── design/        # Architecture & design
│   ├── build/         # Build phases & guides
│   └── api/           # API specifications
├── src/               # Source code
│   ├── connectors/    # MetaTrader connection
│   ├── trading/       # Trading logic
│   ├── ai/            # AI/ML models
│   └── utils/         # Utilities
├── tests/             # Test suites
├── config/            # Configuration files
└── data/              # Historical data & models
```
