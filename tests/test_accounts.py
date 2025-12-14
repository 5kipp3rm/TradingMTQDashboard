"""
Tests for Trading Account Management

Tests account CRUD operations, account switching, and default account management.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.api.app import app
from src.database import get_session, TradingAccount, init_db
from src.database.models import Base


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test"""
    init_db()
    yield
    # Cleanup after test
    with get_session() as session:
        session.query(TradingAccount).delete()
        session.commit()


class TestAccountCreation:
    """Test account creation operations"""

    def test_create_account_success(self, client):
        """Test successful account creation"""
        account_data = {
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345,
            "password": "test_password",
            "is_demo": True,
            "is_active": True,
            "is_default": False,
            "initial_balance": 10000.0,
            "currency": "USD",
            "description": "Test account description"
        }

        response = client.post("/api/accounts", json=account_data)
        assert response.status_code == 201

        data = response.json()
        assert data["account_number"] == 12345
        assert data["account_name"] == "Test Account"
        assert data["broker"] == "Test Broker"
        assert data["is_demo"] is True
        assert data["is_active"] is True
        assert data["currency"] == "USD"

    def test_create_first_account_sets_default(self, client):
        """Test that first account is automatically set as default"""
        account_data = {
            "account_number": 12345,
            "account_name": "First Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345,
            "is_default": False  # Even though False, should become True
        }

        response = client.post("/api/accounts", json=account_data)
        assert response.status_code == 201

        data = response.json()
        assert data["is_default"] is True

    def test_create_duplicate_account_number(self, client):
        """Test that duplicate account numbers are rejected"""
        account_data = {
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345
        }

        # Create first account
        response1 = client.post("/api/accounts", json=account_data)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post("/api/accounts", json=account_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_account_currency_uppercase(self, client):
        """Test that currency is converted to uppercase"""
        account_data = {
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345,
            "currency": "usd"  # lowercase
        }

        response = client.post("/api/accounts", json=account_data)
        assert response.status_code == 201

        data = response.json()
        assert data["currency"] == "USD"  # Should be uppercase


class TestAccountRetrieval:
    """Test account retrieval operations"""

    def test_list_accounts_empty(self, client):
        """Test listing accounts when none exist"""
        response = client.get("/api/accounts")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert data["active_count"] == 0
        assert data["default_account_id"] is None
        assert len(data["accounts"]) == 0

    def test_list_accounts_with_data(self, client):
        """Test listing accounts with existing accounts"""
        # Create multiple accounts
        for i in range(3):
            client.post("/api/accounts", json={
                "account_number": 10000 + i,
                "account_name": f"Account {i}",
                "broker": "Test Broker",
                "server": "TestServer-Demo",
                "login": 10000 + i
            })

        response = client.get("/api/accounts")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 3
        assert data["active_count"] == 3
        assert len(data["accounts"]) == 3

    def test_list_accounts_active_only(self, client):
        """Test filtering accounts by active status"""
        # Create active and inactive accounts
        client.post("/api/accounts", json={
            "account_number": 10001,
            "account_name": "Active Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 10001,
            "is_active": True
        })

        client.post("/api/accounts", json={
            "account_number": 10002,
            "account_name": "Inactive Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 10002,
            "is_active": False
        })

        response = client.get("/api/accounts?active_only=true")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert data["accounts"][0]["account_name"] == "Active Account"

    def test_get_account_by_id(self, client):
        """Test retrieving specific account by ID"""
        # Create account
        create_response = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345
        })
        account_id = create_response.json()["id"]

        # Retrieve account
        response = client.get(f"/api/accounts/{account_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == account_id
        assert data["account_number"] == 12345

    def test_get_nonexistent_account(self, client):
        """Test retrieving non-existent account"""
        response = client.get("/api/accounts/9999")
        assert response.status_code == 404


class TestAccountUpdate:
    """Test account update operations"""

    def test_update_account_success(self, client):
        """Test successful account update"""
        # Create account
        create_response = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Original Name",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345
        })
        account_id = create_response.json()["id"]

        # Update account
        update_data = {
            "account_name": "Updated Name",
            "description": "Updated description"
        }
        response = client.put(f"/api/accounts/{account_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["account_name"] == "Updated Name"
        assert data["description"] == "Updated description"

    def test_update_nonexistent_account(self, client):
        """Test updating non-existent account"""
        response = client.put("/api/accounts/9999", json={"account_name": "Test"})
        assert response.status_code == 404


class TestAccountDeletion:
    """Test account deletion operations"""

    def test_delete_account_success(self, client):
        """Test successful account deletion"""
        # Create account
        create_response = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345,
            "is_default": False
        })
        account_id = create_response.json()["id"]

        # Delete account
        response = client.delete(f"/api/accounts/{account_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/accounts/{account_id}")
        assert get_response.status_code == 404

    def test_delete_default_account_reassigns_default(self, client):
        """Test that deleting default account reassigns default to another active account"""
        # Create two accounts
        response1 = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "First Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345
        })
        account1_id = response1.json()["id"]

        response2 = client.post("/api/accounts", json={
            "account_number": 67890,
            "account_name": "Second Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 67890
        })
        account2_id = response2.json()["id"]

        # First account should be default
        assert response1.json()["is_default"] is True

        # Delete default account
        client.delete(f"/api/accounts/{account1_id}")

        # Check that second account became default
        response = client.get(f"/api/accounts/{account2_id}")
        assert response.json()["is_default"] is True


class TestDefaultAccount:
    """Test default account management"""

    def test_set_default_account(self, client):
        """Test setting an account as default"""
        # Create two accounts
        response1 = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Account 1",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345
        })
        account1_id = response1.json()["id"]

        response2 = client.post("/api/accounts", json={
            "account_number": 67890,
            "account_name": "Account 2",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 67890
        })
        account2_id = response2.json()["id"]

        # Set second account as default
        response = client.post(f"/api/accounts/{account2_id}/set-default")
        assert response.status_code == 200
        assert response.json()["is_default"] is True

        # Verify first account is no longer default
        response = client.get(f"/api/accounts/{account1_id}")
        assert response.json()["is_default"] is False

    def test_cannot_set_inactive_account_as_default(self, client):
        """Test that inactive account cannot be set as default"""
        # Create inactive account
        response = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Inactive Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345,
            "is_active": False
        })
        account_id = response.json()["id"]

        # Try to set as default
        response = client.post(f"/api/accounts/{account_id}/set-default")
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()


class TestAccountActivation:
    """Test account activation/deactivation"""

    def test_activate_account(self, client):
        """Test activating an inactive account"""
        # Create inactive account
        response = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345,
            "is_active": False
        })
        account_id = response.json()["id"]

        # Activate account
        response = client.post(f"/api/accounts/{account_id}/activate")
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_deactivate_account(self, client):
        """Test deactivating an active account"""
        # Create active account
        response = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345,
            "is_active": True
        })
        account_id = response.json()["id"]

        # Deactivate account
        response = client.post(f"/api/accounts/{account_id}/deactivate")
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_deactivate_default_account_reassigns_default(self, client):
        """Test that deactivating default account reassigns default to another active account"""
        # Create two accounts
        response1 = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Account 1",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345
        })
        account1_id = response1.json()["id"]

        response2 = client.post("/api/accounts", json={
            "account_number": 67890,
            "account_name": "Account 2",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 67890
        })
        account2_id = response2.json()["id"]

        # Deactivate default account (first one)
        response = client.post(f"/api/accounts/{account1_id}/deactivate")
        assert response.status_code == 200

        # Check that second account became default
        response = client.get(f"/api/accounts/{account2_id}")
        assert response.json()["is_default"] is True


class TestAccountFiltering:
    """Test analytics filtering by account"""

    def test_analytics_without_account_filter(self, client):
        """Test analytics endpoints work without account filtering"""
        response = client.get("/api/analytics/summary?days=30")
        assert response.status_code == 200

        data = response.json()
        assert "total_trades" in data
        assert data.get("account_id") is None

    def test_analytics_with_account_filter(self, client):
        """Test analytics endpoints accept account_id parameter"""
        # Create account
        create_response = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345
        })
        account_id = create_response.json()["id"]

        # Test analytics with account filter
        response = client.get(f"/api/analytics/summary?days=30&account_id={account_id}")
        assert response.status_code == 200

        data = response.json()
        assert data.get("account_id") == account_id

    def test_charts_with_account_filter(self, client):
        """Test chart endpoints accept account_id parameter"""
        # Create account
        create_response = client.post("/api/accounts", json={
            "account_number": 12345,
            "account_name": "Test Account",
            "broker": "Test Broker",
            "server": "TestServer-Demo",
            "login": 12345
        })
        account_id = create_response.json()["id"]

        # Test equity curve with account filter
        response = client.get(f"/api/charts/equity-curve?account_id={account_id}")
        assert response.status_code == 200

        # Test trade distribution with account filter
        response = client.get(f"/api/charts/trade-distribution?account_id={account_id}")
        assert response.status_code == 200
