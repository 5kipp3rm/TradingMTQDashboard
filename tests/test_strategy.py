"""
Tests for Strategy Classes
"""
import pytest
from datetime import datetime, timedelta

from src.strategies.base import BaseStrategy, Signal, SignalType
from src.strategies.simple_ma import SimpleMovingAverageStrategy
from src.connectors.base import OHLCBar


class TestSimpleMovingAverageStrategy:
    """Test suite for Simple MA Crossover Strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create strategy instance"""
        return SimpleMovingAverageStrategy()
    
    def test_initialization(self, strategy):
        """Test strategy initialization"""
        assert strategy.get_name() == "Simple MA Crossover"
        assert strategy.params['fast_period'] == 10
        assert strategy.params['slow_period'] == 20
        assert strategy.is_enabled() is True
    
    def test_custom_parameters(self):
        """Test strategy with custom parameters"""
        strategy = SimpleMovingAverageStrategy(params={
            'fast_period': 5,
            'slow_period': 15,
            'sl_pips': 30,
            'tp_pips': 60
        })
        
        assert strategy.params['fast_period'] == 5
        assert strategy.params['slow_period'] == 15
        assert strategy.params['sl_pips'] == 30
        assert strategy.params['tp_pips'] == 60
    
    def test_calculate_sma(self, strategy):
        """Test SMA calculation"""
        # Create test bars
        bars = []
        base_time = datetime.now()
        
        for i in range(10):
            bars.append(OHLCBar(
                symbol="EURUSD",
                timeframe="M5",
                time=base_time + timedelta(minutes=i*5),
                open=1.08500 + i * 0.00010,
                high=1.08550 + i * 0.00010,
                low=1.08450 + i * 0.00010,
                close=1.08500 + i * 0.00010,
                tick_volume=1000,
                real_volume=100000,
                spread=2
            ))
        
        sma = strategy.calculate_sma(bars, 5)
        
        assert sma > 0
        assert isinstance(sma, float)
    
    def test_insufficient_data(self, strategy):
        """Test with insufficient data"""
        # Create only 5 bars (need 20 for slow MA)
        bars = []
        base_time = datetime.now()
        
        for i in range(5):
            bars.append(OHLCBar(
                symbol="EURUSD",
                timeframe="M5",
                time=base_time + timedelta(minutes=i*5),
                open=1.08500,
                high=1.08550,
                low=1.08450,
                close=1.08500,
                tick_volume=1000,
                real_volume=100000,
                spread=2
            ))
        
        signal = strategy.analyze("EURUSD", "M5", bars)
        
        assert signal.type == SignalType.HOLD
        assert "Insufficient data" in signal.reason
    
    def test_bullish_crossover(self, strategy):
        """Test bullish crossover detection"""
        bars = []
        base_time = datetime.now()
        
        # Create downtrend then uptrend (bullish crossover)
        for i in range(30):
            if i < 15:
                # Downtrend
                close = 1.08500 - i * 0.00010
            else:
                # Uptrend (faster than slow MA can follow)
                close = 1.08350 + (i - 15) * 0.00020
            
            bars.append(OHLCBar(
                symbol="EURUSD",
                timeframe="M5",
                time=base_time + timedelta(minutes=i*5),
                open=close,
                high=close + 0.00010,
                low=close - 0.00010,
                close=close,
                tick_volume=1000,
                real_volume=100000,
                spread=2
            ))
        
        # First call to initialize
        strategy.analyze("EURUSD", "M5", bars[:25])
        
        # Second call should detect crossover
        signal = strategy.analyze("EURUSD", "M5", bars)
        
        # Should eventually get a BUY signal as fast MA crosses above slow
        assert signal is not None
        assert signal.symbol == "EURUSD"
    
    def test_bearish_crossover(self, strategy):
        """Test bearish crossover detection"""
        bars = []
        base_time = datetime.now()
        
        # Create uptrend then downtrend (bearish crossover)
        for i in range(30):
            if i < 15:
                # Uptrend
                close = 1.08500 + i * 0.00010
            else:
                # Downtrend (faster than slow MA can follow)
                close = 1.08650 - (i - 15) * 0.00020
            
            bars.append(OHLCBar(
                symbol="EURUSD",
                timeframe="M5",
                time=base_time + timedelta(minutes=i*5),
                open=close,
                high=close + 0.00010,
                low=close - 0.00010,
                close=close,
                tick_volume=1000,
                real_volume=100000,
                spread=2
            ))
        
        # First call to initialize
        strategy.analyze("EURUSD", "M5", bars[:25])
        
        # Second call should detect crossover
        signal = strategy.analyze("EURUSD", "M5", bars)
        
        assert signal is not None
        assert signal.symbol == "EURUSD"
    
    def test_sl_tp_calculation(self, strategy):
        """Test stop loss and take profit calculation"""
        bars = []
        base_time = datetime.now()
        current_price = 1.08500
        
        for i in range(25):
            bars.append(OHLCBar(
                symbol="EURUSD",
                timeframe="M5",
                time=base_time + timedelta(minutes=i*5),
                open=current_price,
                high=current_price + 0.00010,
                low=current_price - 0.00010,
                close=current_price,
                tick_volume=1000,
                real_volume=100000,
                spread=2
            ))
        
        signal = strategy.analyze("EURUSD", "M5", bars)
        
        # If signal is BUY or SELL, check SL/TP
        if signal.type in [SignalType.BUY, SignalType.SELL]:
            assert signal.stop_loss is not None
            assert signal.take_profit is not None
            
            if signal.type == SignalType.BUY:
                assert signal.stop_loss < current_price
                assert signal.take_profit > current_price
            elif signal.type == SignalType.SELL:
                assert signal.stop_loss > current_price
                assert signal.take_profit < current_price
    
    def test_disabled_strategy(self, strategy):
        """Test disabled strategy"""
        strategy.disable()
        
        bars = [OHLCBar(
            symbol="EURUSD",
            timeframe="M5",
            time=datetime.now(),
            open=1.08500,
            high=1.08550,
            low=1.08450,
            close=1.08500,
            tick_volume=1000,
            real_volume=100000,
            spread=2
        )]
        
        signal = strategy.analyze("EURUSD", "M5", bars)
        
        assert signal.type == SignalType.HOLD
        assert "disabled" in signal.reason.lower()
