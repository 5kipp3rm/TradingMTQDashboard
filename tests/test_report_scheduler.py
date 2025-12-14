"""
Unit Tests for Report Scheduler

Tests scheduled report generation with APScheduler including
daily, weekly, monthly schedules, error handling, and history tracking.
"""

import pytest
from datetime import datetime, date, timedelta, time as datetime_time
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, call
import time as time_module

from apscheduler.triggers.cron import CronTrigger

from src.reports.scheduler import ReportScheduler
from src.reports.generator import ReportGenerator
from src.reports.email_service import EmailService, EmailConfiguration
from src.database import get_session, init_db, TradingAccount, DailyPerformance
from src.database.report_models import (
    ReportConfiguration,
    ReportHistory,
    ReportFrequency,
    ReportFormat
)


@pytest.fixture
def temp_report_dir():
    """Create temporary directory for test reports"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
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


@pytest.fixture
def mock_email_service():
    """Create mock email service"""
    email_service = Mock(spec=EmailService)
    email_service.send_report.return_value = True
    return email_service


@pytest.fixture
def scheduler(temp_report_dir, mock_email_service):
    """Create scheduler instance"""
    report_generator = ReportGenerator(output_dir=temp_report_dir)
    scheduler = ReportScheduler(
        report_generator=report_generator,
        email_service=mock_email_service
    )
    yield scheduler
    # Cleanup
    scheduler.stop()


class TestSchedulerInitialization:
    """Test scheduler initialization"""

    def test_init_default_generator(self):
        """Test initialization with default report generator"""
        scheduler = ReportScheduler()
        assert scheduler.report_generator is not None
        assert scheduler.email_service is None
        assert not scheduler.scheduler.running
        scheduler.stop()

    def test_init_with_custom_generator(self, temp_report_dir):
        """Test initialization with custom report generator"""
        generator = ReportGenerator(output_dir=temp_report_dir)
        scheduler = ReportScheduler(report_generator=generator)
        assert scheduler.report_generator == generator
        scheduler.stop()

    def test_init_with_email_service(self, mock_email_service):
        """Test initialization with email service"""
        scheduler = ReportScheduler(email_service=mock_email_service)
        assert scheduler.email_service == mock_email_service
        scheduler.stop()


class TestSchedulerStartStop:
    """Test scheduler start and stop"""

    def test_start_scheduler(self, scheduler):
        """Test starting the scheduler"""
        scheduler.start()
        assert scheduler.scheduler.running

    def test_stop_scheduler(self, scheduler):
        """Test stopping the scheduler"""
        scheduler.start()
        assert scheduler.scheduler.running

        scheduler.stop()
        assert not scheduler.scheduler.running

    def test_start_already_running(self, scheduler):
        """Test starting scheduler when already running"""
        scheduler.start()
        assert scheduler.scheduler.running

        scheduler.start()  # Should not raise error
        assert scheduler.scheduler.running

    def test_stop_already_stopped(self, scheduler):
        """Test stopping scheduler when already stopped"""
        assert not scheduler.scheduler.running
        scheduler.stop()  # Should not raise error
        assert not scheduler.scheduler.running


class TestScheduleReport:
    """Test scheduling individual reports"""

    def test_schedule_daily_report(self, scheduler, sample_account):
        """Test scheduling daily report"""
        # Create daily report config
        with get_session() as session:
            config = ReportConfiguration(
                name="Daily Report",
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

        scheduler.start()
        scheduler.schedule_report(config_id)

        # Verify job was created
        assert config_id in scheduler._job_map
        job_id = scheduler._job_map[config_id]
        job = scheduler.scheduler.get_job(job_id)
        assert job is not None
        assert job.name == "Daily Report"

    def test_schedule_weekly_report(self, scheduler, sample_account):
        """Test scheduling weekly report"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Weekly Report",
                frequency=ReportFrequency.WEEKLY,
                day_of_week=1,  # Monday
                time_of_day="10:00",
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

        scheduler.start()
        scheduler.schedule_report(config_id)

        assert config_id in scheduler._job_map

    def test_schedule_monthly_report(self, scheduler, sample_account):
        """Test scheduling monthly report"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Monthly Report",
                frequency=ReportFrequency.MONTHLY,
                day_of_month=1,
                time_of_day="08:00",
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=30,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            config_id = config.id

        scheduler.start()
        scheduler.schedule_report(config_id)

        assert config_id in scheduler._job_map

    def test_schedule_nonexistent_config(self, scheduler):
        """Test scheduling non-existent configuration"""
        scheduler.start()

        with pytest.raises(ValueError, match="not found"):
            scheduler.schedule_report(99999)

    def test_schedule_inactive_config(self, scheduler, sample_account):
        """Test scheduling inactive configuration"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Inactive Report",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=False  # Inactive
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            config_id = config.id

        scheduler.start()
        scheduler.schedule_report(config_id)

        # Should not be scheduled
        assert config_id not in scheduler._job_map

    def test_schedule_updates_next_run(self, scheduler, sample_account):
        """Test that scheduling updates next_run time in database"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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

        scheduler.start()
        scheduler.schedule_report(config_id)

        # Verify next_run was updated
        with get_session() as session:
            config = session.get(ReportConfiguration, config_id)
            assert config.next_run is not None


class TestUnscheduleReport:
    """Test unscheduling reports"""

    def test_unschedule_report(self, scheduler, sample_account):
        """Test unscheduling a report"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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

        scheduler.start()
        scheduler.schedule_report(config_id)
        assert config_id in scheduler._job_map

        scheduler.unschedule_report(config_id)
        assert config_id not in scheduler._job_map

    def test_unschedule_nonexistent_report(self, scheduler):
        """Test unscheduling non-existent report"""
        scheduler.start()
        scheduler.unschedule_report(99999)  # Should not raise error


class TestReloadSchedules:
    """Test reloading all schedules"""

    def test_reload_empty_schedules(self, scheduler):
        """Test reloading when no configurations exist"""
        scheduler.start()
        scheduler.reload_schedules()

        assert len(scheduler._job_map) == 0

    def test_reload_multiple_schedules(self, scheduler, sample_account):
        """Test reloading multiple configurations"""
        # Create multiple configs
        config_ids = []
        with get_session() as session:
            for i in range(3):
                config = ReportConfiguration(
                    name=f"Report {i}",
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
                config_ids.append(config.id)

        scheduler.start()
        scheduler.reload_schedules()

        assert len(scheduler._job_map) == 3
        for config_id in config_ids:
            assert config_id in scheduler._job_map

    def test_reload_skips_inactive(self, scheduler, sample_account):
        """Test that reload skips inactive configurations"""
        with get_session() as session:
            # Active config
            active_config = ReportConfiguration(
                name="Active Report",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )
            session.add(active_config)

            # Inactive config
            inactive_config = ReportConfiguration(
                name="Inactive Report",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=False
            )
            session.add(inactive_config)

            session.commit()
            session.refresh(active_config)
            session.refresh(inactive_config)

        scheduler.start()
        scheduler.reload_schedules()

        assert len(scheduler._job_map) == 1
        assert active_config.id in scheduler._job_map
        assert inactive_config.id not in scheduler._job_map


class TestGenerateScheduledReport:
    """Test report generation triggered by scheduler"""

    def test_generate_report_success(
        self,
        scheduler,
        sample_account,
        sample_daily_performance
    ):
        """Test successful scheduled report generation"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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

        # Manually trigger report generation
        scheduler._generate_scheduled_report(config_id)

        # Verify history record was created
        with get_session() as session:
            history = session.query(ReportHistory).filter(
                ReportHistory.config_id == config_id
            ).first()

            assert history is not None
            assert history.success is True
            assert history.file_path is not None
            assert history.email_sent is True

        # Verify email was sent
        assert scheduler.email_service.send_report.called

    def test_generate_report_without_email(
        self,
        temp_report_dir,
        sample_account,
        sample_daily_performance
    ):
        """Test report generation without email service"""
        report_generator = ReportGenerator(output_dir=temp_report_dir)
        scheduler = ReportScheduler(
            report_generator=report_generator,
            email_service=None  # No email service
        )

        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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

        scheduler._generate_scheduled_report(config_id)

        # Verify history shows email not sent
        with get_session() as session:
            history = session.query(ReportHistory).filter(
                ReportHistory.config_id == config_id
            ).first()

            assert history is not None
            assert history.success is True
            assert history.email_sent is False

    def test_generate_report_updates_config_status(
        self,
        scheduler,
        sample_account,
        sample_daily_performance
    ):
        """Test that report generation updates configuration status"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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
            initial_run_count = config.run_count

        scheduler._generate_scheduled_report(config_id)

        # Verify status was updated
        with get_session() as session:
            config = session.get(ReportConfiguration, config_id)
            assert config.last_run is not None
            assert config.last_success is not None
            assert config.run_count == initial_run_count + 1
            assert config.last_error is None

    def test_generate_report_failure(self, scheduler, sample_account):
        """Test report generation failure handling"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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

        # Mock report generator to raise error
        scheduler.report_generator.generate_performance_report = Mock(
            side_effect=Exception("Test error")
        )

        scheduler._generate_scheduled_report(config_id)

        # Verify failure was recorded
        with get_session() as session:
            history = session.query(ReportHistory).filter(
                ReportHistory.config_id == config_id
            ).first()

            assert history is not None
            assert history.success is False
            assert history.error_message is not None
            assert "Test error" in history.error_message

            # Verify config status
            config = session.get(ReportConfiguration, config_id)
            assert config.last_error is not None

    def test_generate_report_nonexistent_config(self, scheduler):
        """Test generating report for non-existent configuration"""
        # Should log error but not raise exception
        scheduler._generate_scheduled_report(99999)

    def test_generate_report_inactive_config(self, scheduler, sample_account):
        """Test generating report for inactive configuration"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Inactive Report",
                frequency=ReportFrequency.DAILY,
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=False  # Inactive
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            config_id = config.id

        # Should log warning and return
        scheduler._generate_scheduled_report(config_id)

        # Verify no history was created
        with get_session() as session:
            history_count = session.query(ReportHistory).filter(
                ReportHistory.config_id == config_id
            ).count()
            assert history_count == 0


class TestTriggerCreation:
    """Test trigger creation for different frequencies"""

    def test_create_daily_trigger(self, scheduler, sample_account):
        """Test creating daily trigger"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Daily Report",
                frequency=ReportFrequency.DAILY,
                time_of_day="09:30",
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )

            trigger = scheduler._create_trigger(config)

            assert isinstance(trigger, CronTrigger)
            # Trigger should have hour=9, minute=30

    def test_create_weekly_trigger(self, scheduler, sample_account):
        """Test creating weekly trigger"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Weekly Report",
                frequency=ReportFrequency.WEEKLY,
                day_of_week=3,  # Wednesday
                time_of_day="10:00",
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )

            trigger = scheduler._create_trigger(config)

            assert isinstance(trigger, CronTrigger)

    def test_create_monthly_trigger(self, scheduler, sample_account):
        """Test creating monthly trigger"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Monthly Report",
                frequency=ReportFrequency.MONTHLY,
                day_of_month=15,
                time_of_day="08:00",
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=30,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )

            trigger = scheduler._create_trigger(config)

            assert isinstance(trigger, CronTrigger)

    def test_create_trigger_default_time(self, scheduler, sample_account):
        """Test creating trigger with default time"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Report",
                frequency=ReportFrequency.DAILY,
                time_of_day=None,  # No time specified
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )

            trigger = scheduler._create_trigger(config)

            assert isinstance(trigger, CronTrigger)
            # Should default to 09:00

    def test_create_trigger_invalid_time_format(self, scheduler, sample_account):
        """Test creating trigger with invalid time format"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Report",
                frequency=ReportFrequency.DAILY,
                time_of_day="invalid",  # Invalid format
                report_format=ReportFormat.PDF,
                include_trades=True,
                include_charts=False,
                days_lookback=7,
                account_id=sample_account,
                recipients="test@example.com",
                is_active=True
            )

            trigger = scheduler._create_trigger(config)

            # Should fall back to default 09:00
            assert isinstance(trigger, CronTrigger)


class TestSchedulerJobInfo:
    """Test job information retrieval"""

    def test_get_scheduled_jobs_empty(self, scheduler):
        """Test getting jobs when none are scheduled"""
        scheduler.start()
        jobs = scheduler.get_scheduled_jobs()

        assert jobs == []

    def test_get_scheduled_jobs(self, scheduler, sample_account):
        """Test getting scheduled jobs information"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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

        scheduler.start()
        scheduler.schedule_report(config_id)

        jobs = scheduler.get_scheduled_jobs()

        assert len(jobs) == 1
        assert jobs[0]['name'] == "Test Report"
        assert 'next_run_time' in jobs[0]
        assert 'trigger' in jobs[0]

    def test_get_job_status_existing(self, scheduler, sample_account):
        """Test getting status of existing job"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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

        scheduler.start()
        scheduler.schedule_report(config_id)

        status = scheduler.get_job_status(config_id)

        assert status is not None
        assert status['name'] == "Test Report"
        assert 'next_run_time' in status

    def test_get_job_status_nonexistent(self, scheduler):
        """Test getting status of non-existent job"""
        scheduler.start()
        status = scheduler.get_job_status(99999)

        assert status is None


class TestManualTrigger:
    """Test manual report triggering"""

    def test_trigger_report_now(
        self,
        scheduler,
        sample_account,
        sample_daily_performance
    ):
        """Test manually triggering report generation"""
        with get_session() as session:
            config = ReportConfiguration(
                name="Test Report",
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

        scheduler.trigger_report_now(config_id)

        # Verify report was generated
        with get_session() as session:
            history = session.query(ReportHistory).filter(
                ReportHistory.config_id == config_id
            ).first()

            assert history is not None
            assert history.success is True
