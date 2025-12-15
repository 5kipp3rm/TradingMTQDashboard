"""
Unit Tests for Currency Configuration Models

Tests the CurrencyConfiguration database model including:
- Model creation and validation
- Field constraints and types
- Validation methods
- to_dict() serialization
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.currency_models import CurrencyConfiguration, StrategyType, Timeframe
from src.database.models import Base


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def valid_config_data():
    """Valid currency configuration data"""
    return {
        'symbol': 'EURUSD',
        'enabled': True,
        'risk_percent': 1.0,
        'max_position_size': 1.0,
        'min_position_size': 0.01,
        'strategy_type': 'position',
        'timeframe': 'M15',
        'fast_period': 10,
        'slow_period': 20,
        'sl_pips': 20,
        'tp_pips': 40,
        'cooldown_seconds': 60,
        'trade_on_signal_change': True,
        'allow_position_stacking': False,
        'max_positions_same_direction': 1,
        'max_total_positions': 5,
        'stacking_risk_multiplier': 1.0,
    }


# ============================================================================
# TEST: MODEL CREATION
# ============================================================================

def test_create_currency_config_with_valid_data(db_session, valid_config_data):
    """Test creating currency configuration with valid data"""
    config = CurrencyConfiguration(**valid_config_data)
    db_session.add(config)
    db_session.commit()

    assert config.id is not None
    assert config.symbol == 'EURUSD'
    assert config.enabled is True
    assert config.risk_percent == 1.0
    assert config.config_version == 1


def test_create_multiple_currencies(db_session, valid_config_data):
    """Test creating multiple currency configurations"""
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']

    for symbol in symbols:
        config_data = valid_config_data.copy()
        config_data['symbol'] = symbol
        config = CurrencyConfiguration(**config_data)
        db_session.add(config)

    db_session.commit()

    configs = db_session.query(CurrencyConfiguration).all()
    assert len(configs) == 3
    assert {c.symbol for c in configs} == set(symbols)


def test_currency_config_timestamps(db_session, valid_config_data):
    """Test that timestamps are automatically set"""
    config = CurrencyConfiguration(**valid_config_data)
    db_session.add(config)
    db_session.commit()

    assert config.created_at is not None
    assert config.updated_at is not None
    assert isinstance(config.created_at, datetime)
    assert isinstance(config.updated_at, datetime)


def test_currency_config_defaults(db_session):
    """Test default values for optional fields"""
    config = CurrencyConfiguration(
        symbol='EURUSD',
        risk_percent=1.0,
        max_position_size=1.0,
        min_position_size=0.01,
        strategy_type='position',
        timeframe='M15',
        fast_period=10,
        slow_period=20,
        sl_pips=20,
        tp_pips=40,
        cooldown_seconds=60,
    )
    db_session.add(config)
    db_session.commit()

    # Check defaults
    assert config.enabled is True
    assert config.trade_on_signal_change is True
    assert config.allow_position_stacking is False
    assert config.max_positions_same_direction == 1
    assert config.max_total_positions == 5
    assert config.stacking_risk_multiplier == 1.0
    assert config.config_version == 1


# ============================================================================
# TEST: VALIDATION
# ============================================================================

def test_validate_valid_configuration(valid_config_data):
    """Test validation passes for valid configuration"""
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is True
    assert len(errors) == 0


def test_validate_invalid_symbol_too_short(valid_config_data):
    """Test validation fails for symbol too short"""
    valid_config_data['symbol'] = 'EUR'
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Symbol must be at least 6 characters' in err for err in errors)


def test_validate_risk_percent_out_of_range(valid_config_data):
    """Test validation fails for risk percent out of range"""
    valid_config_data['risk_percent'] = 15.0  # Too high
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Risk percent must be between' in err for err in errors)


def test_validate_negative_position_sizes(valid_config_data):
    """Test validation fails for negative position sizes"""
    valid_config_data['max_position_size'] = -1.0
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Max position size must be greater than 0' in err for err in errors)


def test_validate_min_greater_than_max_position_size(valid_config_data):
    """Test validation fails when min > max position size"""
    valid_config_data['min_position_size'] = 2.0
    valid_config_data['max_position_size'] = 1.0
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Min position size cannot be greater than max' in err for err in errors)


def test_validate_invalid_strategy_type(valid_config_data):
    """Test validation fails for invalid strategy type"""
    valid_config_data['strategy_type'] = 'invalid'
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Strategy type must be' in err for err in errors)


def test_validate_invalid_timeframe(valid_config_data):
    """Test validation fails for invalid timeframe"""
    valid_config_data['timeframe'] = 'M99'
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Invalid timeframe' in err for err in errors)


def test_validate_fast_period_greater_than_slow(valid_config_data):
    """Test validation fails when fast_period >= slow_period"""
    valid_config_data['fast_period'] = 30
    valid_config_data['slow_period'] = 20
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Fast period must be less than slow period' in err for err in errors)


def test_validate_zero_periods(valid_config_data):
    """Test validation fails for zero periods"""
    valid_config_data['fast_period'] = 0
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Fast period must be greater than 0' in err for err in errors)


def test_validate_negative_sl_tp(valid_config_data):
    """Test validation fails for negative SL/TP"""
    valid_config_data['sl_pips'] = -10
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Stop Loss pips must be greater than 0' in err for err in errors)


def test_validate_negative_cooldown(valid_config_data):
    """Test validation fails for negative cooldown"""
    valid_config_data['cooldown_seconds'] = -60
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Cooldown seconds cannot be negative' in err for err in errors)


def test_validate_invalid_trading_hours_format(valid_config_data):
    """Test validation fails for invalid time format"""
    valid_config_data['trading_hours_start'] = '25:00'  # Invalid hour
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    assert is_valid is False
    assert any('Trading hours start must be in HH:MM format' in err for err in errors)


def test_validate_warning_tp_less_than_sl(valid_config_data):
    """Test validation warns when TP < SL (poor risk/reward)"""
    valid_config_data['tp_pips'] = 10
    valid_config_data['sl_pips'] = 20
    config = CurrencyConfiguration(**valid_config_data)
    is_valid, errors = config.validate()

    # Should still be valid but with warning
    assert any('Warning' in err or 'Take Profit should typically be larger' in err for err in errors)


# ============================================================================
# TEST: TO_DICT METHOD
# ============================================================================

def test_to_dict_contains_all_fields(valid_config_data):
    """Test to_dict() includes all configuration fields"""
    config = CurrencyConfiguration(**valid_config_data)
    config.id = 1

    result = config.to_dict()

    # Check required fields
    assert result['id'] == 1
    assert result['symbol'] == 'EURUSD'
    assert result['enabled'] is True
    assert result['risk_percent'] == 1.0
    assert result['strategy_type'] == 'position'
    assert result['timeframe'] == 'M15'
    assert result['fast_period'] == 10
    assert result['slow_period'] == 20
    assert result['sl_pips'] == 20
    assert result['tp_pips'] == 40


def test_to_dict_serializes_timestamps(valid_config_data):
    """Test to_dict() properly serializes datetime objects"""
    config = CurrencyConfiguration(**valid_config_data)
    config.created_at = datetime(2024, 1, 1, 12, 0, 0)
    config.updated_at = datetime(2024, 1, 2, 12, 0, 0)

    result = config.to_dict()

    assert result['created_at'] == '2024-01-01T12:00:00'
    assert result['updated_at'] == '2024-01-02T12:00:00'


def test_to_dict_handles_null_optional_fields(valid_config_data):
    """Test to_dict() handles null optional fields"""
    config = CurrencyConfiguration(**valid_config_data)
    config.trading_hours_start = None
    config.trading_hours_end = None
    config.description = None
    config.last_loaded = None

    result = config.to_dict()

    assert result['trading_hours_start'] is None
    assert result['trading_hours_end'] is None
    assert result['description'] is None
    assert result['last_loaded'] is None


# ============================================================================
# TEST: MODEL UPDATE
# ============================================================================

def test_update_currency_config(db_session, valid_config_data):
    """Test updating currency configuration"""
    config = CurrencyConfiguration(**valid_config_data)
    db_session.add(config)
    db_session.commit()

    original_version = config.config_version

    # Update fields
    config.risk_percent = 2.0
    config.sl_pips = 30
    config.config_version += 1
    db_session.commit()

    # Verify updates
    updated_config = db_session.query(CurrencyConfiguration).filter_by(symbol='EURUSD').first()
    assert updated_config.risk_percent == 2.0
    assert updated_config.sl_pips == 30
    assert updated_config.config_version == original_version + 1


def test_symbol_uniqueness(db_session, valid_config_data):
    """Test that symbol must be unique"""
    config1 = CurrencyConfiguration(**valid_config_data)
    db_session.add(config1)
    db_session.commit()

    # Try to add duplicate symbol
    config2 = CurrencyConfiguration(**valid_config_data)
    db_session.add(config2)

    with pytest.raises(Exception):  # IntegrityError
        db_session.commit()


# ============================================================================
# TEST: ENUMS
# ============================================================================

def test_strategy_type_enum():
    """Test StrategyType enum values"""
    assert StrategyType.CROSSOVER.value == "crossover"
    assert StrategyType.POSITION.value == "position"


def test_timeframe_enum():
    """Test Timeframe enum values"""
    assert Timeframe.M1.value == "M1"
    assert Timeframe.M5.value == "M5"
    assert Timeframe.M15.value == "M15"
    assert Timeframe.H1.value == "H1"
    assert Timeframe.D1.value == "D1"


# ============================================================================
# TEST: REPR
# ============================================================================

def test_repr_contains_key_info(valid_config_data):
    """Test __repr__ contains key information"""
    config = CurrencyConfiguration(**valid_config_data)
    config.id = 1

    repr_str = repr(config)

    assert 'CurrencyConfiguration' in repr_str
    assert 'id=1' in repr_str
    assert "symbol='EURUSD'" in repr_str
    assert 'enabled=True' in repr_str
    assert "strategy='position'" in repr_str
    assert "timeframe='M15'" in repr_str
