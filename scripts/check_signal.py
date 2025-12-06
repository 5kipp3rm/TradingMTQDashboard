"""
Quick signal checker - See what the strategy is saying right now
"""
import MetaTrader5 as mt5
from src.connectors import MT5Connector
from src.strategies import SimpleMovingAverageStrategy
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
connector = MT5Connector()
connector.connect(int(os.getenv('MT5_LOGIN')), os.getenv('MT5_PASSWORD'), os.getenv('MT5_SERVER'))

print("=" * 80)
print("  CURRENT MARKET SIGNAL")
print("=" * 80)

# Get recent bars
bars = connector.get_bars('EURUSD', 'M5', 100)

# Create strategy
strategy = SimpleMovingAverageStrategy({
    'fast_period': 10,
    'slow_period': 20,
    'sl_pips': 20,
    'tp_pips': 40
})

# Analyze
signal = strategy.analyze('EURUSD', 'M5', bars)

# Calculate MAs
import numpy as np
fast_ma = np.mean([bar.close for bar in bars[-10:]])
slow_ma = np.mean([bar.close for bar in bars[-20:]])
current_price = bars[-1].close

print(f"\n📊 Market Analysis [{datetime.now().strftime('%H:%M:%S')}]")
print(f"Symbol: EURUSD")
print(f"Current Price: {current_price:.5f}")
print(f"\n📈 Moving Averages:")
print(f"  Fast MA (10): {fast_ma:.5f}")
print(f"  Slow MA (20): {slow_ma:.5f}")
print(f"  Difference: {(fast_ma - slow_ma):.5f}")

if fast_ma > slow_ma:
    print(f"  Status: Fast MA is ABOVE Slow MA (bullish)")
else:
    print(f"  Status: Fast MA is BELOW Slow MA (bearish)")

print(f"\n🎯 Strategy Signal:")
print(f"  Signal Type: {signal.type.name}")
print(f"  Confidence: {signal.confidence:.1%}")
print(f"  Entry Price: {signal.price:.5f}")
if signal.stop_loss:
    print(f"  Stop Loss: {signal.stop_loss:.5f}")
if signal.take_profit:
    print(f"  Take Profit: {signal.take_profit:.5f}")

print(f"\n💡 Why HOLD?")
print(f"  The MA Crossover strategy only triggers BUY/SELL when:")
print(f"  • BUY: Fast MA crosses ABOVE Slow MA")
print(f"  • SELL: Fast MA crosses BELOW Slow MA")
print(f"  ")
print(f"  Currently the MAs are {'aligned' if abs(fast_ma - slow_ma) < 0.0001 else 'not crossing'}")
print(f"  Waiting for a crossover to occur...")

connector.disconnect()

print("\n" + "=" * 80)
print("\n💡 TIP: To see trades faster, try:")
print("   python aggressive_test.py  (trades every 10 seconds)")
print("=" * 80)
