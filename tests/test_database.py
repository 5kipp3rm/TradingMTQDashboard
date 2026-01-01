#!/usr/bin/env python3
"""
Test Database Integration for TradingMTQ

Tests Phase 5.1 database integration:
- Database initialization
- Model creation
- Repository operations
- Connection management
"""
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Phase 0 imports
from src.utils.structured_logger import StructuredLogger, CorrelationContext
from src.exceptions import DatabaseError

# Database imports
from src.database.connection import init_db, get_session, check_database_health
from src.database.repository import (
    TradeRepository, SignalRepository,
    AccountSnapshotRepository, DailyPerformanceRepository
)
from src.database.models import TradeStatus, SignalType as DBSignalType

logger = StructuredLogger(__name__)


def test_database_initialization():
    """Test 1: Database initialization"""
    print("\n" + "=" * 80)
    print("TEST 1: Database Initialization")
    print("=" * 80)

    try:
        # Initialize with SQLite for testing
        engine = init_db("sqlite:///./test_tradingmtq.db", echo=False)
        print("✅ Database initialized successfully")
        print(f"   Engine: {engine}")

        # Check health
        if check_database_health():
            print("✅ Database health check passed")
        else:
            print("❌ Database health check failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def test_trade_repository():
    """Test 2: Trade Repository operations"""
    print("\n" + "=" * 80)
    print("TEST 2: Trade Repository Operations")
    print("=" * 80)

    repo = TradeRepository()

    try:
        with get_session() as session:
            # Create a trade
            trade = repo.create(
                session,
                ticket=123456,
                symbol="EURUSD",
                magic_number=0,
                trade_type="BUY",  # Uppercase enum value
                status="OPEN",  # Uppercase enum value
                entry_price=Decimal("1.0850"),
                entry_time=datetime.now(),
                volume=Decimal("0.1"),
                stop_loss=Decimal("1.0830"),
                take_profit=Decimal("1.0900"),
                strategy_name="TestStrategy",
                signal_confidence=0.85,
                signal_reason="Test trade",
                ml_enhanced=True,
                ml_confidence=0.90,
                ai_approved=True,
                ai_reasoning="High confidence signal"
            )

            print(f"✅ Trade created: ID={trade.id}, Ticket={trade.ticket}")
            print(f"   Symbol: {trade.symbol}, Type: {trade.trade_type}, Status: {trade.status}")

            # Get trade by ticket
            retrieved = repo.get_by_ticket(session, 123456)
            if retrieved:
                print(f"✅ Trade retrieved by ticket: {retrieved.id}")
            else:
                print("❌ Failed to retrieve trade by ticket")
                return False

            # Update on close
            updated = repo.update_on_close(
                session,
                ticket=123456,
                exit_price=Decimal("1.0900"),
                exit_time=datetime.now(),
                profit=Decimal("50.00"),
                pips=Decimal("50.0")
            )

            if updated:
                print(f"✅ Trade closed: Profit=${updated.profit}, Pips={updated.pips}")
                print(f"   Duration: {updated.duration_seconds}s")
            else:
                print("❌ Failed to close trade")
                return False

            # Get open trades (should be 0 now)
            open_trades = repo.get_open_trades(session)
            print(f"✅ Open trades count: {len(open_trades)}")

            # Get trade statistics
            stats = repo.get_trade_statistics(session)
            print(f"✅ Trade Statistics:")
            print(f"   Total Trades: {stats['total_trades']}")
            print(f"   Winning Trades: {stats['winning_trades']}")
            print(f"   Win Rate: {stats['win_rate']:.2f}%")
            print(f"   Total Profit: ${stats['total_profit']:.2f}")
            print(f"   Profit Factor: {stats['profit_factor']:.2f}")

            return True

    except Exception as e:
        print(f"❌ Trade repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_repository():
    """Test 3: Signal Repository operations"""
    print("\n" + "=" * 80)
    print("TEST 3: Signal Repository Operations")
    print("=" * 80)

    repo = SignalRepository()

    try:
        with get_session() as session:
            # Create a signal
            signal = repo.create(
                session,
                symbol="EURUSD",
                signal_type="BUY",  # Uppercase enum value
                timestamp=datetime.now(),
                price=Decimal("1.0850"),
                stop_loss=Decimal("1.0830"),
                take_profit=Decimal("1.0900"),
                confidence=0.85,
                reason="MA crossover",
                strategy_name="MovingAverageCrossover",
                timeframe="M5",
                ml_enhanced=True,
                ml_confidence=0.90,
                ml_agreed=True,
                executed=False
            )

            print(f"✅ Signal created: ID={signal.id}")
            print(f"   Symbol: {signal.symbol}, Type: {signal.signal_type}")
            print(f"   Confidence: {signal.confidence:.2f}, ML: {signal.ml_confidence:.2f}")

            # Mark as executed
            executed = repo.mark_executed(
                session,
                signal_id=signal.id,
                trade_id=1,  # From previous test
                execution_reason="High confidence signal"
            )

            if executed and executed.executed:
                print(f"✅ Signal marked as executed, linked to trade {executed.trade_id}")
            else:
                print("❌ Failed to mark signal as executed")
                return False

            # Get recent signals
            recent = repo.get_recent_signals(session, symbol="EURUSD", limit=10)
            print(f"✅ Recent signals: {len(recent)}")

            # Get execution rate
            exec_rate = repo.get_signal_execution_rate(session)
            print(f"✅ Signal Execution Rate:")
            print(f"   Total Signals: {exec_rate['total_signals']}")
            print(f"   Executed: {exec_rate['executed_signals']}")
            print(f"   Execution Rate: {exec_rate['execution_rate']:.2f}%")

            return True

    except Exception as e:
        print(f"❌ Signal repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_account_snapshot_repository():
    """Test 4: Account Snapshot Repository operations"""
    print("\n" + "=" * 80)
    print("TEST 4: Account Snapshot Repository Operations")
    print("=" * 80)

    repo = AccountSnapshotRepository()

    try:
        with get_session() as session:
            # Create snapshot
            snapshot = repo.create(
                session,
                account_number=12345,
                server="TestServer",
                broker="TestBroker",
                balance=Decimal("10000.00"),
                equity=Decimal("10050.00"),
                profit=Decimal("50.00"),
                margin=Decimal("100.00"),
                margin_free=Decimal("9900.00"),
                margin_level=Decimal("10050.00"),
                open_positions=1,
                total_volume=Decimal("0.1"),
                snapshot_time=datetime.now()
            )

            print(f"✅ Snapshot created: ID={snapshot.id}")
            print(f"   Account: {snapshot.account_number}")
            print(f"   Balance: ${snapshot.balance}, Equity: ${snapshot.equity}")
            print(f"   Open Positions: {snapshot.open_positions}")

            # Get latest snapshot
            latest = repo.get_latest_snapshot(session, 12345)
            if latest:
                print(f"✅ Latest snapshot retrieved: ID={latest.id}")
            else:
                print("❌ Failed to retrieve latest snapshot")
                return False

            # Get snapshots by date range
            start_date = datetime.now() - timedelta(days=1)
            end_date = datetime.now() + timedelta(days=1)
            snapshots = repo.get_snapshots_by_date_range(
                session, 12345, start_date, end_date
            )
            print(f"✅ Snapshots in date range: {len(snapshots)}")

            return True

    except Exception as e:
        print(f"❌ Account snapshot repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_daily_performance_repository():
    """Test 5: Daily Performance Repository operations"""
    print("\n" + "=" * 80)
    print("TEST 5: Daily Performance Repository Operations")
    print("=" * 80)

    repo = DailyPerformanceRepository()

    try:
        from datetime import date
        with get_session() as session:
            # Create or update daily performance
            today = date.today()
            perf = repo.create_or_update(
                session,
                target_date=today,
                total_trades=10,
                winning_trades=7,
                losing_trades=3,
                gross_profit=Decimal("500.00"),
                gross_loss=Decimal("150.00"),
                net_profit=Decimal("350.00"),
                win_rate=Decimal("70.00"),
                profit_factor=Decimal("3.33"),
                average_win=Decimal("71.43"),
                average_loss=Decimal("50.00"),
                largest_win=Decimal("120.00"),
                largest_loss=Decimal("80.00"),
                end_balance=Decimal("10350.00"),
                end_equity=Decimal("10350.00")
            )

            print(f"✅ Daily performance created: ID={perf.id}")
            print(f"   Date: {perf.date.date()}")
            print(f"   Total Trades: {perf.total_trades}")
            print(f"   Win Rate: {perf.win_rate}%")
            print(f"   Net Profit: ${perf.net_profit}")
            print(f"   Profit Factor: {perf.profit_factor}")

            # Get by date
            retrieved = repo.get_by_date(session, today)
            if retrieved:
                print(f"✅ Performance retrieved by date: {retrieved.id}")
            else:
                print("❌ Failed to retrieve performance by date")
                return False

            # Get performance summary
            summary = repo.get_performance_summary(session)
            print(f"✅ Performance Summary:")
            print(f"   Total Days: {summary['total_days']}")
            print(f"   Winning Days: {summary['winning_days']}")
            print(f"   Total Trades: {summary['total_trades']}")
            print(f"   Total Profit: ${summary['total_profit']:.2f}")

            return True

    except Exception as e:
        print(f"❌ Daily performance repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all database tests"""
    print("\n" + "=" * 80)
    print("🚀 TRADINGMTQ DATABASE INTEGRATION TESTS - PHASE 5.1")
    print("=" * 80)

    results = []

    # Test 1: Initialization
    results.append(("Database Initialization", test_database_initialization()))

    # Test 2: Trade Repository
    results.append(("Trade Repository", test_trade_repository()))

    # Test 3: Signal Repository
    results.append(("Signal Repository", test_signal_repository()))

    # Test 4: Account Snapshot Repository
    results.append(("Account Snapshot Repository", test_account_snapshot_repository()))

    # Test 5: Daily Performance Repository
    results.append(("Daily Performance Repository", test_daily_performance_repository()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 80)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 80)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Phase 5.1 database integration is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
