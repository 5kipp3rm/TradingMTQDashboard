"""
Comprehensive tests for src.strategies.base module
Tests for BaseStrategy, Signal, and SignalType classes
"""
import pytest
from datetime import datetime
from src.strategies.base import BaseStrategy, Signal, SignalType


class TestSignalType:
    """Test suite for SignalType enum"""
    
    def test_signal_type_values(self):
        """Test all SignalType enum values"""
        assert SignalType.BUY.value == "BUY"
        assert SignalType.SELL.value == "SELL"
        assert SignalType.CLOSE_BUY.value == "CLOSE_BUY"
        assert SignalType.CLOSE_SELL.value == "CLOSE_SELL"
        assert SignalType.HOLD.value == "HOLD"
    
    def test_signal_type_members(self):
        """Test SignalType enum members"""
        assert len(SignalType) == 5
        assert SignalType.BUY in SignalType
        assert SignalType.SELL in SignalType


class TestSignal:
    """Test suite for Signal dataclass"""
    
    def test_signal_creation_minimal(self):
        """Test Signal creation with minimal parameters"""
        timestamp = datetime.now()
        signal = Signal(
            type=SignalType.BUY,
            symbol="EURUSD",
            timestamp=timestamp,
            price=1.0850,
            confidence=0.8
        )
        
        assert signal.type == SignalType.BUY
        assert signal.symbol == "EURUSD"
        assert signal.timestamp == timestamp
        assert signal.price == 1.0850
        assert signal.confidence == 0.8
        assert signal.stop_loss is None
        assert signal.take_profit is None
        assert signal.reason == ""
        assert signal.metadata == {}
    
    def test_signal_creation_full(self):
        """Test Signal creation with all parameters"""
        timestamp = datetime.now()
        metadata = {"indicator": "MA", "period": 20}
        
        signal = Signal(
            type=SignalType.SELL,
            symbol="GBPUSD",
            timestamp=timestamp,
            price=1.2500,
            confidence=0.95,
            stop_loss=1.2550,
            take_profit=1.2400,
            reason="MA crossover detected",
            metadata=metadata
        )
        
        assert signal.type == SignalType.SELL
        assert signal.symbol == "GBPUSD"
        assert signal.price == 1.2500
        assert signal.confidence == 0.95
        assert signal.stop_loss == 1.2550
        assert signal.take_profit == 1.2400
        assert signal.reason == "MA crossover detected"
        assert signal.metadata == metadata
    
    def test_signal_metadata_post_init(self):
        """Test Signal metadata initialization in __post_init__"""
        signal = Signal(
            type=SignalType.HOLD,
            symbol="USDJPY",
            timestamp=datetime.now(),
            price=150.00,
            confidence=0.5,
            metadata=None
        )
        
        # __post_init__ should initialize metadata to empty dict
        assert signal.metadata == {}
        assert isinstance(signal.metadata, dict)
    
    def test_signal_different_types(self):
        """Test Signal with different signal types"""
        timestamp = datetime.now()
        
        for signal_type in SignalType:
            signal = Signal(
                type=signal_type,
                symbol="TEST",
                timestamp=timestamp,
                price=1.0,
                confidence=0.7
            )
            assert signal.type == signal_type


class ConcreteStrategy(BaseStrategy):
    """Concrete implementation of BaseStrategy for testing"""
    
    def analyze(self, symbol: str, timeframe: str, bars: list) -> Signal:
        """Concrete implementation of analyze method"""
        return Signal(
            type=SignalType.HOLD,
            symbol=symbol,
            timestamp=datetime.now(),
            price=1.0,
            confidence=0.5,
            reason="Test strategy"
        )


class TestBaseStrategy:
    """Test suite for BaseStrategy abstract class"""
    
    def test_initialization_minimal(self):
        """Test BaseStrategy initialization with minimal parameters"""
        strategy = ConcreteStrategy(name="Test Strategy")
        
        assert strategy.name == "Test Strategy"
        assert strategy.params == {}
        assert strategy.enabled is True
    
    def test_initialization_with_params(self):
        """Test BaseStrategy initialization with parameters"""
        params = {"period": 20, "threshold": 0.5}
        strategy = ConcreteStrategy(name="Test Strategy", params=params)
        
        assert strategy.name == "Test Strategy"
        assert strategy.params == params
        assert strategy.enabled is True
    
    def test_get_name(self):
        """Test get_name method"""
        strategy = ConcreteStrategy(name="My Strategy")
        assert strategy.get_name() == "My Strategy"
    
    def test_get_params(self):
        """Test get_params method"""
        params = {"fast": 10, "slow": 20}
        strategy = ConcreteStrategy(name="Test", params=params)
        
        retrieved_params = strategy.get_params()
        assert retrieved_params == params
        assert retrieved_params is strategy.params  # Should return the same dict
    
    def test_set_param(self):
        """Test set_param method"""
        strategy = ConcreteStrategy(name="Test")
        
        # Initially empty
        assert strategy.params == {}
        
        # Set a parameter
        strategy.set_param("period", 50)
        assert strategy.params["period"] == 50
        assert "period" in strategy.params
        
        # Set another parameter
        strategy.set_param("threshold", 0.75)
        assert strategy.params["threshold"] == 0.75
        
        # Overwrite existing parameter
        strategy.set_param("period", 100)
        assert strategy.params["period"] == 100
        
        # Set various types
        strategy.set_param("string_value", "test")
        strategy.set_param("list_value", [1, 2, 3])
        strategy.set_param("dict_value", {"key": "value"})
        assert strategy.params["string_value"] == "test"
        assert strategy.params["list_value"] == [1, 2, 3]
        assert strategy.params["dict_value"] == {"key": "value"}
    
    def test_enable_disable(self):
        """Test enable and disable methods"""
        strategy = ConcreteStrategy(name="Test")
        
        # Initially enabled
        assert strategy.enabled is True
        assert strategy.is_enabled() is True
        
        # Disable
        strategy.disable()
        assert strategy.enabled is False
        assert strategy.is_enabled() is False
        
        # Enable again
        strategy.enable()
        assert strategy.enabled is True
        assert strategy.is_enabled() is True
    
    def test_is_enabled(self):
        """Test is_enabled method"""
        strategy = ConcreteStrategy(name="Test")
        
        assert strategy.is_enabled() is True
        
        strategy.enabled = False
        assert strategy.is_enabled() is False
        
        strategy.enabled = True
        assert strategy.is_enabled() is True
    
    def test_analyze_abstract_method(self):
        """Test that analyze must be implemented"""
        # This test verifies that BaseStrategy cannot be instantiated directly
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseStrategy(name="Test")
    
    def test_concrete_analyze(self):
        """Test concrete implementation of analyze"""
        strategy = ConcreteStrategy(name="Test")
        
        signal = strategy.analyze("EURUSD", "M5", [])
        
        assert isinstance(signal, Signal)
        assert signal.symbol == "EURUSD"
        assert signal.type == SignalType.HOLD
    
    def test_params_isolation(self):
        """Test that each strategy instance has isolated params"""
        strategy1 = ConcreteStrategy(name="Strategy1", params={"value": 10})
        strategy2 = ConcreteStrategy(name="Strategy2", params={"value": 20})
        
        assert strategy1.params["value"] == 10
        assert strategy2.params["value"] == 20
        
        strategy1.set_param("value", 30)
        assert strategy1.params["value"] == 30
        assert strategy2.params["value"] == 20  # Should not be affected
    
    def test_strategy_state_persistence(self):
        """Test that strategy state persists across method calls"""
        strategy = ConcreteStrategy(name="Test")
        
        strategy.set_param("counter", 0)
        strategy.disable()
        
        assert strategy.get_params()["counter"] == 0
        assert strategy.is_enabled() is False
        
        strategy.set_param("counter", 5)
        strategy.enable()
        
        assert strategy.get_params()["counter"] == 5
        assert strategy.is_enabled() is True
