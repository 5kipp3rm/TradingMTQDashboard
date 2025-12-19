Here’s a **project-specific** version for **`tradingmtq`**, based on your repo tree, with the same “Project Memory” workflow + the added **(D) Dependencies & delivery** section.

---

## Long prompt (TradingMTQ-specific)

```text
You are a senior engineer doing a pre-work codebase analysis for a project named “tradingmtq”.

I will paste files from this repo in chunks (start with entrypoints + bootstrap + config + DB, then core trading/strategies, then ML/LLM/backtest, then API/UI/integrations).
Your goal is to build a reusable “Project Memory” summary so we can safely implement changes.

Repo map (context, don’t assume behavior until you see code):
- src/
  - cli/                 (CLI entrypoints, commands, args validation)
  - api/                 (REST/Web API server, routes, request/response models)
  - config/              (settings loader, env/files precedence, defaults)
  - database/            (DB engine/session/repositories; Alembic is in /alembic)
  - connectors/          (MetaTrader / broker / exchange connectors, adapters)
  - trading/             (order execution, position mgmt, risk mgmt, event loop)
  - strategies/          (strategy logic, signal generation, decision rules)
  - indicators/          (TA indicators, feature builders)
  - backtest/            (historical simulation, fill models, metrics)
  - optimization/        (parameter sweeps, tuning, experimentation)
  - ml/ + llm/           (models, training/inference, prompts/agents, pipelines)
  - analytics/ + analysis/ (analysis utilities, dashboards/insights, reporting)
  - notifications/       (alerts: email/telegram/webhooks/etc.)
  - reports/             (report generation, exports)
  - services/            (service layer / orchestration / business workflows)
  - utils/               (logging, helpers, shared tooling)
- alembic/               (migrations, schema evolution)
- dashboard/             (static dashboard assets: css/js)
- data/                  (raw/processed/models datasets)
- deploy/                (windows/macos packaging, scripts)
- docs/                  (design/architecture/phases/guides + API docs)
- scripts/               (maintenance, tooling, run helpers)
- tests/                 (unit/integration tests)

Tasks (produce outputs in this order):
1) TL;DR (5–10 bullets): what tradingmtq does end-to-end (user + system view).
2) Architecture / flow diagram (Mermaid preferred; ASCII ok):
   CLI/API/UI → config bootstrap → DB/init → connectors → strategy engine →
   trading/execution → persistence → reporting/notifications → shutdown.
3) Entrypoints & runtime:
   - Identify exact entry files/modules (CLI main, API server main, workers/schedulers).
   - Explain how each mode runs: CLI commands, API startup, background jobs.
4) Key abstractions & responsibilities:
   - Core classes/functions (Trader/Engine/Executor/Strategy/Connector/Repository/etc.)
   - How data flows between them (signals → orders → executions → positions → P&L).
5) Configuration model:
   - Where config comes from (env/files/CLI flags/secrets)
   - Precedence rules and default profiles (paper/live/backtest, aggressive/conservative, etc.)
6) (D) Dependencies & delivery (build/deploy/CI):
   - Packaging (pyproject/setup, requirements, lockfiles)
   - Runtime deps (DB, broker terminal, API keys, GPU/ML libs if relevant)
   - Deployment artifacts (deploy/windows, deploy/macos, Dockerfile if exists)
   - CI/CD and release/versioning (if present)
   - Local dev workflow: run, test, lint, migrations, dashboard/dev server
7) Data & results pipeline:
   - What inputs exist (market data, account state, configs)
   - What outputs exist (orders, trades, positions, reports, alerts, stored metrics)
   - Backtest outputs vs live outputs (differences, assumptions)
8) Error handling & observability:
   - Logging strategy, metrics/tracing, retries/timeouts, circuit breakers
   - Failure modes (connector disconnects, order rejects, DB errors, partial fills)
9) Extension points (step-by-step, concrete):
   - Add a new strategy
   - Add a new connector/broker adapter
   - Add a new indicator/feature
   - Add a new notification channel
   - Add a new config option that affects runtime behavior end-to-end
10) Hotspots & risks:
   - Tight coupling, global state, hidden IO, concurrency assumptions,
     risk mgmt gaps, money-safety issues, testing gaps, security footguns.
11) End with a Project Memory block (250–500 words) I can paste into future chats.

Rules:
- For every important claim, cite “file path + symbol name” (function/class).
- If something is missing, list assumptions + what to verify next (don’t stall).
- Ignore generated artifacts (__pycache__, htmlcov, egg-info, venv, logs output files).
- Be concise, bullet-heavy, and implementation-oriented.

Start by telling me the exact first 6–10 files you want to read.
Prioritize:
- CLI/API entrypoints
- config loader + defaults
- database init + Alembic env
- trading engine/executor core loop
- connector base + one concrete connector
Then begin analysis as soon as I paste them.
```

---

## Short prompt (TradingMTQ-specific)

```text
Analyze the code I paste from “tradingmtq” and produce a reusable Project Memory summary.

Output in this order:
1) What it is / does (5–8 bullets).
2) Execution flow (Mermaid/ASCII): CLI/API/UI → config → DB/init → connectors → strategies → trading/execution → persistence → reports/notifications.
3) Key components & responsibilities: src/{cli,api,config,database,connectors,trading,strategies,indicators,backtest,optimization,ml,llm,notifications,reports,services,utils} + alembic.
4) Entrypoints & runtime: how it starts, modes (live/paper/backtest), CLI args/env/config precedence.
5) (D) Dependencies & delivery: packaging, runtime deps (DB/broker), deploy artifacts, CI/CD (if any), local dev workflow.
6) Results pipeline: trades/positions/P&L, reports, alerts; backtest vs live differences.
7) Extension points: add strategy + connector + indicator + notification channel (step-by-step).
8) Hotspots/risks: coupling, error handling, concurrency, money-safety, testing gaps.
9) End with a Project Memory block (250–500 words).

Rules: cite file path + symbol name for each major claim; list assumptions; ignore __pycache__/venv/htmlcov/egg-info.
Start by telling me the first 6–10 files you want me to paste, then begin analysis immediately.
```

---

### Suggested “first 6–10 files” to paste (so we start strong)

If these exist, they’re usually the best starting set:

1. `pyproject.toml` **or** `setup.py` **or** `requirements.txt` (packaging/deps)
2. `src/cli/*` (the main CLI entrypoint file)
3. `src/api/*` (API server entrypoint, routes registration)
4. `src/config/*` (settings loader + defaults)
5. `src/database/*` (engine/session init + repositories)
6. `alembic/env.py` (migration wiring)
7. `src/trading/*` (engine/executor main loop)
8. `src/connectors/*` (base connector + one concrete broker/MT connector)
9. `src/strategies/*` (base strategy + one concrete strategy)
10. `src/utils/logging*` (logging/observability setup)

If you paste those, I can generate the first “Project Memory” pass immediately.
###

```mermaid
graph TD
    subgraph "Entrypoints"
        A[CLI: main.py or tradingmtq CLI] -->|trade| B[run_trading]
        A -->|serve| C[FastAPI App]
        A -->|aggregate| D[DailyAggregator]
    end

    subgraph "Bootstrap & Config"
        B --> E[load_dotenv + env vars]
        B --> F[ConfigurationManager: config/currencies.yaml]
        C --> E
    end

    subgraph "Database Layer"
        E --> G[init_db: SQLAlchemy engine + Base.metadata.create_all]
        G --> H[(SQLite / PostgreSQL)]
        H -.-> I[Trade, Signal, AccountSnapshot, DailyPerformance models]
    end

    subgraph "Connector / Broker Layer"
        F --> J[ConnectorFactory.create_connector]
        J --> K{PlatformType?}
        K -->|MT5| L[MT5Connector: connect via mt5.initialize]
        K -->|MT4| M[MT4Connector: socket bridge to MQL4]
        L --> N[MT5 Terminal / Broker API]
    end

    subgraph "Orchestrator / Trading Loop"
        B --> O[MultiCurrencyOrchestrator]
        O --> P[add_currency per config]
        P --> Q[CurrencyTrader per symbol]
        O --> R[process_single_cycle / process_parallel_cycle]
    end

    subgraph "Signal Generation & Execution"
        R --> S[CurrencyTrader.process_cycle]
        S --> T[analyze_market: fetch bars via connector]
        T --> U{use_position_trading?}
        U -->|Yes| V[Fast/Slow MA position logic]
        U -->|No| W[Strategy.analyze: crossover detection]
        
        V --> X[Optional: ML enhancement]
        W --> X
        X --> Y{ML agrees?}
        Y -->|Yes| Z[Boost confidence]
        Y -->|No| AA[Reduce confidence or ML override]
        
        Z --> AB[Optional: LLM sentiment filter]
        AA --> AB
        AB --> AC[Signal: type, price, SL, TP, confidence]
        
        AC --> AD{should_execute_signal?}
        AD -->|cooldown/stacking checks| AE[execute_trade]
        AE --> AF[calculate_lot_size: risk-based via AccountUtils]
        AF --> AG[connector.send_order]
        AG --> AH{Success?}
        AH -->|Yes| AI[Save Trade to DB]
        AH -->|No| AJ[Log error + raise OrderExecutionError]
    end

    subgraph "Position Management"
        R --> AK[PositionManager.process_all_positions]
        AK --> AL{Check SL/TP rules?}
        AL -->|Breakeven| AM[Move SL to entry + offset]
        AL -->|Trailing| AN[Update SL following price]
        AL -->|Partial Close| AO[Close X% at profit target]
        
        R --> AP[Optional: IntelligentPositionManager AI analysis]
        AP --> AQ[analyze_portfolio: ML + risk scoring]
        AQ --> AR[Close losing positions if confidence low]
    end

    subgraph "Persistence & Reporting"
        AI --> AS[TradeRepository.create]
        AC --> AT[SignalRepository.create]
        R --> AU[AccountSnapshotRepository.create every cycle]
        
        D --> AV[Query Trade history]
        AV --> AW[Aggregate daily metrics: win_rate, profit_factor, etc.]
        AW --> AX[DailyPerformanceRepository.create]
    end

    subgraph "API / Dashboard"
        C --> AY[FastAPI routers: /api/analytics, /api/trades, /api/positions]
        AY --> AZ[Query repositories via get_db_dependency]
        AZ --> BA[JSON responses + WebSocket events]
        C --> BB[Static Files: dashboard/ HTML/CSS/JS]
    end

    subgraph "Notifications"
        AI --> BC[WebSocket: connection_manager.broadcast]
        R --> BD[Email alerts if configured]
    end

    subgraph "Shutdown"
        BE[KeyboardInterrupt or API shutdown] --> BF[trading_bot_service.stop]
        BF --> BG[orchestrator.print_final_statistics]
        BG --> BH[connector.disconnect]
        BH --> BI[close_db]
    end
```