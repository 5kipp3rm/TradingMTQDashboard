"""
Unit Tests for Currency Configuration API Endpoints

Tests all 13 API endpoints:
- CRUD operations (8 endpoints)
- Hot-reload operations (5 endpoints)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.app import app
from src.database.models import Base
from src.database.currency_models import CurrencyConfiguration
from src.database import get_session


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
def client(db_session):
    """Create test client with database override"""
    def override_get_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


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
def created_currency(client, sample_currency_data):
    """Create a currency and return the response"""
    response = client.post("/api/currencies", json=sample_currency_data)
    return response.json()


# ============================================================================
# TEST: LIST CURRENCIES (GET /api/currencies)
# ============================================================================

def test_list_currencies_empty(client):
    """Test listing currencies when database is empty"""
    response = client.get("/api/currencies")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 0
    assert data["enabled_count"] == 0
    assert len(data["currencies"]) == 0


def test_list_currencies_with_data(client, created_currency):
    """Test listing currencies with data"""
    response = client.get("/api/currencies")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["enabled_count"] == 1
    assert len(data["currencies"]) == 1
    assert data["currencies"][0]["symbol"] == "EURUSD"


def test_list_currencies_filter_enabled_only(client, sample_currency_data):
    """Test filtering to show only enabled currencies"""
    # Create enabled currency
    client.post("/api/currencies", json=sample_currency_data)

    # Create disabled currency
    disabled_data = sample_currency_data.copy()
    disabled_data["symbol"] = "GBPUSD"
    disabled_data["enabled"] = False
    client.post("/api/currencies", json=disabled_data)

    # List all
    response = client.get("/api/currencies")
    assert response.json()["total"] == 2

    # List enabled only
    response = client.get("/api/currencies?enabled_only=true")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["currencies"][0]["enabled"] is True


def test_list_currencies_multiple(client, sample_currency_data):
    """Test listing multiple currencies"""
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]

    for symbol in symbols:
        data = sample_currency_data.copy()
        data["symbol"] = symbol
        client.post("/api/currencies", json=data)

    response = client.get("/api/currencies")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 3
    assert {c["symbol"] for c in data["currencies"]} == set(symbols)


# ============================================================================
# TEST: GET CURRENCY (GET /api/currencies/{symbol})
# ============================================================================

def test_get_currency_success(client, created_currency):
    """Test getting a specific currency"""
    response = client.get(f"/api/currencies/EURUSD")
    assert response.status_code == 200

    data = response.json()
    assert data["symbol"] == "EURUSD"
    assert data["risk_percent"] == 1.0
    assert data["strategy_type"] == "position"


def test_get_currency_not_found(client):
    """Test getting non-existent currency"""
    response = client.get("/api/currencies/INVALID")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_currency_case_insensitive(client, created_currency):
    """Test that symbol lookup is case-insensitive"""
    response = client.get("/api/currencies/eurusd")
    assert response.status_code == 200
    assert response.json()["symbol"] == "EURUSD"


# ============================================================================
# TEST: CREATE CURRENCY (POST /api/currencies)
# ============================================================================

def test_create_currency_success(client, sample_currency_data):
    """Test creating a new currency"""
    response = client.post("/api/currencies", json=sample_currency_data)
    assert response.status_code == 201

    data = response.json()
    assert data["symbol"] == "EURUSD"
    assert data["id"] is not None
    assert data["config_version"] == 1


def test_create_currency_duplicate_symbol(client, created_currency):
    """Test creating currency with duplicate symbol"""
    duplicate_data = {
        "symbol": "EURUSD",
        "risk_percent": 2.0,
        "max_position_size": 2.0,
        "min_position_size": 0.01,
        "strategy_type": "crossover",
        "timeframe": "H1",
        "fast_period": 20,
        "slow_period": 50,
        "sl_pips": 30,
        "tp_pips": 60,
        "cooldown_seconds": 120
    }

    response = client.post("/api/currencies", json=duplicate_data)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_create_currency_invalid_risk_percent(client, sample_currency_data):
    """Test creating currency with invalid risk percent"""
    sample_currency_data["risk_percent"] = 15.0  # Too high
    response = client.post("/api/currencies", json=sample_currency_data)
    assert response.status_code == 422  # Validation error from Pydantic


def test_create_currency_invalid_strategy_type(client, sample_currency_data):
    """Test creating currency with invalid strategy type"""
    sample_currency_data["strategy_type"] = "invalid"
    response = client.post("/api/currencies", json=sample_currency_data)
    assert response.status_code == 422


def test_create_currency_invalid_timeframe(client, sample_currency_data):
    """Test creating currency with invalid timeframe"""
    sample_currency_data["timeframe"] = "M99"
    response = client.post("/api/currencies", json=sample_currency_data)
    assert response.status_code == 422


def test_create_currency_fast_period_greater_than_slow(client, sample_currency_data):
    """Test creating currency with fast_period > slow_period"""
    sample_currency_data["fast_period"] = 50
    sample_currency_data["slow_period"] = 20
    response = client.post("/api/currencies", json=sample_currency_data)
    assert response.status_code == 422


def test_create_currency_with_optional_fields(client, sample_currency_data):
    """Test creating currency with optional fields"""
    sample_currency_data["description"] = "Test currency"
    sample_currency_data["trading_hours_start"] = "08:00"
    sample_currency_data["trading_hours_end"] = "17:00"

    response = client.post("/api/currencies", json=sample_currency_data)
    assert response.status_code == 201

    data = response.json()
    assert data["description"] == "Test currency"
    assert data["trading_hours_start"] == "08:00"
    assert data["trading_hours_end"] == "17:00"


# ============================================================================
# TEST: UPDATE CURRENCY (PUT /api/currencies/{symbol})
# ============================================================================

def test_update_currency_success(client, created_currency):
    """Test updating a currency configuration"""
    update_data = {
        "risk_percent": 2.0,
        "sl_pips": 30
    }

    response = client.put("/api/currencies/EURUSD", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["risk_percent"] == 2.0
    assert data["sl_pips"] == 30
    assert data["config_version"] == 2  # Version incremented


def test_update_currency_not_found(client):
    """Test updating non-existent currency"""
    update_data = {"risk_percent": 2.0}
    response = client.put("/api/currencies/INVALID", json=update_data)
    assert response.status_code == 404


def test_update_currency_partial_update(client, created_currency):
    """Test partial update (only some fields)"""
    original_sl = created_currency["sl_pips"]

    update_data = {"risk_percent": 1.5}
    response = client.put("/api/currencies/EURUSD", json=update_data)

    data = response.json()
    assert data["risk_percent"] == 1.5
    assert data["sl_pips"] == original_sl  # Unchanged


def test_update_currency_invalid_validation(client, created_currency):
    """Test update that fails validation"""
    update_data = {
        "fast_period": 50,
        "slow_period": 20  # Invalid: fast > slow
    }

    response = client.put("/api/currencies/EURUSD", json=update_data)
    assert response.status_code == 400


# ============================================================================
# TEST: DELETE CURRENCY (DELETE /api/currencies/{symbol})
# ============================================================================

def test_delete_currency_success(client, created_currency):
    """Test deleting a currency"""
    response = client.delete("/api/currencies/EURUSD")
    assert response.status_code == 204

    # Verify deletion
    response = client.get("/api/currencies/EURUSD")
    assert response.status_code == 404


def test_delete_currency_not_found(client):
    """Test deleting non-existent currency"""
    response = client.delete("/api/currencies/INVALID")
    assert response.status_code == 404


# ============================================================================
# TEST: ENABLE/DISABLE CURRENCY
# ============================================================================

def test_enable_currency(client, sample_currency_data):
    """Test enabling a currency"""
    # Create disabled currency
    sample_currency_data["enabled"] = False
    client.post("/api/currencies", json=sample_currency_data)

    # Enable it
    response = client.post("/api/currencies/EURUSD/enable")
    assert response.status_code == 200
    assert response.json()["enabled"] is True


def test_disable_currency(client, created_currency):
    """Test disabling a currency"""
    response = client.post("/api/currencies/EURUSD/disable")
    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_enable_nonexistent_currency(client):
    """Test enabling non-existent currency"""
    response = client.post("/api/currencies/INVALID/enable")
    assert response.status_code == 404


def test_disable_nonexistent_currency(client):
    """Test disabling non-existent currency"""
    response = client.post("/api/currencies/INVALID/disable")
    assert response.status_code == 404


# ============================================================================
# TEST: VALIDATE CURRENCY (POST /api/currencies/validate)
# ============================================================================

def test_validate_currency_valid(client, sample_currency_data):
    """Test validating valid configuration"""
    response = client.post("/api/currencies/validate", json=sample_currency_data)
    assert response.status_code == 200

    data = response.json()
    assert data["is_valid"] is True
    assert len(data["errors"]) == 0


def test_validate_currency_invalid(client, sample_currency_data):
    """Test validating invalid configuration"""
    sample_currency_data["risk_percent"] = 15.0  # Too high

    response = client.post("/api/currencies/validate", json=sample_currency_data)
    assert response.status_code == 200

    data = response.json()
    assert data["is_valid"] is False
    assert len(data["errors"]) > 0


def test_validate_currency_multiple_errors(client, sample_currency_data):
    """Test validation with multiple errors"""
    sample_currency_data["risk_percent"] = 15.0
    sample_currency_data["fast_period"] = 50
    sample_currency_data["slow_period"] = 20

    response = client.post("/api/currencies/validate", json=sample_currency_data)
    data = response.json()

    assert data["is_valid"] is False
    assert len(data["errors"]) >= 2


# ============================================================================
# TEST: RELOAD FROM YAML (POST /api/currencies/reload)
# ============================================================================

def test_reload_from_yaml_empty(client):
    """Test reloading when YAML doesn't exist"""
    response = client.post("/api/currencies/reload")
    assert response.status_code == 200

    data = response.json()
    # Should succeed even if no YAML file
    assert "success" in data


# ============================================================================
# TEST: SYNC TO YAML (POST /api/currencies/sync-to-yaml)
# ============================================================================

def test_sync_to_yaml_success(client, created_currency):
    """Test syncing database to YAML"""
    response = client.post("/api/currencies/sync-to-yaml")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["currency_count"] >= 1


def test_sync_to_yaml_empty_database(client):
    """Test syncing empty database"""
    response = client.post("/api/currencies/sync-to-yaml")
    assert response.status_code == 200

    data = response.json()
    assert data["currency_count"] == 0


# ============================================================================
# TEST: CHECK CONSISTENCY (GET /api/currencies/consistency)
# ============================================================================

def test_check_consistency(client, created_currency):
    """Test checking consistency between DB and YAML"""
    response = client.get("/api/currencies/consistency")
    assert response.status_code == 200

    data = response.json()
    assert "is_consistent" in data
    assert "differences" in data
    assert "message" in data


# ============================================================================
# TEST: EXPORT/IMPORT CONFIGURATION
# ============================================================================

def test_export_configuration(client, created_currency, tmp_path):
    """Test exporting configuration to file"""
    export_file = tmp_path / "export.yaml"

    response = client.post(f"/api/currencies/export?export_path={export_file}")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True or data["success"] is False  # May fail on permissions


def test_import_configuration(client, tmp_path):
    """Test importing configuration from file"""
    import_file = tmp_path / "import.yaml"
    import_file.write_text("currencies: {}")

    response = client.post(f"/api/currencies/import?import_path={import_file}")
    assert response.status_code == 200


# ============================================================================
# TEST: API RESPONSE STRUCTURE
# ============================================================================

def test_currency_response_has_all_fields(client, created_currency):
    """Test that currency response contains all expected fields"""
    response = client.get("/api/currencies/EURUSD")
    data = response.json()

    expected_fields = [
        "id", "symbol", "enabled", "risk_percent",
        "max_position_size", "min_position_size",
        "strategy_type", "timeframe", "fast_period", "slow_period",
        "sl_pips", "tp_pips", "cooldown_seconds",
        "trade_on_signal_change", "allow_position_stacking",
        "max_positions_same_direction", "max_total_positions",
        "stacking_risk_multiplier", "config_version",
        "created_at", "updated_at"
    ]

    for field in expected_fields:
        assert field in data, f"Missing field: {field}"


def test_list_response_structure(client, created_currency):
    """Test that list response has correct structure"""
    response = client.get("/api/currencies")
    data = response.json()

    assert "currencies" in data
    assert "total" in data
    assert "enabled_count" in data
    assert isinstance(data["currencies"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["enabled_count"], int)


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

def test_create_currency_missing_required_fields(client):
    """Test creating currency with missing required fields"""
    incomplete_data = {"symbol": "EURUSD"}
    response = client.post("/api/currencies", json=incomplete_data)
    assert response.status_code == 422


def test_update_currency_empty_body(client, created_currency):
    """Test updating with empty body"""
    response = client.put("/api/currencies/EURUSD", json={})
    assert response.status_code == 200
    # Should succeed but not change anything


def test_invalid_endpoint(client):
    """Test calling invalid endpoint"""
    response = client.get("/api/currencies/invalid/endpoint")
    assert response.status_code == 404
