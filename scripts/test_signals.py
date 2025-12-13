"""Quick test to check if signals are being generated"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.connectors.mt5_connector import MT5Connector
from src.strategies.base import BaseStrategy
from src.trading.currency_trader import CurrencyTrader, CurrencyTraderConfig
from src.utils.logger import setup_logging, get_logger

# Create a dummy strategy for testing
class TestStrategy(BaseStrategy):
    def analyze(self, candles):
        return None  # Not used in position trading mode

setup_logging(log_level="DEBUG")
logger = get_logger(__name__)

# Connect to MT5
connector = MT5Connector("test_signals")
if not connector.connect(5043091442, "Mq*y6BFJ", "MetaQuotes-Demo"):
    print("Failed to connect to MT5")
    sys.exit(1)

logger.info("✅ Connected to MT5")

# Create a simple trader
strategy = TestStrategy(name="Test MA")
config = CurrencyTraderConfig(
    symbol="EURUSD",
    strategy=strategy,
    risk_percent=0.5,
    timeframe="H1",
    use_position_trading=True,
    fast_period=20,
    slow_period=50,
    sl_pips=30,
    tp_pips=60
)

trader = CurrencyTrader(config, connector)

logger.info(f"Testing signal generation for {config.symbol}")

# Try to analyze market
signal = trader.analyze_market()

if signal:
    logger.info(f"✅ Signal generated: {signal.type.name} @ {signal.price:.5f}")
    logger.info(f"   Confidence: {signal.confidence:.2f}")
    logger.info(f"   SL: {signal.stop_loss:.5f if signal.stop_loss else 'None'}")
    logger.info(f"   TP: {signal.take_profit:.5f if signal.take_profit else 'None'}")
    logger.info(f"   Reason: {signal.reason}")
    
    # Check if should execute
    should_exec = trader.should_execute_signal(signal)
    logger.info(f"   Should execute: {should_exec}")
else:
    logger.error("❌ No signal generated")

# Try full cycle
logger.info("\nTrying full process_cycle()...")
result = trader.process_cycle()
logger.info(f"Cycle result: {result}")

connector.disconnect()
