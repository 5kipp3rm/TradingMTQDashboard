"""
Demo: Multi-Currency OOP Architecture
Shows how each currency is its own object with independent configuration
"""

print("=" * 80)
print("  MULTI-CURRENCY OOP ARCHITECTURE DEMO")
print("=" * 80)

print("\n📚 ARCHITECTURE OVERVIEW")
print("-" * 80)

print("""
┌─────────────────────────────────────────────────────────────────┐
│                  MultiCurrencyOrchestrator                      │
│  (Main controller - orchestrates all currency traders)         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ manages
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  CurrencyTrader  │  │  CurrencyTrader  │  │  CurrencyTrader  │
│     (EURUSD)     │  │     (GBPUSD)     │  │     (USDJPY)     │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ • Own Strategy   │  │ • Own Strategy   │  │ • Own Strategy   │
│ • Own Risk %     │  │ • Own Risk %     │  │ • Own Risk %     │
│ • Own State      │  │ • Own State      │  │ • Own State      │
│ • Own SL/TP      │  │ • Own SL/TP      │  │ • Own SL/TP      │
│ • Own Cooldown   │  │ • Own Cooldown   │  │ • Own Cooldown   │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        │                     │                     │
        │ shares              │ shares              │ shares
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  MT5 Connector   │
                    │  (Shared)        │
                    └──────────────────┘
""")

print("\n🏗️  KEY DESIGN PATTERNS")
print("-" * 80)

print("\n1. COMPOSITE PATTERN:")
print("   - Orchestrator contains multiple CurrencyTrader objects")
print("   - Each trader is independent but managed centrally")

print("\n2. STRATEGY PATTERN:")
print("   - Each currency can use different strategy")
print("   - Position Trading vs Crossover")
print("   - Different MA periods per pair")

print("\n3. CONFIGURATION OBJECT:")
print("   - CurrencyTraderConfig dataclass")
print("   - Type-safe configuration")
print("   - Easy to serialize/deserialize")

print("\n4. DEPENDENCY INJECTION:")
print("   - Connector injected into orchestrator")
print("   - Shared across all traders")
print("   - Easy to mock for testing")

print("\n" + "=" * 80)
print("  CODE EXAMPLE")
print("=" * 80)

print("""
# Create orchestrator (main controller)
orchestrator = MultiCurrencyOrchestrator(
    connector=connector,
    max_concurrent_trades=5,
    portfolio_risk_percent=10.0
)

# Each currency is a separate object with different config
eurusd_config = CurrencyTraderConfig(
    symbol='EURUSD',
    strategy=SimpleMovingAverageStrategy({'fast': 10, 'slow': 20}),
    risk_percent=1.0,      # EURUSD: 1% risk
    sl_pips=20,
    tp_pips=40,
    use_position_trading=True
)

gbpusd_config = CurrencyTraderConfig(
    symbol='GBPUSD',
    strategy=SimpleMovingAverageStrategy({'fast': 8, 'slow': 21}),
    risk_percent=0.8,      # GBPUSD: 0.8% risk (more volatile)
    sl_pips=25,
    tp_pips=50,
    use_position_trading=True
)

xauusd_config = CurrencyTraderConfig(
    symbol='XAUUSD',
    strategy=SimpleMovingAverageStrategy({'fast': 20, 'slow': 50}),
    risk_percent=0.5,      # XAUUSD: 0.5% risk (very volatile)
    sl_pips=50,
    tp_pips=100,
    use_position_trading=False  # Different mode!
)

# Add currencies (each becomes its own object)
orchestrator.add_currency(eurusd_config)  # Creates CurrencyTrader #1
orchestrator.add_currency(gbpusd_config)  # Creates CurrencyTrader #2
orchestrator.add_currency(xauusd_config)  # Creates CurrencyTrader #3

# Run - orchestrator manages all traders
orchestrator.run_continuous(interval_seconds=30, parallel=False)
""")

print("\n" + "=" * 80)
print("  BENEFITS OF THIS ARCHITECTURE")
print("=" * 80)

benefits = {
    "✓ Independence": "Each currency trades with own parameters",
    "✓ Isolation": "Error in one pair doesn't affect others",
    "✓ Flexibility": "Mix strategies (position/crossover/custom)",
    "✓ Risk Management": "Different risk % per currency + portfolio limit",
    "✓ Scalability": "Easy to add/remove currencies",
    "✓ Testability": "Test individual currency traders separately",
    "✓ Maintainability": "Clear separation of concerns",
    "✓ Parallelization": "Can run currencies in parallel threads",
    "✓ Monitoring": "Per-currency statistics and performance",
    "✓ Configuration": "Each currency has own SL/TP/cooldown/etc"
}

for benefit, description in benefits.items():
    print(f"\n{benefit}")
    print(f"  {description}")

print("\n" + "=" * 80)
print("  OBJECT HIERARCHY")
print("=" * 80)

print("""
MultiCurrencyOrchestrator
├── traders: Dict[str, CurrencyTrader]
│   ├── "EURUSD" → CurrencyTrader
│   │   ├── config: CurrencyTraderConfig
│   │   │   ├── symbol: "EURUSD"
│   │   │   ├── strategy: SimpleMovingAverageStrategy
│   │   │   ├── risk_percent: 1.0
│   │   │   ├── sl_pips: 20
│   │   │   ├── tp_pips: 40
│   │   │   └── use_position_trading: True
│   │   ├── connector: MT5Connector (shared)
│   │   ├── last_signal: Signal (state)
│   │   ├── last_trade_time: datetime (state)
│   │   └── statistics: Dict
│   │
│   ├── "GBPUSD" → CurrencyTrader
│   │   ├── config: CurrencyTraderConfig
│   │   │   ├── symbol: "GBPUSD"
│   │   │   ├── strategy: SimpleMovingAverageStrategy
│   │   │   ├── risk_percent: 0.8  ← Different!
│   │   │   ├── sl_pips: 25         ← Different!
│   │   │   └── ...
│   │   └── ... (own state)
│   │
│   └── "XAUUSD" → CurrencyTrader
│       ├── config: CurrencyTraderConfig
│       │   ├── risk_percent: 0.5   ← Different!
│       │   ├── use_position_trading: False  ← Different mode!
│       │   └── ...
│       └── ... (own state)
│
├── connector: MT5Connector (shared reference)
├── max_concurrent_trades: 5
└── portfolio_risk_percent: 10.0
""")

print("\n" + "=" * 80)
print("  STATE MANAGEMENT")
print("=" * 80)

print("""
Each CurrencyTrader maintains its own state:

EURUSD Trader State:
  last_signal = BUY @ 1.16234
  last_trade_time = 2025-12-03 10:30:15
  last_signal_type = SignalType.BUY
  total_trades = 5
  successful_trades = 4

GBPUSD Trader State:  ← Completely independent!
  last_signal = SELL @ 1.25678
  last_trade_time = 2025-12-03 10:29:45
  last_signal_type = SignalType.SELL
  total_trades = 3
  successful_trades = 2

XAUUSD Trader State:  ← Also independent!
  last_signal = HOLD @ 2045.50
  last_trade_time = 2025-12-03 10:15:30
  last_signal_type = SignalType.BUY
  total_trades = 1
  successful_trades = 1
""")

print("\n" + "=" * 80)
print("  EXECUTION FLOW")
print("=" * 80)

print("""
1. Orchestrator.run_continuous() starts main loop

2. Each cycle:
   for each CurrencyTrader in traders:
       ├─ trader.analyze_market()
       │   └─ Get bars → Calculate indicators → Generate Signal
       │
       ├─ trader.should_execute_signal(signal)
       │   ├─ Check: signal != HOLD?
       │   ├─ Check: cooldown period passed?
       │   └─ Check: signal changed? (position mode)
       │
       ├─ trader.calculate_lot_size(signal)
       │   └─ Risk-based calculation (uses currency's risk_percent)
       │
       └─ trader.execute_trade(signal)
           ├─ Create TradeRequest
           ├─ Call connector.send_order()
           └─ Update trader state
   
   Sleep(interval_seconds)

3. On KeyboardInterrupt:
   └─ Print statistics for each trader
""")

print("\n" + "=" * 80)
print("  USAGE EXAMPLES")
print("=" * 80)

print("""
# Get specific trader
eurusd_trader = orchestrator.get_trader('EURUSD')
stats = eurusd_trader.get_statistics()
print(f"EURUSD Win Rate: {stats['win_rate']:.1f}%")

# Get all statistics
all_stats = orchestrator.get_all_statistics()
for symbol, stats in all_stats.items():
    print(f"{symbol}: {stats['total_trades']} trades")

# Remove a currency
orchestrator.remove_currency('BTCUSD')

# Check position limit
if orchestrator.can_open_new_position():
    print("Can open new trade")

# Run in parallel mode (faster)
orchestrator.run_continuous(
    interval_seconds=30,
    parallel=True,      # ← Run currencies in parallel threads
    max_cycles=100      # ← Stop after 100 cycles
)
""")

print("\n" + "=" * 80)
print("  FILES CREATED")
print("=" * 80)

print("""
✓ src/trading/currency_trader.py
  - CurrencyTrader class
  - CurrencyTraderConfig dataclass
  - Per-currency trading logic

✓ src/trading/orchestrator.py
  - MultiCurrencyOrchestrator class
  - Portfolio management
  - Parallel/sequential execution

✓ run_multi_currency.py
  - Example usage script
  - 5 currencies with different configs
  - Ready to run

✓ src/trading/__init__.py
  - Updated exports
""")

print("\n" + "=" * 80)
print("  NEXT STEPS")
print("=" * 80)

print("""
1. Run the demo:
   python run_multi_currency.py

2. Customize currencies in run_multi_currency.py:
   - Add/remove pairs
   - Adjust risk percentages
   - Change strategy parameters
   - Mix position/crossover modes

3. Create your own configurations:
   - Different strategies per currency
   - Dynamic parameter adjustment
   - Time-based configs (day vs night)

4. Extend the system:
   - Add portfolio correlation analysis
   - Implement drawdown protection
   - Add currency-specific filters
   - Create custom CurrencyTrader subclasses
""")

print("\n" + "=" * 80)
print("  DEMO COMPLETE!")
print("=" * 80)
print()
