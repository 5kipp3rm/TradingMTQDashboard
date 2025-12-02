# System Architecture - TradingMTQ

## Architecture Overview

TradingMTQ follows a modular, event-driven architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│              (CLI → Web Dashboard → Mobile)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Trading    │  │  AI/ML       │  │  Risk        │      │
│  │   Engine     │  │  Decision    │  │  Management  │      │
│  │              │  │  Engine      │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│                    Service Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Market Data │  │  Order       │  │  Portfolio   │      │
│  │  Service     │  │  Management  │  │  Service     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│              MetaTrader Connector Layer                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         MT5 Python API Integration                   │   │
│  │  • Connection Management  • Order Execution          │   │
│  │  • Market Data Streaming  • Account Management       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              MetaTrader 5 Terminal                           │
│                   (External System)                          │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. MetaTrader Connector Layer

**Purpose**: Bridge between TradingMTQ and MetaTrader 5 terminal

**Responsibilities**:
- Establish and maintain MT5 connection
- Handle authentication and session management
- Stream real-time market data
- Execute trading orders
- Retrieve account information and history

**Key Classes**:
- `MT5Connector`: Main connection handler
- `MarketDataStream`: Real-time price feed
- `OrderExecutor`: Trade execution interface
- `AccountManager`: Account info and balance tracking

**Dependencies**:
- MetaTrader5 Python package
- MT5 terminal running locally or on accessible server

### 2. Market Data Service

**Purpose**: Process and distribute market data to application components

**Responsibilities**:
- Normalize data from MT5
- Cache historical data
- Provide real-time price updates
- Calculate technical indicators
- Maintain tick/candle data

**Key Features**:
- Support for multiple timeframes (M1, M5, H1, D1, etc.)
- On-demand technical indicator calculation (RSI, MACD, Bollinger Bands)
- Event-driven price notifications

### 3. Trading Engine

**Purpose**: Core trading logic and decision execution

**Responsibilities**:
- Receive trading signals (manual or AI-generated)
- Validate trading conditions
- Execute orders through MT5 connector
- Track open positions
- Manage stop-loss and take-profit

**Trading Modes**:
- **Manual Mode**: User-initiated trades
- **Semi-Automated**: AI suggestions with user approval
- **Fully Automated**: AI-driven autonomous trading

### 4. AI/ML Decision Engine (Phase 2+)

**Purpose**: Generate trading signals using AI/LLM models

**Components**:

**a) Price Prediction Models**
- LSTM/GRU neural networks for price forecasting
- Random Forest for pattern recognition
- XGBoost for trend classification

**b) LLM Analysis**
- Market sentiment from news/social media
- Pattern recognition from chart descriptions
- Strategy generation and optimization

**c) Signal Generator**
- Combine multiple model outputs
- Calculate confidence scores
- Generate buy/sell/hold signals

### 5. Risk Management System

**Purpose**: Protect capital and enforce trading rules

**Features**:
- Position sizing calculations
- Maximum drawdown limits
- Daily/weekly loss limits
- Correlation-based exposure management
- Emergency stop mechanisms

### 6. Portfolio Service

**Purpose**: Track and analyze trading performance

**Capabilities**:
- Real-time P&L calculation
- Trade history and analytics
- Performance metrics (Sharpe ratio, win rate, etc.)
- Portfolio composition analysis

## Data Flow

### Real-Time Trading Flow

```
1. MT5 Terminal → Market Data Event
2. MT5Connector → Receives tick data
3. MarketDataService → Processes & distributes
4. AI Decision Engine → Analyzes data
5. Trading Engine → Validates signal
6. Risk Management → Approves/rejects
7. Order Executor → Sends order to MT5
8. MT5 Terminal → Executes trade
9. Portfolio Service → Updates positions
```

### Historical Data Analysis Flow

```
1. Request historical data (symbol, timeframe, range)
2. MT5Connector → Fetch from MT5
3. Cache in local database
4. Calculate technical indicators
5. Feed to AI models for training/backtesting
6. Generate insights and strategies
```

## Technology Decisions

### Why MetaTrader 5?

- Industry-standard retail forex platform
- Robust Python API (MetaTrader5 package)
- Access to wide range of brokers
- Built-in backtesting capabilities
- Free to use with broker accounts

### Why Python?

- Excellent ML/AI library ecosystem
- Native MT5 API support
- Rapid development and prototyping
- Strong community for trading applications

### Database Strategy

- **PostgreSQL**: Trade history, user settings, performance logs
- **Redis**: Real-time market data cache, session management
- **InfluxDB** (future): Time-series tick data for advanced analytics

## Scalability Considerations

### Phase 1 (MVP)
- Single-threaded, single-currency trading
- Local MT5 connection only
- Simple file-based configuration

### Phase 2 (Growth)
- Multi-threaded market data processing
- Support for multiple currency pairs
- Database-backed persistence
- Basic web dashboard

### Phase 3 (Scale)
- Microservices architecture
- Distributed backtesting
- Cloud deployment options
- Multiple broker/account support

## Security Considerations

1. **Credential Management**: Store MT5 credentials securely (environment variables, vault)
2. **API Keys**: Encrypt LLM API keys (OpenAI, etc.)
3. **Trade Validation**: Multi-layer validation before order execution
4. **Audit Logging**: Complete audit trail of all trading decisions
5. **Error Handling**: Graceful degradation on connection failures

## Deployment Architecture (Future)

```
┌──────────────────────────────────────────────┐
│           Cloud Infrastructure                │
│  ┌────────────┐      ┌──────────────┐        │
│  │   Web UI   │      │  API Server  │        │
│  │  (Next.js) │─────▶│  (FastAPI)   │        │
│  └────────────┘      └──────┬───────┘        │
│                              │                │
│  ┌────────────┐      ┌──────▼───────┐        │
│  │ PostgreSQL │◀─────│   Trading    │        │
│  │  Database  │      │   Engine     │        │
│  └────────────┘      └──────┬───────┘        │
└────────────────────────────┬┼───────────────┘
                             ││
                    ┌────────▼▼────────┐
                    │  Local Machine    │
                    │  ┌─────────────┐  │
                    │  │ MT5 Terminal│  │
                    │  │  + Broker   │  │
                    │  └─────────────┘  │
                    └───────────────────┘
```

## Integration Points

### External Services (Phase 2+)

1. **LLM APIs**: OpenAI GPT-4, Anthropic Claude
2. **News APIs**: Alpha Vantage, NewsAPI
3. **Market Data**: Yahoo Finance, Twelve Data (backup/supplement)
4. **Notifications**: Telegram, Discord, Email
5. **Cloud Storage**: AWS S3 for model artifacts

## Error Handling Strategy

1. **Connection Errors**: Auto-retry with exponential backoff
2. **Order Failures**: Log, alert, and provide manual intervention
3. **Data Gaps**: Fallback to cached data or pause trading
4. **AI Model Errors**: Revert to rule-based trading or manual mode
5. **Critical Failures**: Emergency position closing mechanism

## Monitoring & Observability

- **Logging**: Structured logging (JSON) with multiple levels
- **Metrics**: Trading performance, system health, API latency
- **Alerting**: Critical errors, large losses, connection issues
- **Dashboards**: Real-time trading status, P&L, system metrics
