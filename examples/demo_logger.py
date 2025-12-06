"""
Demo: Enhanced Logging System
Shows the improved logger with colors, emojis, and structured output
"""
from src.utils.logger import (
    setup_logging, 
    get_logger,
    log_trade,
    log_signal,
    log_connection,
    log_config,
    log_cycle
)
import time

# Initialize logging system
print("Initializing enhanced logging system...\n")
setup_logging(log_dir="logs", log_level="DEBUG")

# Get logger instances
logger = get_logger(__name__)
mt5_logger = get_logger("MT5Connector")
strategy_logger = get_logger("Strategy")
orchestrator_logger = get_logger("Orchestrator")

print("\n" + "=" * 80)
print("  ENHANCED LOGGING SYSTEM DEMO")
print("=" * 80 + "\n")

# 1. Connection Events
print("\n1️⃣  CONNECTION EVENTS")
print("-" * 80)
log_connection(logger, "STARTED", "MetaTrader 5 Build 5450")
time.sleep(0.5)
log_connection(logger, "ESTABLISHED", "Server: MetaQuotes-Demo")
time.sleep(0.5)
mt5_logger.info("Account: #51234567, Balance: $99,999.51")

# 2. Configuration Events
print("\n2️⃣  CONFIGURATION EVENTS")
print("-" * 80)
log_config(logger, "Loading configuration from config/currencies.yaml")
time.sleep(0.5)
log_config(logger, "Enabled currencies: EURUSD, GBPUSD, USDJPY, XAUUSD")
time.sleep(0.5)
log_config(logger, "Max concurrent trades: 5, Portfolio risk: 10%")

# 3. Trading Cycle
print("\n3️⃣  TRADING CYCLE")
print("-" * 80)
log_cycle(orchestrator_logger, 1, "Started - Processing 6 currencies")
time.sleep(0.5)

# 4. Signal Generation
print("\n4️⃣  SIGNAL GENERATION")
print("-" * 80)
log_signal(strategy_logger, "EURUSD", "BUY", 1.16234, 0.75)
time.sleep(0.3)
log_signal(strategy_logger, "GBPUSD", "SELL", 1.25678, 0.82)
time.sleep(0.3)
log_signal(strategy_logger, "USDJPY", "HOLD", 142.543, 0.0)
time.sleep(0.3)
log_signal(strategy_logger, "XAUUSD", "BUY", 2045.80, 0.68)

# 5. Trade Execution
print("\n5️⃣  TRADE EXECUTION")
print("-" * 80)
log_trade(mt5_logger, "EURUSD", "BUY", 0.10, 1.16234, 54195785173)
time.sleep(0.5)
log_trade(mt5_logger, "GBPUSD", "SELL", 0.08, 1.25678, 54195785174)
time.sleep(0.5)
log_trade(mt5_logger, "XAUUSD", "BUY", 0.03, 2045.80, 54195785175)

# 6. Different Log Levels
print("\n6️⃣  DIFFERENT LOG LEVELS")
print("-" * 80)
logger.debug("Debug message: Analyzing 100 bars for EURUSD M5")
time.sleep(0.3)
logger.info("Info message: Position opened successfully")
time.sleep(0.3)
logger.warning("Warning message: High spread detected (3.5 pips)")
time.sleep(0.3)
logger.error("Error message: Failed to get symbol info for BTCUSD")
time.sleep(0.3)
logger.critical("Critical message: EMERGENCY STOP ACTIVATED")

# 7. Symbol Context
print("\n7️⃣  SYMBOL-SPECIFIC LOGGING")
print("-" * 80)
logger.info("Fast MA (10): 1.16221, Slow MA (20): 1.16189", extra={'symbol': 'EURUSD'})
time.sleep(0.3)
logger.info("Spread: 2.5 pips, Volume: 0.10 lots", extra={'symbol': 'GBPUSD'})
time.sleep(0.3)
logger.warning("Volatility spike detected - widening stops", extra={'symbol': 'XAUUSD'})

# 8. Cycle Completion
print("\n8️⃣  CYCLE COMPLETION")
print("-" * 80)
log_cycle(orchestrator_logger, 1, "Completed - 3 trades executed in 5.2s")

# 9. Error Scenarios
print("\n9️⃣  ERROR SCENARIOS")
print("-" * 80)
logger.error("Failed to execute trade", extra={'symbol': 'EURUSD'})
time.sleep(0.3)
mt5_logger.error("Insufficient margin for trade", exc_info=False)
time.sleep(0.3)
strategy_logger.warning("No bars available for analysis", extra={'symbol': 'BTCUSD'})

# 10. Configuration Reload
print("\n🔟 CONFIGURATION RELOAD")
print("-" * 80)
log_config(logger, "Configuration file changed - reloading...")
time.sleep(0.5)
log_config(logger, "Updated: EURUSD SL/TP changed to 30/60 pips")
time.sleep(0.5)
log_config(logger, "Updated: GBPUSD disabled by user")

print("\n" + "=" * 80)
print("  DEMO COMPLETE!")
print("=" * 80)

print("\n📁 Log Files Created:")
print("   - logs/trading_YYYYMMDD.log (all logs with DEBUG level)")
print("   - logs/errors_YYYYMMDD.log (errors only)")
print("   - logs/trades_YYYYMMDD.log (trade-related events only)")

print("\n💡 Features:")
print("   ✓ Color-coded log levels")
print("   ✓ Emoji icons for visual clarity")
print("   ✓ Symbol-specific context")
print("   ✓ Structured file logging")
print("   ✓ Separate error and trade logs")
print("   ✓ Rotating log files (10MB max)")
print("   ✓ Custom log helpers (log_trade, log_signal, etc.)")

print("\n📚 Usage in Your Code:")
print("""
from src.utils.logger import setup_logging, get_logger, log_trade

# Initialize (once at startup)
setup_logging(log_level="INFO")

# Get logger
logger = get_logger(__name__)

# Log messages
logger.info("Bot started")
logger.debug("Analyzing market data")
logger.warning("High volatility detected")
logger.error("Trade failed", extra={'symbol': 'EURUSD'})

# Use helpers
log_trade(logger, "EURUSD", "BUY", 0.10, 1.16234, 123456)
log_signal(logger, "GBPUSD", "SELL", 1.25678, 0.85)
""")

print()
