"""
Unit Tests for ConfigurationService

Tests configuration synchronization, YAML operations, and dual persistence.
"""

import pytest
import yaml
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base
from src.database.currency_models import CurrencyConfiguration
from src.services.config_service import ConfigurationService


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
def temp_yaml_path(tmp_path):
    """Create temporary YAML file path"""
    yaml_file = tmp_path / "test_currencies.yaml"
    return str(yaml_file)


@pytest.fixture
def config_service(temp_yaml_path):
    """Create ConfigurationService with temporary YAML path"""
    return ConfigurationService(yaml_path=temp_yaml_path)


@pytest.fixture
def sample_currency_data():
    """Sample valid currency configuration data"""
    return {
        "symbol": "EURUSD",
        "enabled": True,
        "risk_percent": 1.0,
        "max_position_size": 1.0,
        "min_position_size": 0.01,
        "strategy_type": "position",
        "timeframe": "M15",
        "fast_period": 10,
        "slow_period": 20,
        "sl_pips": 20,
        "tp_pips": 40,
        "cooldown_seconds": 60,
        "trade_on_signal_change": True,
        "allow_position_stacking": False,
        "max_positions_same_direction": 1,
        "max_total_positions": 5,
        "stacking_risk_multiplier": 1.0
    }


@pytest.fixture
def sample_yaml_config():
    """Sample YAML configuration structure"""
    return {
        "global": {
            "max_concurrent_trades": 15,
            "portfolio_risk_percent": 8.0,
        },
        "currencies": {
            "EURUSD": {
                "enabled": True,
                "risk_percent": 1.0,
                "max_position_size": 1.0,
                "min_position_size": 0.01,
                "strategy_type": "position",
                "timeframe": "M15",
                "fast_period": 10,
                "slow_period": 20,
                "sl_pips": 20,
                "tp_pips": 40,
                "cooldown_seconds": 60,
                "trade_on_signal_change": True,
                "allow_position_stacking": False,
                "max_positions_same_direction": 1,
                "max_total_positions": 5,
                "stacking_risk_multiplier": 1.0,
            },
            "GBPUSD": {
                "enabled": False,
                "risk_percent": 0.5,
                "max_position_size": 0.5,
                "min_position_size": 0.01,
                "strategy_type": "crossover",
                "timeframe": "H1",
                "fast_period": 20,
                "slow_period": 50,
                "sl_pips": 30,
                "tp_pips": 60,
                "cooldown_seconds": 120,
                "trade_on_signal_change": False,
                "allow_position_stacking": True,
                "max_positions_same_direction": 3,
                "max_total_positions": 10,
                "stacking_risk_multiplier": 0.8,
            }
        }
    }


# ============================================================================
# TEST: LOAD FROM DATABASE
# ============================================================================

def test_load_from_database_empty(config_service, db_session):
    """Test loading from empty database"""
    currencies = config_service.load_from_database(db_session)
    assert len(currencies) == 0


def test_load_from_database_with_data(config_service, db_session, sample_currency_data):
    """Test loading currencies from database"""
    # Add currencies to database
    currency1 = CurrencyConfiguration(**sample_currency_data)
    db_session.add(currency1)

    currency2_data = sample_currency_data.copy()
    currency2_data["symbol"] = "GBPUSD"
    currency2 = CurrencyConfiguration(**currency2_data)
    db_session.add(currency2)

    db_session.commit()

    # Load from database
    currencies = config_service.load_from_database(db_session)
    assert len(currencies) == 2
    assert {c.symbol for c in currencies} == {"EURUSD", "GBPUSD"}


def test_load_from_database_ordered_by_symbol(config_service, db_session, sample_currency_data):
    """Test currencies are loaded in alphabetical order"""
    symbols = ["USDJPY", "EURUSD", "GBPUSD"]

    for symbol in symbols:
        data = sample_currency_data.copy()
        data["symbol"] = symbol
        currency = CurrencyConfiguration(**data)
        db_session.add(currency)

    db_session.commit()

    currencies = config_service.load_from_database(db_session)
    loaded_symbols = [c.symbol for c in currencies]
    assert loaded_symbols == sorted(symbols)


# ============================================================================
# TEST: LOAD FROM YAML
# ============================================================================

def test_load_from_yaml_file_not_exists(config_service):
    """Test loading from non-existent YAML file"""
    config = config_service.load_from_yaml()
    assert config == {"currencies": {}}


def test_load_from_yaml_success(config_service, temp_yaml_path, sample_yaml_config):
    """Test loading valid YAML configuration"""
    # Write YAML file
    with open(temp_yaml_path, 'w') as f:
        yaml.dump(sample_yaml_config, f)

    # Load from YAML
    config = config_service.load_from_yaml()
    assert "currencies" in config
    assert len(config["currencies"]) == 2
    assert "EURUSD" in config["currencies"]
    assert "GBPUSD" in config["currencies"]


def test_load_from_yaml_empty_file(config_service, temp_yaml_path):
    """Test loading empty YAML file"""
    # Create empty file
    Path(temp_yaml_path).touch()

    config = config_service.load_from_yaml()
    assert config == {}


def test_load_from_yaml_invalid_yaml(config_service, temp_yaml_path):
    """Test loading invalid YAML raises error"""
    # Write invalid YAML
    with open(temp_yaml_path, 'w') as f:
        f.write("invalid: yaml: content: [")

    with pytest.raises(yaml.YAMLError):
        config_service.load_from_yaml()


# ============================================================================
# TEST: SAVE TO YAML
# ============================================================================

def test_save_to_yaml_empty_database(config_service, db_session, temp_yaml_path):
    """Test saving empty database to YAML"""
    result = config_service.save_to_yaml(db_session)
    assert result is True

    # Verify YAML file was created with default structure
    with open(temp_yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    assert "currencies" in config
    assert len(config["currencies"]) == 0


def test_save_to_yaml_with_currencies(config_service, db_session, sample_currency_data, temp_yaml_path):
    """Test saving currencies to YAML"""
    # Add currency to database
    currency = CurrencyConfiguration(**sample_currency_data)
    db_session.add(currency)
    db_session.commit()

    # Save to YAML
    result = config_service.save_to_yaml(db_session)
    assert result is True

    # Verify YAML content
    with open(temp_yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    assert "EURUSD" in config["currencies"]
    assert config["currencies"]["EURUSD"]["enabled"] is True
    assert config["currencies"]["EURUSD"]["risk_percent"] == 1.0
    assert config["currencies"]["EURUSD"]["strategy_type"] == "position"


def test_save_to_yaml_preserves_non_currency_settings(config_service, db_session, temp_yaml_path, sample_yaml_config):
    """Test saving preserves global settings in YAML"""
    # Write initial YAML with global settings
    with open(temp_yaml_path, 'w') as f:
        yaml.dump(sample_yaml_config, f)

    # Save to YAML (should preserve global settings)
    result = config_service.save_to_yaml(db_session)
    assert result is True

    # Verify global settings are preserved
    with open(temp_yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    assert "global" in config
    assert config["global"]["max_concurrent_trades"] == 15


def test_save_to_yaml_with_optional_fields(config_service, db_session, sample_currency_data, temp_yaml_path):
    """Test saving currency with optional fields"""
    sample_currency_data["description"] = "Test currency"
    sample_currency_data["trading_hours_start"] = "08:00"
    sample_currency_data["trading_hours_end"] = "17:00"

    currency = CurrencyConfiguration(**sample_currency_data)
    db_session.add(currency)
    db_session.commit()

    result = config_service.save_to_yaml(db_session)
    assert result is True

    with open(temp_yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    eurusd = config["currencies"]["EURUSD"]
    assert eurusd["description"] == "Test currency"
    assert eurusd["trading_hours"]["start"] == "08:00"
    assert eurusd["trading_hours"]["end"] == "17:00"


# ============================================================================
# TEST: SYNC YAML TO DATABASE
# ============================================================================

def test_sync_yaml_to_database_empty_yaml(config_service, db_session, temp_yaml_path):
    """Test syncing from empty YAML"""
    # Create empty YAML
    with open(temp_yaml_path, 'w') as f:
        yaml.dump({"currencies": {}}, f)

    added, updated, errors = config_service.sync_yaml_to_database(db_session)
    assert added == 0
    assert updated == 0
    assert len(errors) == 0


def test_sync_yaml_to_database_add_new_currencies(config_service, db_session, temp_yaml_path, sample_yaml_config):
    """Test adding new currencies from YAML"""
    # Write YAML
    with open(temp_yaml_path, 'w') as f:
        yaml.dump(sample_yaml_config, f)

    # Sync to database
    added, updated, errors = config_service.sync_yaml_to_database(db_session)
    assert added == 2
    assert updated == 0
    assert len(errors) == 0

    # Verify database has currencies
    currencies = config_service.load_from_database(db_session)
    assert len(currencies) == 2


def test_sync_yaml_to_database_update_existing(config_service, db_session, temp_yaml_path, sample_currency_data, sample_yaml_config):
    """Test updating existing currencies from YAML"""
    # Add currency to database
    currency = CurrencyConfiguration(**sample_currency_data)
    db_session.add(currency)
    db_session.commit()

    # Modify YAML with different values
    sample_yaml_config["currencies"]["EURUSD"]["enabled"] = False
    sample_yaml_config["currencies"]["EURUSD"]["risk_percent"] = 2.0

    with open(temp_yaml_path, 'w') as f:
        yaml.dump(sample_yaml_config, f)

    # Sync to database
    added, updated, errors = config_service.sync_yaml_to_database(db_session)
    assert added == 1  # GBPUSD is new
    assert updated == 1  # EURUSD is updated
    assert len(errors) == 0

    # Verify updates
    db_session.refresh(currency)
    assert currency.enabled is False
    assert currency.risk_percent == 2.0


def test_sync_yaml_to_database_invalid_currency(config_service, db_session, temp_yaml_path):
    """Test syncing with invalid currency data"""
    invalid_config = {
        "currencies": {
            "INVALID": {
                "enabled": True,
                "risk_percent": 15.0,  # Too high
                "max_position_size": 1.0,
                "min_position_size": 0.01,
                "strategy_type": "position",
                "timeframe": "M15",
                "fast_period": 10,
                "slow_period": 20,
                "sl_pips": 20,
                "tp_pips": 40,
                "cooldown_seconds": 60,
            }
        }
    }

    with open(temp_yaml_path, 'w') as f:
        yaml.dump(invalid_config, f)

    added, updated, errors = config_service.sync_yaml_to_database(db_session)
    assert added == 0
    assert updated == 0
    assert len(errors) == 1
    assert "INVALID" in errors[0]


# ============================================================================
# TEST: SYNC DATABASE TO YAML
# ============================================================================

def test_sync_database_to_yaml(config_service, db_session, sample_currency_data, temp_yaml_path):
    """Test sync_database_to_yaml is alias for save_to_yaml"""
    currency = CurrencyConfiguration(**sample_currency_data)
    db_session.add(currency)
    db_session.commit()

    result = config_service.sync_database_to_yaml(db_session)
    assert result is True

    # Verify YAML was created
    assert Path(temp_yaml_path).exists()


# ============================================================================
# TEST: EXPORT TO FILE
# ============================================================================

def test_export_to_file(config_service, db_session, sample_currency_data, tmp_path):
    """Test exporting configuration to custom file"""
    currency = CurrencyConfiguration(**sample_currency_data)
    db_session.add(currency)
    db_session.commit()

    export_path = tmp_path / "exported_config.yaml"
    result = config_service.export_to_file(db_session, str(export_path))
    assert result is True
    assert export_path.exists()

    # Verify export content
    with open(export_path, 'r') as f:
        config = yaml.safe_load(f)

    assert "EURUSD" in config["currencies"]


def test_export_to_file_preserves_original_path(config_service, db_session, sample_currency_data, temp_yaml_path, tmp_path):
    """Test export doesn't change service's yaml_path"""
    original_path = config_service.yaml_path

    export_path = tmp_path / "exported.yaml"
    config_service.export_to_file(db_session, str(export_path))

    assert config_service.yaml_path == original_path


# ============================================================================
# TEST: IMPORT FROM FILE
# ============================================================================

def test_import_from_file(config_service, db_session, tmp_path, sample_yaml_config):
    """Test importing configuration from custom file"""
    import_path = tmp_path / "import_config.yaml"
    with open(import_path, 'w') as f:
        yaml.dump(sample_yaml_config, f)

    added, updated, errors = config_service.import_from_file(db_session, str(import_path))
    assert added == 2
    assert updated == 0
    assert len(errors) == 0

    # Verify import
    currencies = config_service.load_from_database(db_session)
    assert len(currencies) == 2


def test_import_from_file_preserves_original_path(config_service, db_session, temp_yaml_path, tmp_path, sample_yaml_config):
    """Test import doesn't change service's yaml_path"""
    original_path = config_service.yaml_path

    import_path = tmp_path / "import.yaml"
    with open(import_path, 'w') as f:
        yaml.dump(sample_yaml_config, f)

    config_service.import_from_file(db_session, str(import_path))

    assert config_service.yaml_path == original_path


# ============================================================================
# TEST: VALIDATE CONSISTENCY
# ============================================================================

def test_validate_consistency_empty(config_service, db_session, temp_yaml_path):
    """Test consistency check with empty database and YAML"""
    # Create empty YAML
    with open(temp_yaml_path, 'w') as f:
        yaml.dump({"currencies": {}}, f)

    is_consistent, differences = config_service.validate_consistency(db_session)
    assert is_consistent is True
    assert len(differences) == 0


def test_validate_consistency_matching(config_service, db_session, temp_yaml_path, sample_currency_data, sample_yaml_config):
    """Test consistency when DB and YAML match"""
    # Add currency to database
    currency = CurrencyConfiguration(**sample_currency_data)
    db_session.add(currency)

    currency2_data = sample_currency_data.copy()
    currency2_data["symbol"] = "GBPUSD"
    currency2 = CurrencyConfiguration(**currency2_data)
    db_session.add(currency2)

    db_session.commit()

    # Write matching YAML
    with open(temp_yaml_path, 'w') as f:
        yaml.dump(sample_yaml_config, f)

    is_consistent, differences = config_service.validate_consistency(db_session)
    assert is_consistent is True
    assert len(differences) == 0


def test_validate_consistency_db_has_extra(config_service, db_session, temp_yaml_path, sample_currency_data):
    """Test consistency when database has extra currencies"""
    # Add currency to database
    currency = CurrencyConfiguration(**sample_currency_data)
    db_session.add(currency)
    db_session.commit()

    # Create empty YAML
    with open(temp_yaml_path, 'w') as f:
        yaml.dump({"currencies": {}}, f)

    is_consistent, differences = config_service.validate_consistency(db_session)
    assert is_consistent is False
    assert len(differences) == 1
    assert "EURUSD" in differences[0]
    assert "database but not in YAML" in differences[0]


def test_validate_consistency_yaml_has_extra(config_service, db_session, temp_yaml_path, sample_yaml_config):
    """Test consistency when YAML has extra currencies"""
    # Write YAML with currencies
    with open(temp_yaml_path, 'w') as f:
        yaml.dump(sample_yaml_config, f)

    # Database is empty

    is_consistent, differences = config_service.validate_consistency(db_session)
    assert is_consistent is False
    assert len(differences) == 2
    assert any("EURUSD" in d and "YAML but not in database" in d for d in differences)
    assert any("GBPUSD" in d and "YAML but not in database" in d for d in differences)


# ============================================================================
# TEST: GET DEFAULT YAML STRUCTURE
# ============================================================================

def test_get_default_yaml_structure(config_service):
    """Test default YAML structure contains expected sections"""
    default = config_service._get_default_yaml_structure()

    assert "global" in default
    assert "currencies" in default
    assert "emergency" in default
    assert "modifications" in default

    assert default["currencies"] == {}
    assert isinstance(default["global"]["max_concurrent_trades"], int)
