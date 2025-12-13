"""
Simple test to understand why signals aren't being generated
"""
import sys
import numpy as np
from datetime import datetime

# Mock candles data
class MockBar:
    def __init__(self, close):
        self.close = close

# Test the MA crossover logic directly
bars = [MockBar(1.05 + i * 0.0001) for i in range(100)]  # Uptrend

fast_period = 20
slow_period = 50

fast_ma = np.mean([bar.close for bar in bars[-fast_period:]])
slow_ma = np.mean([bar.close for bar in bars[-slow_period:]])

print(f"Fast MA ({fast_period}): {fast_ma:.5f}")
print(f"Slow MA ({slow_period}): {slow_ma:.5f}")
print(f"Fast > Slow: {fast_ma > slow_ma}")

if fast_ma > slow_ma:
    print("Signal: BUY")
elif fast_ma < slow_ma:
    print("Signal: SELL")
else:
    print("Signal: HOLD")
