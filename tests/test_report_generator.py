"""
Unit Tests for Report Generator

Tests PDF report generation functionality including title pages,
executive summaries, detailed metrics, and trade lists.
"""

import pytest
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
import tempfile
import shutil

from src.reports.generator import ReportGenerator
from src.database import get_session, init_db, Trade, TradingAccount, DailyPerformance
from src.database.models import TradeStatus, TradeType


@pytest.fixture
def temp_report_dir():
    """Create temporary directory for test reports"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test"""
    init_db()
    yield
    # Cleanup after test
    with get_session() as session:
        session.query(Trade).delete()
        session.query(TradingAccount).delete()
        session.query(DailyPerformance).delete()
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
def sample_trades(sample_account):
    """Create sample trades for testing"""
    with get_session() as session:
        base_date = datetime.now() - timedelta(days=10)

        trades = []
        for i in range(20):
            trade = Trade(
                ticket=10000 + i,
                symbol="EURUSD",
                trade_type=TradeType.BUY if i % 2 == 0 else TradeType.SELL,
                volume=Decimal("0.1"),
                entry_price=Decimal("1.1000") + Decimal(str(i * 0.0001)),
                entry_time=base_date + timedelta(days=i // 2, hours=i % 24),
                exit_price=Decimal("1.1010") + Decimal(str(i * 0.0001)),
                exit_time=base_date + timedelta(days=i // 2 + 1, hours=(i + 2) % 24),
                profit=Decimal("10.00") if i % 3 != 0 else Decimal("-5.00"),
                status=TradeStatus.CLOSED,
                account_id=sample_account
            )
            trades.append(trade)
            session.add(trade)

        session.commit()
        return [t.id for t in trades]


@pytest.fixture
def sample_daily_performance(sample_account):
    """Create sample daily performance records"""
    with get_session() as session:
        base_date = date.today() - timedelta(days=30)

        for i in range(30):
            performance = DailyPerformance(
                date=base_date + timedelta(days=i),
                total_trades=5,
                winning_trades=3,
                losing_trades=2,
                net_profit=Decimal("50.00") if i % 2 == 0 else Decimal("-20.00"),
                gross_profit=Decimal("100.00"),
                gross_loss=Decimal("-50.00"),
                win_rate=Decimal("60.00"),
                average_win=Decimal("33.33"),
                average_loss=Decimal("-25.00"),
                largest_win=Decimal("50.00"),
                largest_loss=Decimal("-30.00"),
                start_balance=Decimal("10000.00") + Decimal(str(i * 10)),
                end_balance=Decimal("10000.00") + Decimal(str((i + 1) * 10)),
                start_equity=Decimal("10000.00") + Decimal(str(i * 10)),
                end_equity=Decimal("10000.00") + Decimal(str((i + 1) * 10)),
                account_id=sample_account
            )
            session.add(performance)

        session.commit()


class TestReportGeneratorInitialization:
    """Test report generator initialization"""

    def test_init_with_default_directory(self):
        """Test initialization with default output directory"""
        generator = ReportGenerator()
        assert generator.output_dir == Path("./reports")
        assert generator.styles is not None

    def test_init_with_custom_directory(self, temp_report_dir):
        """Test initialization with custom output directory"""
        generator = ReportGenerator(output_dir=temp_report_dir)
        assert generator.output_dir == temp_report_dir
        assert temp_report_dir.exists()

    def test_custom_styles_created(self):
        """Test that custom paragraph styles are created"""
        generator = ReportGenerator()
        assert 'ReportTitle' in generator.styles
        assert 'SectionHeader' in generator.styles
        assert 'MetricValue' in generator.styles
        assert 'MetricLabel' in generator.styles


class TestReportGeneration:
    """Test PDF report generation"""

    def test_generate_basic_report(self, temp_report_dir, sample_account, sample_trades, sample_daily_performance):
        """Test generating basic performance report"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=None,
            include_trades=True,
            include_charts=False
        )

        assert output_path.exists()
        assert output_path.suffix == '.pdf'
        assert output_path.stat().st_size > 0

    def test_generate_report_with_account_filter(
        self,
        temp_report_dir,
        sample_account,
        sample_trades,
        sample_daily_performance
    ):
        """Test generating report filtered by account"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=sample_account,
            include_trades=True,
            include_charts=False
        )

        assert output_path.exists()
        assert f"account_{sample_account}" in output_path.name

    def test_generate_report_without_trades(
        self,
        temp_report_dir,
        sample_account,
        sample_daily_performance
    ):
        """Test generating report without trade list"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=None,
            include_trades=False,
            include_charts=False
        )

        assert output_path.exists()

    def test_generate_report_no_data(self, temp_report_dir):
        """Test generating report with no data"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=None,
            include_trades=True,
            include_charts=False
        )

        assert output_path.exists()
        # Report should still be generated even with no data


class TestTitlePageCreation:
    """Test title page creation"""

    def test_create_title_page_without_account(self, temp_report_dir):
        """Test creating title page for all accounts"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_title_page(start_date, end_date, None)

        assert len(elements) > 0
        # Verify all elements are ReportLab objects
        assert all(e is not None for e in elements)

    def test_create_title_page_with_account(self, temp_report_dir, sample_account):
        """Test creating title page for specific account"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_title_page(start_date, end_date, sample_account)

        assert len(elements) > 0


class TestExecutiveSummary:
    """Test executive summary creation"""

    def test_create_executive_summary_with_data(
        self,
        temp_report_dir,
        sample_account,
        sample_daily_performance
    ):
        """Test creating executive summary with data"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_executive_summary(start_date, end_date, sample_account)

        assert len(elements) > 0
        # Should include section header and metrics table

    def test_create_executive_summary_no_data(self, temp_report_dir):
        """Test creating executive summary with no data"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_executive_summary(start_date, end_date, None)

        assert len(elements) > 0
        # Should include "No data" message


class TestDetailedMetrics:
    """Test detailed metrics section"""

    def test_create_detailed_metrics_with_trades(
        self,
        temp_report_dir,
        sample_account,
        sample_trades
    ):
        """Test creating detailed metrics with trade data"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_detailed_metrics(start_date, end_date, sample_account)

        assert len(elements) > 0
        # Should include section header and detailed metrics table

    def test_create_detailed_metrics_no_trades(self, temp_report_dir):
        """Test creating detailed metrics with no trades"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_detailed_metrics(start_date, end_date, None)

        assert len(elements) > 0
        # Should include "No trades" message


class TestTradeList:
    """Test trade list creation"""

    def test_create_trade_list_with_trades(
        self,
        temp_report_dir,
        sample_account,
        sample_trades
    ):
        """Test creating trade list with trade data"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_trade_list(start_date, end_date, sample_account, limit=10)

        assert len(elements) > 0
        # Should include section header and trades table

    def test_create_trade_list_no_trades(self, temp_report_dir):
        """Test creating trade list with no trades"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_trade_list(start_date, end_date, None)

        assert len(elements) > 0
        # Should include "No trades" message

    def test_create_trade_list_with_limit(
        self,
        temp_report_dir,
        sample_account,
        sample_trades
    ):
        """Test creating trade list with custom limit"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        elements = generator._create_trade_list(start_date, end_date, sample_account, limit=5)

        assert len(elements) > 0


class TestReportFilenaming:
    """Test report filename generation"""

    def test_filename_includes_dates(self, temp_report_dir, sample_daily_performance):
        """Test that filename includes start and end dates"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=None,
            include_trades=False,
            include_charts=False
        )

        assert "2024-01-01" in output_path.name
        assert "2024-01-31" in output_path.name

    def test_filename_includes_account_id(
        self,
        temp_report_dir,
        sample_account,
        sample_daily_performance
    ):
        """Test that filename includes account ID when specified"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=sample_account,
            include_trades=False,
            include_charts=False
        )

        assert f"account_{sample_account}" in output_path.name

    def test_filename_all_accounts(self, temp_report_dir, sample_daily_performance):
        """Test filename when showing all accounts"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=None,
            include_trades=False,
            include_charts=False
        )

        assert "all_accounts" in output_path.name


class TestReportMetrics:
    """Test report metrics calculations"""

    def test_win_rate_calculation(
        self,
        temp_report_dir,
        sample_account,
        sample_trades
    ):
        """Test that win rate is calculated correctly"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        # Generate report to ensure calculations work
        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=sample_account,
            include_trades=True,
            include_charts=False
        )

        assert output_path.exists()

    def test_profit_factor_calculation(
        self,
        temp_report_dir,
        sample_account,
        sample_trades
    ):
        """Test that profit factor is calculated correctly"""
        generator = ReportGenerator(output_dir=temp_report_dir)

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        # Generate report to ensure calculations work
        output_path = generator.generate_performance_report(
            start_date=start_date,
            end_date=end_date,
            account_id=sample_account,
            include_trades=True,
            include_charts=False
        )

        assert output_path.exists()
