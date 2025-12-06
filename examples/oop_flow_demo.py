"""
TradingMTQ - OOP Architecture Flow Demo
Demonstrates the complete object-oriented design and data flow
"""
import sys
from datetime import datetime
from typing import List
import time

print("=" * 80)
print("  TRADINGMTQ - OOP ARCHITECTURE FLOW DEMO")
print("  Demonstrating: Design Patterns, Class Hierarchy, and Data Flow")
print("=" * 80)

# ============================================================================
# PHASE 1: IMPORT AND CLASS STRUCTURE
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 1: CLASS STRUCTURE & DESIGN PATTERNS")
print("=" * 80)

print("\n1️⃣  Base Classes (Abstract Layer)")
print("-" * 80)

from src.connectors.base import (
    BaseMetaTraderConnector,
    PlatformType, 
    OrderType,
    ConnectionStatus,
    TradeRequest,
    TradeResult
)

print("✓ BaseMetaTraderConnector (Abstract Base Class)")
print("  - Defines interface for all MT connectors")
print("  - Platform-agnostic design")
print("  - Enforces contract for implementations")

print("\n✓ Enum Classes:")
print(f"  - PlatformType: {[p.value for p in PlatformType]}")
print(f"  - OrderType: {[o.value for o in OrderType]}")
print(f"  - ConnectionStatus: {[c.value for c in ConnectionStatus]}")

print("\n✓ Data Classes (Dataclass Pattern):")
print("  - TradeRequest: Encapsulates order parameters")
print("  - TradeResult: Encapsulates execution results")
print("  - Position, TickData, OHLCBar, etc.")

# ============================================================================
# PHASE 2: FACTORY PATTERN
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 2: FACTORY PATTERN (Connector Creation)")
print("=" * 80)

from src.connectors import ConnectorFactory

print("\n2️⃣  Factory Pattern Implementation")
print("-" * 80)

print("✓ ConnectorFactory.create_connector()")
print("  - Centralizes object creation")
print("  - Manages multiple instances")
print("  - Returns appropriate implementation (MT5/MT4)")

# Create connector using factory
print("\n📦 Creating MT5 Connector via Factory...")
connector = ConnectorFactory.create_connector(
    platform=PlatformType.MT5,
    instance_id="demo_bot"
)

print(f"✓ Created: {connector.__class__.__name__}")
print(f"  - Instance ID: {connector.instance_id}")
print(f"  - Platform: {connector.platform.value}")
print(f"  - Status: {connector.status.value}")

# ============================================================================
# PHASE 3: CONNECTION MANAGEMENT
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 3: CONNECTION MANAGEMENT (State Pattern)")
print("=" * 80)

print("\n3️⃣  Connection Lifecycle")
print("-" * 80)

import os
from dotenv import load_dotenv

load_dotenv()
login = int(os.getenv('MT5_LOGIN', 0))
password = os.getenv('MT5_PASSWORD', '')
server = os.getenv('MT5_SERVER', '')

print(f"Initial State: {connector.status.value}")
print("\n🔌 Connecting to MT5...")

if connector.connect(login, password, server):
    print(f"✓ Connection established")
    print(f"  - New State: {connector.status.value}")
    print(f"  - Server: {server}")
else:
    print("✗ Connection failed")
    sys.exit(1)

# ============================================================================
# PHASE 4: DATA MODELS & RETRIEVAL
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 4: DATA MODELS (Value Objects)")
print("=" * 80)

print("\n4️⃣  Domain Objects")
print("-" * 80)

# Get account info
account = connector.get_account_info()
if account:
    print("\n✓ AccountInfo Object:")
    print(f"  Type: {type(account).__name__}")
    print(f"  Attributes:")
    print(f"    - login: {account.login}")
    print(f"    - balance: ${account.balance:,.2f}")
    print(f"    - equity: ${account.equity:,.2f}")
    print(f"    - leverage: 1:{account.leverage}")

# Get symbol info
symbol = "EURUSD"
symbol_info = connector.get_symbol_info(symbol)
if symbol_info:
    print(f"\n✓ SymbolInfo Object ({symbol}):")
    print(f"  Type: {type(symbol_info).__name__}")
    print(f"  Attributes:")
    print(f"    - bid: {symbol_info.bid:.5f}")
    print(f"    - ask: {symbol_info.ask:.5f}")
    print(f"    - spread: {symbol_info.spread}")
    print(f"    - volume_min: {symbol_info.volume_min}")

# Get market data
bars = connector.get_bars(symbol, 'M5', 10)
if bars:
    print(f"\n✓ OHLCBar Objects (List[OHLCBar]):")
    print(f"  Type: {type(bars).__name__}")
    print(f"  Count: {len(bars)}")
    print(f"  Latest Bar:")
    latest = bars[-1]
    print(f"    - time: {latest.time}")
    print(f"    - open: {latest.open:.5f}")
    print(f"    - high: {latest.high:.5f}")
    print(f"    - low: {latest.low:.5f}")
    print(f"    - close: {latest.close:.5f}")
    print(f"    - volume: {latest.volume}")

# ============================================================================
# PHASE 5: STRATEGY PATTERN
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 5: STRATEGY PATTERN (Polymorphic Behavior)")
print("=" * 80)

print("\n5️⃣  Strategy Abstraction")
print("-" * 80)

from src.strategies.base import BaseStrategy, Signal, SignalType
from src.strategies import SimpleMovingAverageStrategy

print("\n✓ BaseStrategy (Abstract Base Class)")
print("  - Defines analyze() interface")
print("  - All strategies inherit from this")
print("  - Polymorphic signal generation")

# Create strategy
strategy = SimpleMovingAverageStrategy({
    'fast_period': 10,
    'slow_period': 20,
    'sl_pips': 20,
    'tp_pips': 40
})

print(f"\n✓ Strategy Instance Created:")
print(f"  Type: {type(strategy).__name__}")
print(f"  Name: {strategy.name}")
print(f"  Parameters: {strategy.params}")

# Analyze market
print(f"\n📊 Analyzing market data...")
signal = strategy.analyze(symbol, 'M5', bars)

print(f"\n✓ Signal Object Generated:")
print(f"  Type: {type(signal).__name__}")
print(f"  Attributes:")
print(f"    - type: {signal.type.name}")
print(f"    - symbol: {signal.symbol}")
print(f"    - timestamp: {signal.timestamp}")
print(f"    - price: {signal.price:.5f}")
print(f"    - confidence: {signal.confidence:.1%}")
if signal.stop_loss:
    print(f"    - stop_loss: {signal.stop_loss:.5f}")
if signal.take_profit:
    print(f"    - take_profit: {signal.take_profit:.5f}")
print(f"    - reason: {signal.reason}")

# ============================================================================
# PHASE 6: RISK MANAGEMENT
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 6: RISK MANAGEMENT (Utility Classes)")
print("=" * 80)

print("\n6️⃣  AccountUtils (Static Methods)")
print("-" * 80)

from src.connectors.account_utils import AccountUtils

print("\n✓ Risk-Based Position Sizing:")

risk_percent = 1.0
mt5_order_type = 0  # BUY

if signal.type == SignalType.BUY and signal.stop_loss:
    lot_size = AccountUtils.risk_based_lot_size(
        symbol=symbol,
        order_type=mt5_order_type,
        entry_price=signal.price,
        stop_loss=signal.stop_loss,
        risk_percent=risk_percent
    )
    
    print(f"  Input:")
    print(f"    - Risk: {risk_percent}% of ${account.balance:,.2f} = ${account.balance * risk_percent / 100:,.2f}")
    print(f"    - Entry: {signal.price:.5f}")
    print(f"    - Stop Loss: {signal.stop_loss:.5f}")
    print(f"    - Distance: {abs(signal.price - signal.stop_loss):.5f}")
    
    if lot_size:
        print(f"  Output:")
        print(f"    - Calculated Lot Size: {lot_size:.2f} lots")
        
        # Calculate margin required
        margin = AccountUtils.calculate_margin_required(symbol, mt5_order_type, lot_size)
        if margin:
            print(f"    - Margin Required: ${margin:,.2f}")
            print(f"    - Free Margin After: ${account.margin_free - margin:,.2f}")

# ============================================================================
# PHASE 7: ORDER EXECUTION
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 7: ORDER EXECUTION (Command Pattern)")
print("=" * 80)

print("\n7️⃣  Trade Execution Flow")
print("-" * 80)

if signal.type != SignalType.HOLD and lot_size:
    print("\n✓ Creating TradeRequest (Value Object):")
    
    action = OrderType.BUY if signal.type == SignalType.BUY else OrderType.SELL
    
    trade_request = TradeRequest(
        symbol=symbol,
        action=action,
        volume=0.01,  # Small demo size
        price=signal.price,
        sl=signal.stop_loss,
        tp=signal.take_profit
    )
    
    print(f"  Type: {type(trade_request).__name__}")
    print(f"  Attributes:")
    print(f"    - symbol: {trade_request.symbol}")
    print(f"    - action: {trade_request.action.value}")
    print(f"    - volume: {trade_request.volume:.2f} lots")
    print(f"    - price: {trade_request.price:.5f}")
    print(f"    - sl: {trade_request.sl:.5f}")
    print(f"    - tp: {trade_request.tp:.5f}")
    
    print("\n⚠️  Trade Execution (Demo Mode - Not Executing)")
    print("  In production: connector.send_order(trade_request)")
    print("  Returns: TradeResult object")
    
    print("\n✓ TradeResult Structure:")
    print("  - success: bool")
    print("  - order_ticket: int")
    print("  - deal_ticket: int")
    print("  - volume: float")
    print("  - price: float")
    print("  - error_code: int")
    print("  - error_message: str")
else:
    print("\n⏸️  No trade signal - would wait for next opportunity")

# ============================================================================
# PHASE 8: BACKTESTING ENGINE
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 8: BACKTESTING ENGINE (Simulation)")
print("=" * 80)

print("\n8️⃣  Backtesting Architecture")
print("-" * 80)

from src.backtest.engine import BacktestEngine
from src.backtest.reporter import BacktestReporter

print("\n✓ BacktestEngine:")
print("  - Simulates historical trading")
print("  - Tracks virtual positions")
print("  - Calculates P&L with commission/slippage")

engine = BacktestEngine(
    initial_balance=10000.0,
    commission_pips=2.0,
    slippage_pips=1.0
)

print(f"\n  Initial Setup:")
print(f"    - Balance: ${engine.balance:,.2f}")
print(f"    - Commission: {engine.commission_pips} pips")
print(f"    - Slippage: {engine.slippage_pips} pips")

# Get more historical data
print(f"\n📊 Getting historical data for backtest...")
historical_bars = connector.get_bars(symbol, 'H1', 500)

if historical_bars and len(historical_bars) >= 100:
    print(f"✓ Retrieved {len(historical_bars)} bars")
    print(f"\n🔄 Running backtest...")
    
    metrics = engine.run(
        strategy=strategy,
        bars=historical_bars,
        symbol=symbol,
        timeframe='H1',
        volume=0.01
    )
    
    print(f"\n✓ BacktestMetrics Object:")
    print(f"  Type: {type(metrics).__name__}")
    print(f"  Results:")
    print(f"    - Total Trades: {metrics.total_trades}")
    print(f"    - Win Rate: {metrics.win_rate:.1f}%")
    print(f"    - Total Profit: ${metrics.total_profit:.2f}")
    print(f"    - Profit Factor: {metrics.profit_factor:.2f}")
    print(f"    - Max Drawdown: {metrics.max_drawdown:.2f}%")
    
    if metrics.total_trades > 0:
        print(f"    - Avg Profit/Trade: ${metrics.average_profit_per_trade:.2f}")

# ============================================================================
# PHASE 9: INDICATOR SYSTEM
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 9: INDICATOR SYSTEM (Composition)")
print("=" * 80)

print("\n9️⃣  Technical Indicators")
print("-" * 80)

from src.indicators.trend import SMA, EMA
from src.indicators.momentum import RSI
from src.indicators.volatility import BollingerBands, ATR

print("\n✓ Indicator Classes (BaseIndicator inheritance):")

# SMA
sma = SMA(period=20)
sma_values = sma.calculate(bars)
print(f"\n  - SMA(20): {type(sma).__name__}")
print(f"    Latest value: {sma_values[-1]:.5f}")

# EMA
ema = EMA(period=20)
ema_values = ema.calculate(bars)
print(f"\n  - EMA(20): {type(ema).__name__}")
print(f"    Latest value: {ema_values[-1]:.5f}")

# RSI
rsi = RSI(period=14)
rsi_values = rsi.calculate(bars)
print(f"\n  - RSI(14): {type(rsi).__name__}")
print(f"    Latest value: {rsi_values[-1]:.2f}")

# Bollinger Bands
bb = BollingerBands(period=20, std_dev=2.0)
bb_result = bb.calculate(bars)
print(f"\n  - BollingerBands: {type(bb).__name__}")
print(f"    Upper: {bb_result['upper'][-1]:.5f}")
print(f"    Middle: {bb_result['middle'][-1]:.5f}")
print(f"    Lower: {bb_result['lower'][-1]:.5f}")

# ATR
atr = ATR(period=14)
atr_values = atr.calculate(bars)
print(f"\n  - ATR(14): {type(atr).__name__}")
print(f"    Latest value: {atr_values[-1]:.5f}")

print("\n✓ All indicators inherit from BaseIndicator")
print("  - Consistent calculate() interface")
print("  - Polymorphic behavior")
print("  - Composable in strategies")

# ============================================================================
# PHASE 10: CONTROLLER PATTERN
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 10: CONTROLLER PATTERN (Orchestration)")
print("=" * 80)

print("\n🔟 TradingController")
print("-" * 80)

from src.trading.controller import TradingController

print("\n✓ TradingController (Facade Pattern):")
print("  - High-level trading operations")
print("  - Encapsulates complex logic")
print("  - Simplified API for clients")

controller = TradingController(connector)

print(f"\n  Instance created:")
print(f"    Type: {type(controller).__name__}")
print(f"    Connector: {type(controller.connector).__name__}")

print("\n  Available Methods:")
print("    - execute_trade()")
print("    - close_position()")
print("    - modify_position()")
print("    - get_open_positions()")
print("    - close_all_positions()")
print("    - get_account_summary()")

# Get account summary
summary = controller.get_account_summary()
print(f"\n  Account Summary:")
print(f"    - Balance: ${summary['balance']:,.2f}")
print(f"    - Equity: ${summary['equity']:,.2f}")
print(f"    - Margin: ${summary['margin']:,.2f}")
print(f"    - Free Margin: ${summary['free_margin']:,.2f}")
print(f"    - Open Positions: {summary['open_positions']}")
print(f"    - Total Profit: ${summary['profit']:,.2f}")

# Get positions
positions = controller.get_open_positions()
if positions:
    print(f"\n  Open Positions ({len(positions)}):")
    for pos in positions[:3]:  # Show first 3
        print(f"    - {pos.symbol}: {'BUY' if pos.type == 0 else 'SELL'} "
              f"{pos.volume:.2f} lots @ {pos.price_open:.5f} "
              f"(P/L: ${pos.profit:.2f})")

# ============================================================================
# PHASE 11: DATA FLOW SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 11: COMPLETE DATA FLOW")
print("=" * 80)

print("\n📊 End-to-End Object Flow:")
print("-" * 80)

print("""
1. Factory creates Connector
   ConnectorFactory → MT5Connector

2. Connector retrieves data
   MT5Connector.get_bars() → List[OHLCBar]

3. Strategy analyzes data
   BaseStrategy.analyze(bars) → Signal

4. Risk calculator sizes position
   AccountUtils.risk_based_lot_size() → float

5. Request object created
   TradeRequest(symbol, action, volume, ...)

6. Connector executes trade
   MT5Connector.send_order(request) → TradeResult

7. Controller manages lifecycle
   TradingController.execute_trade() → bool

8. Backtester simulates history
   BacktestEngine.run() → BacktestMetrics

9. Reporter analyzes results
   BacktestReporter.print_summary()
""")

# ============================================================================
# PHASE 12: DESIGN PATTERNS USED
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 12: DESIGN PATTERNS SUMMARY")
print("=" * 80)

print("\n🏗️  Object-Oriented Design Patterns:")
print("-" * 80)

patterns = {
    "Factory Pattern": "ConnectorFactory - Centralized object creation",
    "Strategy Pattern": "BaseStrategy, Signal - Pluggable algorithms",
    "Abstract Base Class": "BaseMetaTraderConnector - Interface definition",
    "Data Class": "TradeRequest, TradeResult - Value objects",
    "Singleton": "Config - Single configuration instance",
    "Facade": "TradingController - Simplified interface",
    "Command": "TradeRequest - Encapsulated requests",
    "State": "ConnectionStatus - State management",
    "Composition": "Indicators in Strategies - Has-a relationships",
    "Polymorphism": "Multiple strategies, same interface"
}

for pattern, description in patterns.items():
    print(f"\n  ✓ {pattern}")
    print(f"    {description}")

# ============================================================================
# CLEANUP
# ============================================================================

print("\n" + "=" * 80)
print("CLEANUP & SUMMARY")
print("=" * 80)

print("\n🧹 Disconnecting...")
connector.disconnect()
print(f"✓ Connection closed")
print(f"  Final State: {connector.status.value}")

print("\n" + "=" * 80)
print("📚 KEY TAKEAWAYS")
print("=" * 80)

print("""
✅ Clean Architecture:
   - Separation of concerns (connectors, strategies, indicators)
   - Interface-based design (abstract base classes)
   - Dependency injection (connector passed to controller)

✅ SOLID Principles:
   - Single Responsibility (each class has one job)
   - Open/Closed (extend via inheritance, not modification)
   - Liskov Substitution (strategies are interchangeable)
   - Interface Segregation (focused interfaces)
   - Dependency Inversion (depend on abstractions)

✅ Testability:
   - Mock-friendly interfaces
   - Dependency injection
   - Isolated components

✅ Maintainability:
   - Clear class hierarchy
   - Consistent naming
   - Type hints throughout
   - Comprehensive docstrings

✅ Extensibility:
   - Add new strategies (inherit BaseStrategy)
   - Add new indicators (inherit BaseIndicator)
   - Add new connectors (inherit BaseMetaTraderConnector)
   - Add new platforms (extend PlatformType)
""")

print("\n" + "=" * 80)
print("  DEMO COMPLETE!")
print("=" * 80)

print("\n💡 Next Steps:")
print("  - Review the source code in src/")
print("  - Check tests/ for unit test examples")
print("  - Read START_HERE.md for full documentation")
print("  - Run python run.py for live trading")

print("\n" + "=" * 80)
