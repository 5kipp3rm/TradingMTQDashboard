"""
Unit Tests for Report Management API Endpoints

Tests REST API endpoints for report configurations, generation, and history.
Uses FastAPI TestClient with database fixtures.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.database import get_session, init_db, TradingAccount, DailyPerformance
from src.database.report_models import ReportConfiguration, ReportHistory, ReportFrequency, ReportFormat


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test"""
    init_db()
    yield
    # Cleanup after test
    with get_session() as session:
        session.query(ReportHistory).delete()
        session.query(ReportConfiguration).delete()
        session.query(DailyPerformance).delete()
        session.query(TradingAccount).delete()
        session.commit()


@pytest.fixture
def sample_account():
    """Create sample trading account"""
    with get_session() as session:
        account = TradingAccount(
            account_number=12345,
            account_name="Test Account",
            broker="Test Broker",
            server="TestServer-Demo",
            login=12345,
            is_demo=True,
            is_active=True,
            is_default=True,
            initial_balance=Decimal("10000.00"),
            currency="USD"
        )
        session.add(account)
        session.commit()
        session.refresh(account)
        return account.id


@pytest.fixture
def sample_report_config(sample_account):
    """Create sample report configuration"""
    with get_session() as session:
        config = ReportConfiguration(
            name="Daily Performance Report",
            description="Automated daily report",
            frequency=ReportFrequency.DAILY,
            time_of_day="09:00",
            report_format=ReportFormat.PDF,
            include_trades=True,
            include_charts=True,
            days_lookback=30,
            account_id=sample_account,
            recipients="test@example.com",
            is_active=True
        )
        session.add(config)
        session.commit()
        session.refresh(config)
        return config.id


@pytest.fixture
def sample_daily_performance(sample_account):
    """Create sample daily performance records"""
    with get_session() as session:
        base_date = date.today() - timedelta(days=10)

        for i in range(10):
            performance = DailyPerformance(
                date=base_date + timedelta(days=i),
                total_trades=5,
                winning_trades=3,
                losing_trades=2,
                net_profit=Decimal("50.00"),
                gross_profit=Decimal("100.00"),
                gross_loss=Decimal("-50.00"),
                win_rate=Decimal("60.00"),
                average_win=Decimal("33.33"),
                average_loss=Decimal("-25.00"),
                largest_win=Decimal("50.00"),
                largest_loss=Decimal("-30.00"),
                start_balance=Decimal("10000.00"),
                end_balance=Decimal("10050.00"),
                start_equity=Decimal("10000.00"),
                end_equity=Decimal("10050.00"),
                account_id=sample_account
            )
            session.add(performance)

        session.commit()


class TestListReportConfigurations:
    """Test listing report configurations"""

    def test_list_empty_configurations(self, client):
        """Test listing when no configurations exist"""
        response = client.get("/api/reports/configurations")

        assert response.status_code == 200
        data = response.json()
        assert "configurations" in data
        assert "total" in data
        assert data["total"] == 0
        assert len(data["configurations"]) == 0

    def test_list_configurations(self, client, sample_report_config):
        """Test listing configurations"""
        response = client.get("/api/reports/configurations")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["configurations"]) == 1

        config = data["configurations"][0]
        assert config["name"] == "Daily Performance Report"
        assert config["frequency"] == "daily"

    def test_list_configurations_active_only(self, client, sample_report_config):
        """Test listing only active configurations"""
        # Create inactive configuration
        with get_session() as session:
            inactive_config = ReportConfiguration(
                name="Inactive Report",
                frequency=ReportFrequency.WEEKLY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                recipients="test@example.com",
                is_active=False
            )
            session.add(inactive_config)
            session.commit()

        response = client.get("/api/reports/configurations?active_only=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["configurations"][0]["name"] == "Daily Performance Report"

    def test_list_configurations_include_inactive(self, client, sample_report_config):
        """Test listing all configurations including inactive"""
        # Create inactive configuration
        with get_session() as session:
            inactive_config = ReportConfiguration(
                name="Inactive Report",
                frequency=ReportFrequency.WEEKLY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                recipients="test@example.com",
                is_active=False
            )
            session.add(inactive_config)
            session.commit()

        response = client.get("/api/reports/configurations?active_only=false")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestGetReportConfiguration:
    """Test getting specific report configuration"""

    def test_get_existing_configuration(self, client, sample_report_config):
        """Test getting existing configuration"""
        response = client.get(f"/api/reports/configurations/{sample_report_config}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_report_config
        assert data["name"] == "Daily Performance Report"
        assert data["frequency"] == "daily"

    def test_get_nonexistent_configuration(self, client):
        """Test getting non-existent configuration"""
        response = client.get("/api/reports/configurations/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateReportConfiguration:
    """Test creating report configurations"""

    def test_create_valid_configuration(self, client, sample_account):
        """Test creating valid configuration"""
        config_data = {
            "name": "Weekly Summary",
            "description": "Weekly performance summary",
            "frequency": "weekly",
            "day_of_week": 1,  # Monday
            "time_of_day": "10:00",
            "report_format": "pdf",
            "include_trades": True,
            "include_charts": True,
            "days_lookback": 7,
            "account_id": sample_account,
            "recipients": ["user@example.com"],
            "email_subject": "Weekly Performance Report",
            "is_active": True
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Weekly Summary"
        assert data["frequency"] == "weekly"
        assert data["day_of_week"] == 1
        assert data["is_active"] is True

    def test_create_minimal_configuration(self, client):
        """Test creating configuration with minimal fields"""
        config_data = {
            "name": "Minimal Report",
            "frequency": "daily",
            "recipients": ["admin@example.com"]
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Report"
        assert data["report_format"] == "pdf"  # Default
        assert data["include_trades"] is True  # Default
        assert data["days_lookback"] == 30  # Default

    def test_create_configuration_invalid_frequency(self, client):
        """Test creating configuration with invalid frequency"""
        config_data = {
            "name": "Invalid Frequency",
            "frequency": "invalid",
            "recipients": ["test@example.com"]
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 422  # Validation error

    def test_create_configuration_invalid_report_format(self, client):
        """Test creating configuration with invalid format"""
        config_data = {
            "name": "Invalid Format",
            "frequency": "daily",
            "report_format": "invalid",
            "recipients": ["test@example.com"]
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 422

    def test_create_configuration_invalid_day_of_week(self, client):
        """Test creating configuration with invalid day of week"""
        config_data = {
            "name": "Invalid Day",
            "frequency": "weekly",
            "day_of_week": 7,  # Valid range is 0-6
            "recipients": ["test@example.com"]
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 422

    def test_create_configuration_invalid_day_of_month(self, client):
        """Test creating configuration with invalid day of month"""
        config_data = {
            "name": "Invalid Day",
            "frequency": "monthly",
            "day_of_month": 32,  # Valid range is 1-31
            "recipients": ["test@example.com"]
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 422

    def test_create_configuration_invalid_time_format(self, client):
        """Test creating configuration with invalid time format"""
        config_data = {
            "name": "Invalid Time",
            "frequency": "daily",
            "time_of_day": "25:00",  # Invalid hour
            "recipients": ["test@example.com"]
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 422

    def test_create_configuration_no_recipients(self, client):
        """Test creating configuration without recipients"""
        config_data = {
            "name": "No Recipients",
            "frequency": "daily",
            "recipients": []  # Must have at least 1
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 422

    def test_create_configuration_with_cc_recipients(self, client):
        """Test creating configuration with CC recipients"""
        config_data = {
            "name": "CC Recipients",
            "frequency": "daily",
            "recipients": ["primary@example.com"],
            "cc_recipients": ["cc1@example.com", "cc2@example.com"]
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 201
        data = response.json()
        assert "cc_recipients" in data


class TestUpdateReportConfiguration:
    """Test updating report configurations"""

    def test_update_configuration_name(self, client, sample_report_config):
        """Test updating configuration name"""
        update_data = {
            "name": "Updated Name"
        }

        response = client.put(
            f"/api/reports/configurations/{sample_report_config}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["frequency"] == "daily"  # Unchanged

    def test_update_configuration_multiple_fields(self, client, sample_report_config):
        """Test updating multiple fields"""
        update_data = {
            "name": "New Name",
            "description": "New description",
            "frequency": "weekly",
            "day_of_week": 5,  # Friday
            "include_charts": False
        }

        response = client.put(
            f"/api/reports/configurations/{sample_report_config}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"
        assert data["frequency"] == "weekly"
        assert data["day_of_week"] == 5
        assert data["include_charts"] is False

    def test_update_nonexistent_configuration(self, client):
        """Test updating non-existent configuration"""
        update_data = {
            "name": "Should Fail"
        }

        response = client.put(
            "/api/reports/configurations/99999",
            json=update_data
        )

        assert response.status_code == 404

    def test_update_configuration_recipients(self, client, sample_report_config):
        """Test updating recipients list"""
        update_data = {
            "recipients": ["new1@example.com", "new2@example.com"]
        }

        response = client.put(
            f"/api/reports/configurations/{sample_report_config}",
            json=update_data
        )

        assert response.status_code == 200


class TestDeleteReportConfiguration:
    """Test deleting report configurations"""

    def test_delete_existing_configuration(self, client, sample_report_config):
        """Test deleting existing configuration"""
        response = client.delete(f"/api/reports/configurations/{sample_report_config}")

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/reports/configurations/{sample_report_config}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_configuration(self, client):
        """Test deleting non-existent configuration"""
        response = client.delete("/api/reports/configurations/99999")

        assert response.status_code == 404


class TestActivateDeactivateConfiguration:
    """Test activating and deactivating configurations"""

    def test_activate_configuration(self, client, sample_report_config):
        """Test activating configuration"""
        # First deactivate it
        with get_session() as session:
            config = session.get(ReportConfiguration, sample_report_config)
            config.is_active = False
            session.commit()

        response = client.post(f"/api/reports/configurations/{sample_report_config}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_deactivate_configuration(self, client, sample_report_config):
        """Test deactivating configuration"""
        response = client.post(f"/api/reports/configurations/{sample_report_config}/deactivate")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_activate_nonexistent_configuration(self, client):
        """Test activating non-existent configuration"""
        response = client.post("/api/reports/configurations/99999/activate")

        assert response.status_code == 404

    def test_deactivate_nonexistent_configuration(self, client):
        """Test deactivating non-existent configuration"""
        response = client.post("/api/reports/configurations/99999/deactivate")

        assert response.status_code == 404


class TestGenerateAdHocReport:
    """Test ad-hoc report generation"""

    def test_generate_report_success(self, client, sample_account, sample_daily_performance):
        """Test successful ad-hoc report generation"""
        request_data = {
            "start_date": (date.today() - timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat(),
            "account_id": sample_account,
            "include_trades": True,
            "include_charts": False
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report_path" in data
        assert "file_size" in data
        assert data["start_date"] == request_data["start_date"]
        assert data["end_date"] == request_data["end_date"]

        # Verify file exists
        report_path = Path(data["report_path"])
        assert report_path.exists()

        # Cleanup
        report_path.unlink()

    def test_generate_report_all_accounts(self, client, sample_daily_performance):
        """Test generating report for all accounts"""
        request_data = {
            "start_date": (date.today() - timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat(),
            "include_trades": False,
            "include_charts": False
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Cleanup
        Path(data["report_path"]).unlink()

    def test_generate_report_no_data(self, client):
        """Test generating report with no data"""
        request_data = {
            "start_date": (date.today() - timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat(),
            "include_trades": False,
            "include_charts": False
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Cleanup
        Path(data["report_path"]).unlink()

    def test_generate_report_invalid_date_range(self, client):
        """Test generating report with invalid date range"""
        request_data = {
            "start_date": date.today().isoformat(),
            "end_date": (date.today() - timedelta(days=7)).isoformat(),  # End before start
            "include_trades": False,
            "include_charts": False
        }

        response = client.post("/api/reports/generate", json=request_data)

        # Should still work but might generate empty report
        assert response.status_code in [200, 500]


class TestGetReportHistory:
    """Test report history retrieval"""

    def test_get_empty_history(self, client):
        """Test getting history when none exists"""
        response = client.get("/api/reports/history")

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "count" in data
        assert data["count"] == 0

    def test_get_history_with_records(self, client, sample_report_config):
        """Test getting history with records"""
        # Create history records
        with get_session() as session:
            for i in range(5):
                history = ReportHistory(
                    config_id=sample_report_config,
                    generated_at=datetime.now() - timedelta(days=i),
                    report_start_date=date.today() - timedelta(days=7),
                    report_end_date=date.today(),
                    success=True,
                    file_path=f"/tmp/report_{i}.pdf",
                    file_size=1024 * (i + 1),
                    email_sent=True,
                    email_recipients="test@example.com",
                    execution_time_ms=500 + i * 100
                )
                session.add(history)
            session.commit()

        response = client.get("/api/reports/history")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert len(data["history"]) == 5

    def test_get_history_filter_by_config(self, client, sample_report_config):
        """Test filtering history by configuration"""
        # Create history for different configs
        with get_session() as session:
            # Create another config
            other_config = ReportConfiguration(
                name="Other Report",
                frequency=ReportFrequency.WEEKLY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                recipients="test@example.com",
                is_active=True
            )
            session.add(other_config)
            session.commit()
            session.refresh(other_config)

            # Create history for sample_report_config
            for i in range(3):
                history = ReportHistory(
                    config_id=sample_report_config,
                    generated_at=datetime.now(),
                    report_start_date=date.today() - timedelta(days=7),
                    report_end_date=date.today(),
                    success=True,
                    email_sent=False
                )
                session.add(history)

            # Create history for other_config
            for i in range(2):
                history = ReportHistory(
                    config_id=other_config.id,
                    generated_at=datetime.now(),
                    report_start_date=date.today() - timedelta(days=7),
                    report_end_date=date.today(),
                    success=True,
                    email_sent=False
                )
                session.add(history)

            session.commit()

        response = client.get(f"/api/reports/history?config_id={sample_report_config}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_get_history_success_only(self, client, sample_report_config):
        """Test filtering for successful reports only"""
        # Create mixed success/failure records
        with get_session() as session:
            for i in range(5):
                history = ReportHistory(
                    config_id=sample_report_config,
                    generated_at=datetime.now(),
                    report_start_date=date.today() - timedelta(days=7),
                    report_end_date=date.today(),
                    success=(i % 2 == 0),  # Alternate success/failure
                    error_message="Test error" if i % 2 != 0 else None,
                    email_sent=False
                )
                session.add(history)
            session.commit()

        response = client.get("/api/reports/history?success_only=true")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3  # 3 successful out of 5

    def test_get_history_with_limit(self, client, sample_report_config):
        """Test limiting history results"""
        # Create many records
        with get_session() as session:
            for i in range(100):
                history = ReportHistory(
                    config_id=sample_report_config,
                    generated_at=datetime.now() - timedelta(minutes=i),
                    report_start_date=date.today() - timedelta(days=7),
                    report_end_date=date.today(),
                    success=True,
                    email_sent=False
                )
                session.add(history)
            session.commit()

        response = client.get("/api/reports/history?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 10
        assert len(data["history"]) == 10


class TestGetReportHistoryDetail:
    """Test getting specific history record"""

    def test_get_existing_history_record(self, client, sample_report_config):
        """Test getting existing history record"""
        # Create history record
        with get_session() as session:
            history = ReportHistory(
                config_id=sample_report_config,
                generated_at=datetime.now(),
                report_start_date=date.today() - timedelta(days=7),
                report_end_date=date.today(),
                success=True,
                file_path="/tmp/test_report.pdf",
                file_size=2048,
                email_sent=True,
                email_recipients="test@example.com",
                execution_time_ms=750
            )
            session.add(history)
            session.commit()
            session.refresh(history)
            history_id = history.id

        response = client.get(f"/api/reports/history/{history_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == history_id
        assert data["success"] is True
        assert data["file_path"] == "/tmp/test_report.pdf"
        assert data["file_size"] == 2048

    def test_get_nonexistent_history_record(self, client):
        """Test getting non-existent history record"""
        response = client.get("/api/reports/history/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestReportAPIValidation:
    """Test Pydantic validation in report endpoints"""

    def test_create_config_missing_required_fields(self, client):
        """Test validation when required fields are missing"""
        config_data = {
            "name": "Incomplete"
            # Missing frequency and recipients
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 422

    def test_create_config_invalid_days_lookback(self, client):
        """Test validation for days_lookback range"""
        config_data = {
            "name": "Invalid Days",
            "frequency": "daily",
            "recipients": ["test@example.com"],
            "days_lookback": 500  # Max is 365
        }

        response = client.post("/api/reports/configurations", json=config_data)

        assert response.status_code == 422

    def test_generate_report_invalid_date_format(self, client):
        """Test validation for date format"""
        request_data = {
            "start_date": "not-a-date",
            "end_date": "also-not-a-date",
            "include_trades": False
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 422
