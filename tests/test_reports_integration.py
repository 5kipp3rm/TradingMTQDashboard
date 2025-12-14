"""
Integration Tests for Reports System

End-to-end integration tests covering the complete report workflow:
- Configuration creation via API
- Scheduled report generation
- Email delivery
- History tracking
- Error handling
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import time

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.database import get_session, init_db, TradingAccount, DailyPerformance
from src.database.report_models import (
    ReportConfiguration,
    ReportHistory,
    ReportFrequency,
    ReportFormat
)
from src.reports.generator import ReportGenerator
from src.reports.email_service import EmailService, EmailConfiguration
from src.reports.scheduler import ReportScheduler


@pytest.fixture
def temp_report_dir():
    """Create temporary directory for test reports"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


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
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_account():
    """Create sample trading account"""
    with get_session() as session:
        account = TradingAccount(
            account_number=12345,
            account_name="Integration Test Account",
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
def sample_daily_performance(sample_account):
    """Create sample daily performance records"""
    with get_session() as session:
        base_date = date.today() - timedelta(days=30)

        for i in range(30):
            performance = DailyPerformance(
                date=base_date + timedelta(days=i),
                total_trades=10,
                winning_trades=6,
                losing_trades=4,
                net_profit=Decimal("100.00") if i % 2 == 0 else Decimal("-50.00"),
                gross_profit=Decimal("200.00"),
                gross_loss=Decimal("-100.00"),
                win_rate=Decimal("60.00"),
                average_win=Decimal("33.33"),
                average_loss=Decimal("-25.00"),
                largest_win=Decimal("100.00"),
                largest_loss=Decimal("-50.00"),
                start_balance=Decimal(f"{10000 + i * 50}.00"),
                end_balance=Decimal(f"{10000 + (i + 1) * 50}.00"),
                start_equity=Decimal(f"{10000 + i * 50}.00"),
                end_equity=Decimal(f"{10000 + (i + 1) * 50}.00"),
                account_id=sample_account
            )
            session.add(performance)

        session.commit()


@pytest.fixture
def mock_email_service():
    """Create mock email service"""
    email_service = Mock(spec=EmailService)
    email_service.send_report.return_value = True
    return email_service


@pytest.fixture
def report_scheduler(temp_report_dir, mock_email_service):
    """Create report scheduler instance"""
    report_generator = ReportGenerator(output_dir=temp_report_dir)
    scheduler = ReportScheduler(
        report_generator=report_generator,
        email_service=mock_email_service
    )
    yield scheduler
    scheduler.stop()


class TestEndToEndReportWorkflow:
    """Test complete end-to-end report workflows"""

    def test_create_and_generate_report_via_api(
        self,
        client,
        sample_account,
        sample_daily_performance
    ):
        """Test creating report config via API and generating ad-hoc report"""

        # Step 1: Create report configuration via API
        config_data = {
            "name": "End-to-End Test Report",
            "description": "Integration test report",
            "frequency": "daily",
            "time_of_day": "09:00",
            "report_format": "pdf",
            "include_trades": True,
            "include_charts": False,
            "days_lookback": 30,
            "account_id": sample_account,
            "recipients": ["test@example.com"],
            "is_active": True
        }

        response = client.post("/api/reports/configurations", json=config_data)
        assert response.status_code == 201
        config = response.json()
        config_id = config["id"]

        # Step 2: Generate ad-hoc report
        generate_request = {
            "start_date": (date.today() - timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat(),
            "account_id": sample_account,
            "include_trades": True,
            "include_charts": False
        }

        response = client.post("/api/reports/generate", json=generate_request)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "report_path" in result

        # Step 3: Verify report file exists
        report_path = Path(result["report_path"])
        assert report_path.exists()
        assert report_path.stat().st_size > 0

        # Cleanup
        report_path.unlink()

    def test_scheduled_report_generation_workflow(
        self,
        report_scheduler,
        sample_account,
        sample_daily_performance
    ):
        """Test scheduled report generation with email delivery"""

        # Step 1: Create report configuration in database
        with get_session() as session:
            config = ReportConfiguration(
                name="Scheduled Integration Test",
                frequency=ReportFrequency.DAILY,
                time_of_day="09:00",
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="integration@example.com",
                is_active=True
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            config_id = config.id

        # Step 2: Manually trigger report generation
        report_scheduler._generate_scheduled_report(config_id)

        # Step 3: Verify history record was created
        with get_session() as session:
            history = session.query(ReportHistory).filter(
                ReportHistory.config_id == config_id
            ).first()

            assert history is not None
            assert history.success is True
            assert history.file_path is not None
            assert Path(history.file_path).exists()
            assert history.email_sent is True

        # Step 4: Verify email was sent
        assert report_scheduler.email_service.send_report.called
        call_args = report_scheduler.email_service.send_report.call_args
        assert call_args[1]['to_emails'] == ['integration@example.com']

        # Step 5: Verify configuration status was updated
        with get_session() as session:
            config = session.get(ReportConfiguration, config_id)
            assert config.last_run is not None
            assert config.last_success is not None
            assert config.run_count == 1
            assert config.last_error is None

    def test_report_failure_workflow(
        self,
        report_scheduler,
        sample_account
    ):
        """Test report generation failure handling and recording"""

        # Step 1: Create configuration
        with get_session() as session:
            config = ReportConfiguration(
                name="Failure Test Report",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            config_id = config.id

        # Step 2: Mock report generator to raise error
        report_scheduler.report_generator.generate_performance_report = Mock(
            side_effect=Exception("Simulated failure")
        )

        # Step 3: Trigger report generation
        report_scheduler._generate_scheduled_report(config_id)

        # Step 4: Verify failure was recorded in history
        with get_session() as session:
            history = session.query(ReportHistory).filter(
                ReportHistory.config_id == config_id
            ).first()

            assert history is not None
            assert history.success is False
            assert history.error_message is not None
            assert "Simulated failure" in history.error_message
            assert history.email_sent is False

        # Step 5: Verify configuration status reflects failure
        with get_session() as session:
            config = session.get(ReportConfiguration, config_id)
            assert config.last_error is not None
            assert "Simulated failure" in config.last_error


class TestMultiAccountReporting:
    """Test reporting with multiple trading accounts"""

    def test_report_generation_for_multiple_accounts(
        self,
        client,
        sample_daily_performance
    ):
        """Test generating reports for multiple accounts"""

        # Create second account
        with get_session() as session:
            account2 = TradingAccount(
                account_number=67890,
                account_name="Second Test Account",
                broker="Test Broker",
                server="TestServer-Demo",
                login=67890,
                is_demo=True,
                is_active=True,
                is_default=False,
                initial_balance=Decimal("20000.00"),
                currency="USD"
            )
            session.add(account2)
            session.commit()
            session.refresh(account2)
            account2_id = account2.id

            # Add performance data for second account
            base_date = date.today() - timedelta(days=10)
            for i in range(10):
                performance = DailyPerformance(
                    date=base_date + timedelta(days=i),
                    total_trades=5,
                    winning_trades=3,
                    losing_trades=2,
                    net_profit=Decimal("75.00"),
                    gross_profit=Decimal("150.00"),
                    gross_loss=Decimal("-75.00"),
                    win_rate=Decimal("60.00"),
                    average_win=Decimal("50.00"),
                    average_loss=Decimal("-37.50"),
                    largest_win=Decimal("75.00"),
                    largest_loss=Decimal("-50.00"),
                    start_balance=Decimal(f"{20000 + i * 75}.00"),
                    end_balance=Decimal(f"{20000 + (i + 1) * 75}.00"),
                    start_equity=Decimal(f"{20000 + i * 75}.00"),
                    end_equity=Decimal(f"{20000 + (i + 1) * 75}.00"),
                    account_id=account2_id
                )
                session.add(performance)
            session.commit()

        # Generate report for all accounts
        generate_request = {
            "start_date": (date.today() - timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat(),
            "include_trades": False,
            "include_charts": False
        }

        response = client.post("/api/reports/generate", json=generate_request)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

        # Cleanup
        Path(result["report_path"]).unlink()

    def test_account_specific_report_configuration(
        self,
        client,
        sample_account,
        sample_daily_performance
    ):
        """Test creating account-specific report configurations"""

        # Create report for specific account
        config_data = {
            "name": "Account-Specific Report",
            "frequency": "daily",
            "report_format": "pdf",
            "include_trades": True,
            "include_charts": False,
            "days_lookback": 7,
            "account_id": sample_account,  # Specific account
            "recipients": ["account-test@example.com"],
            "is_active": True
        }

        response = client.post("/api/reports/configurations", json=config_data)
        assert response.status_code == 201
        config = response.json()
        assert config["account_id"] == sample_account


class TestReportConfigurationLifecycle:
    """Test complete CRUD lifecycle of report configurations"""

    def test_complete_configuration_lifecycle(
        self,
        client,
        sample_account
    ):
        """Test create, read, update, delete cycle"""

        # Step 1: Create configuration
        config_data = {
            "name": "Lifecycle Test Report",
            "frequency": "weekly",
            "day_of_week": 1,
            "time_of_day": "10:00",
            "report_format": "pdf",
            "include_trades": True,
            "include_charts": True,
            "days_lookback": 7,
            "account_id": sample_account,
            "recipients": ["lifecycle@example.com"],
            "email_subject": "Weekly Report",
            "is_active": True
        }

        response = client.post("/api/reports/configurations", json=config_data)
        assert response.status_code == 201
        config = response.json()
        config_id = config["id"]

        # Step 2: Read configuration
        response = client.get(f"/api/reports/configurations/{config_id}")
        assert response.status_code == 200
        retrieved_config = response.json()
        assert retrieved_config["name"] == "Lifecycle Test Report"

        # Step 3: Update configuration
        update_data = {
            "name": "Updated Lifecycle Report",
            "frequency": "monthly",
            "day_of_month": 15,
            "days_lookback": 30
        }

        response = client.put(
            f"/api/reports/configurations/{config_id}",
            json=update_data
        )
        assert response.status_code == 200
        updated_config = response.json()
        assert updated_config["name"] == "Updated Lifecycle Report"
        assert updated_config["frequency"] == "monthly"
        assert updated_config["day_of_month"] == 15

        # Step 4: Deactivate configuration
        response = client.post(
            f"/api/reports/configurations/{config_id}/deactivate"
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

        # Step 5: Reactivate configuration
        response = client.post(
            f"/api/reports/configurations/{config_id}/activate"
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True

        # Step 6: Delete configuration
        response = client.delete(f"/api/reports/configurations/{config_id}")
        assert response.status_code == 204

        # Step 7: Verify deletion
        response = client.get(f"/api/reports/configurations/{config_id}")
        assert response.status_code == 404


class TestReportHistoryTracking:
    """Test report history tracking and retrieval"""

    def test_history_tracking_across_multiple_runs(
        self,
        report_scheduler,
        sample_account,
        sample_daily_performance
    ):
        """Test that multiple report generations create proper history"""

        # Create configuration
        with get_session() as session:
            config = ReportConfiguration(
                name="History Tracking Test",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="history@example.com",
                is_active=True
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            config_id = config.id

        # Generate report multiple times
        for i in range(3):
            report_scheduler._generate_scheduled_report(config_id)
            time.sleep(0.1)  # Small delay to ensure different timestamps

        # Verify history records
        with get_session() as session:
            history_records = session.query(ReportHistory).filter(
                ReportHistory.config_id == config_id
            ).order_by(ReportHistory.generated_at).all()

            assert len(history_records) == 3

            # Verify all were successful
            for record in history_records:
                assert record.success is True
                assert record.file_path is not None
                assert record.email_sent is True
                assert record.execution_time_ms is not None

        # Verify configuration run count
        with get_session() as session:
            config = session.get(ReportConfiguration, config_id)
            assert config.run_count == 3

    def test_history_api_filtering(
        self,
        client,
        report_scheduler,
        sample_account,
        sample_daily_performance
    ):
        """Test history API filtering capabilities"""

        # Create two configurations
        with get_session() as session:
            config1 = ReportConfiguration(
                name="Config 1",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test1@example.com",
                is_active=True
            )
            config2 = ReportConfiguration(
                name="Config 2",
                frequency=ReportFrequency.WEEKLY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test2@example.com",
                is_active=True
            )
            session.add_all([config1, config2])
            session.commit()
            session.refresh(config1)
            session.refresh(config2)
            config1_id = config1.id
            config2_id = config2.id

        # Generate reports for both configs
        report_scheduler._generate_scheduled_report(config1_id)
        report_scheduler._generate_scheduled_report(config2_id)

        # Make one fail
        report_scheduler.report_generator.generate_performance_report = Mock(
            side_effect=Exception("Test error")
        )
        report_scheduler._generate_scheduled_report(config1_id)

        # Test: Get all history
        response = client.get("/api/reports/history")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

        # Test: Filter by config
        response = client.get(f"/api/reports/history?config_id={config1_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

        # Test: Filter by success only
        response = client.get("/api/reports/history?success_only=true")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

        # Test: Limit results
        response = client.get("/api/reports/history?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1


class TestSchedulerIntegration:
    """Test scheduler integration with configurations"""

    def test_scheduler_loads_active_configurations(
        self,
        report_scheduler,
        sample_account
    ):
        """Test that scheduler loads active configurations on start"""

        # Create active and inactive configurations
        with get_session() as session:
            active_config = ReportConfiguration(
                name="Active Config",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="active@example.com",
                is_active=True
            )
            inactive_config = ReportConfiguration(
                name="Inactive Config",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="inactive@example.com",
                is_active=False
            )
            session.add_all([active_config, inactive_config])
            session.commit()
            session.refresh(active_config)
            session.refresh(inactive_config)

        # Start scheduler
        report_scheduler.start()
        report_scheduler.reload_schedules()

        # Verify only active config was scheduled
        jobs = report_scheduler.get_scheduled_jobs()
        assert len(jobs) == 1
        assert jobs[0]['name'] == "Active Config"

    def test_scheduler_reschedule_on_update(
        self,
        report_scheduler,
        sample_account
    ):
        """Test that scheduler reschedules when configuration is updated"""

        # Create and schedule configuration
        with get_session() as session:
            config = ReportConfiguration(
                name="Reschedule Test",
                frequency=ReportFrequency.DAILY,
                time_of_day="09:00",
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            config_id = config.id

        report_scheduler.start()
        report_scheduler.schedule_report(config_id)

        # Get initial job
        initial_jobs = report_scheduler.get_scheduled_jobs()
        assert len(initial_jobs) == 1

        # Update time
        with get_session() as session:
            config = session.get(ReportConfiguration, config_id)
            config.time_of_day = "15:00"
            session.commit()

        # Reschedule
        report_scheduler.schedule_report(config_id)

        # Verify job was updated
        updated_jobs = report_scheduler.get_scheduled_jobs()
        assert len(updated_jobs) == 1


class TestErrorRecovery:
    """Test error recovery and resilience"""

    def test_continue_after_single_report_failure(
        self,
        report_scheduler,
        sample_account,
        sample_daily_performance
    ):
        """Test that scheduler continues after single report failure"""

        # Create two configurations
        with get_session() as session:
            config1 = ReportConfiguration(
                name="Will Fail",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="fail@example.com",
                is_active=True
            )
            config2 = ReportConfiguration(
                name="Will Succeed",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="success@example.com",
                is_active=True
            )
            session.add_all([config1, config2])
            session.commit()
            session.refresh(config1)
            session.refresh(config2)
            config1_id = config1.id
            config2_id = config2.id

        # Make first report fail
        original_generate = report_scheduler.report_generator.generate_performance_report

        def conditional_fail(*args, **kwargs):
            # Check if this is for the failing config by checking the call count
            if not hasattr(conditional_fail, 'call_count'):
                conditional_fail.call_count = 0
            conditional_fail.call_count += 1

            if conditional_fail.call_count == 1:
                raise Exception("Simulated failure")
            return original_generate(*args, **kwargs)

        report_scheduler.report_generator.generate_performance_report = conditional_fail

        # Generate reports
        report_scheduler._generate_scheduled_report(config1_id)
        report_scheduler._generate_scheduled_report(config2_id)

        # Verify first failed, second succeeded
        with get_session() as session:
            history1 = session.query(ReportHistory).filter(
                ReportHistory.config_id == config1_id
            ).first()
            assert history1.success is False

            history2 = session.query(ReportHistory).filter(
                ReportHistory.config_id == config2_id
            ).first()
            assert history2.success is True
