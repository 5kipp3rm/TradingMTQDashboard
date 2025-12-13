"""
Repository Pattern for TradingMTQ Database Operations

Uses Phase 0 patterns:
- Custom exceptions for database errors
- Structured logging with correlation IDs
- Type-safe operations with proper validation
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import Session

# Phase 0 imports
from src.exceptions import DatabaseError, DataNotAvailableError
from src.utils.structured_logger import StructuredLogger, CorrelationContext

from .models import Trade, Signal, AccountSnapshot, DailyPerformance, TradeStatus, SignalType
from .connection import get_session

logger = StructuredLogger(__name__)


class BaseRepository:
    """Base repository with common operations"""

    def __init__(self, model_class):
        self.model_class = model_class

    def _handle_db_error(self, operation: str, error: Exception):
        """Handle database errors with logging"""
        logger.error(
            "Database operation failed",
            operation=operation,
            model=self.model_class.__name__,
            error=str(error),
            exc_info=True
        )
        raise DatabaseError(
            f"Database {operation} failed: {error}",
            context={
                'operation': operation,
                'model': self.model_class.__name__
            }
        )


class TradeRepository(BaseRepository):
    """Repository for Trade operations"""

    def __init__(self):
        super().__init__(Trade)

    def create(self, session: Session, **kwargs) -> Trade:
        """
        Create new trade record

        Args:
            session: Database session
            **kwargs: Trade attributes

        Returns:
            Created Trade instance

        Raises:
            DatabaseError: If creation fails
        """
        with CorrelationContext():
            try:
                trade = Trade(**kwargs)
                session.add(trade)
                session.flush()  # Get ID without committing

                logger.info(
                    "Trade created",
                    trade_id=trade.id,
                    symbol=trade.symbol,
                    trade_type=trade.trade_type,
                    volume=float(trade.volume) if trade.volume else None
                )

                return trade

            except Exception as e:
                self._handle_db_error("create", e)

    def update_on_close(self, session: Session, ticket: int, exit_price: Decimal,
                       exit_time: datetime, profit: Decimal, pips: Optional[Decimal] = None) -> Optional[Trade]:
        """
        Update trade when position closes

        Args:
            session: Database session
            ticket: MT5 ticket number
            exit_price: Exit price
            exit_time: Exit timestamp
            profit: Realized profit
            pips: Profit in pips

        Returns:
            Updated Trade instance or None if not found
        """
        with CorrelationContext():
            try:
                trade = session.query(Trade).filter(Trade.ticket == ticket).first()

                if not trade:
                    logger.warning("Trade not found for update", ticket=ticket)
                    return None

                # Calculate duration
                if trade.entry_time:
                    duration = (exit_time - trade.entry_time).total_seconds()
                    trade.duration_seconds = int(duration)

                trade.exit_price = exit_price
                trade.exit_time = exit_time
                trade.profit = profit
                trade.pips = pips
                trade.status = TradeStatus.CLOSED
                trade.updated_at = datetime.utcnow()

                session.flush()

                logger.info(
                    "Trade closed",
                    trade_id=trade.id,
                    ticket=ticket,
                    profit=float(profit) if profit else None,
                    duration_seconds=trade.duration_seconds
                )

                return trade

            except Exception as e:
                self._handle_db_error("update_on_close", e)

    def get_by_ticket(self, session: Session, ticket: int) -> Optional[Trade]:
        """Get trade by MT5 ticket number"""
        try:
            return session.query(Trade).filter(Trade.ticket == ticket).first()
        except Exception as e:
            self._handle_db_error("get_by_ticket", e)

    def get_open_trades(self, session: Session, symbol: Optional[str] = None) -> List[Trade]:
        """
        Get all open trades

        Args:
            session: Database session
            symbol: Filter by symbol (optional)

        Returns:
            List of open Trade instances
        """
        try:
            query = session.query(Trade).filter(Trade.status == TradeStatus.OPEN)

            if symbol:
                query = query.filter(Trade.symbol == symbol)

            return query.all()

        except Exception as e:
            self._handle_db_error("get_open_trades", e)

    def get_trades_by_date_range(self, session: Session, start_date: datetime,
                                 end_date: datetime, symbol: Optional[str] = None) -> List[Trade]:
        """Get trades within date range"""
        try:
            query = session.query(Trade).filter(
                and_(
                    Trade.entry_time >= start_date,
                    Trade.entry_time <= end_date
                )
            )

            if symbol:
                query = query.filter(Trade.symbol == symbol)

            return query.order_by(Trade.entry_time).all()

        except Exception as e:
            self._handle_db_error("get_trades_by_date_range", e)

    def get_trade_statistics(self, session: Session,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get trade statistics

        Args:
            session: Database session
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            Dictionary with statistics
        """
        with CorrelationContext():
            try:
                query = session.query(Trade).filter(Trade.status == TradeStatus.CLOSED)

                if start_date:
                    query = query.filter(Trade.entry_time >= start_date)
                if end_date:
                    query = query.filter(Trade.entry_time <= end_date)

                trades = query.all()

                if not trades:
                    return {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'win_rate': 0.0,
                        'total_profit': 0.0,
                        'average_profit': 0.0,
                        'profit_factor': 0.0,
                    }

                total_trades = len(trades)
                winning_trades = sum(1 for t in trades if t.profit and t.profit > 0)
                losing_trades = sum(1 for t in trades if t.profit and t.profit < 0)

                total_profit = sum(float(t.profit) for t in trades if t.profit)
                gross_profit = sum(float(t.profit) for t in trades if t.profit and t.profit > 0)
                gross_loss = abs(sum(float(t.profit) for t in trades if t.profit and t.profit < 0))

                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                average_profit = total_profit / total_trades if total_trades > 0 else 0.0
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

                logger.info(
                    "Trade statistics calculated",
                    total_trades=total_trades,
                    win_rate=win_rate,
                    total_profit=total_profit
                )

                return {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': win_rate,
                    'total_profit': total_profit,
                    'average_profit': average_profit,
                    'profit_factor': profit_factor,
                    'gross_profit': gross_profit,
                    'gross_loss': gross_loss,
                }

            except Exception as e:
                self._handle_db_error("get_trade_statistics", e)


class SignalRepository(BaseRepository):
    """Repository for Signal operations"""

    def __init__(self):
        super().__init__(Signal)

    def create(self, session: Session, **kwargs) -> Signal:
        """Create new signal record"""
        with CorrelationContext():
            try:
                signal = Signal(**kwargs)
                session.add(signal)
                session.flush()

                logger.info(
                    "Signal created",
                    signal_id=signal.id,
                    symbol=signal.symbol,
                    signal_type=signal.signal_type,
                    confidence=signal.confidence
                )

                return signal

            except Exception as e:
                self._handle_db_error("create", e)

    def mark_executed(self, session: Session, signal_id: int, trade_id: int,
                     execution_reason: Optional[str] = None) -> Optional[Signal]:
        """Mark signal as executed and link to trade"""
        try:
            signal = session.query(Signal).filter(Signal.id == signal_id).first()

            if not signal:
                return None

            signal.executed = True
            signal.trade_id = trade_id
            signal.execution_reason = execution_reason

            session.flush()

            logger.info("Signal marked as executed", signal_id=signal_id, trade_id=trade_id)

            return signal

        except Exception as e:
            self._handle_db_error("mark_executed", e)

    def get_recent_signals(self, session: Session, symbol: Optional[str] = None,
                          limit: int = 100) -> List[Signal]:
        """Get recent signals"""
        try:
            query = session.query(Signal).order_by(desc(Signal.timestamp)).limit(limit)

            if symbol:
                query = query.filter(Signal.symbol == symbol)

            return query.all()

        except Exception as e:
            self._handle_db_error("get_recent_signals", e)

    def get_signal_execution_rate(self, session: Session,
                                  start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get signal execution statistics"""
        try:
            query = session.query(Signal)

            if start_date:
                query = query.filter(Signal.timestamp >= start_date)

            total_signals = query.count()
            executed_signals = query.filter(Signal.executed == True).count()

            execution_rate = (executed_signals / total_signals * 100) if total_signals > 0 else 0.0

            return {
                'total_signals': total_signals,
                'executed_signals': executed_signals,
                'execution_rate': execution_rate,
            }

        except Exception as e:
            self._handle_db_error("get_signal_execution_rate", e)


class AccountSnapshotRepository(BaseRepository):
    """Repository for AccountSnapshot operations"""

    def __init__(self):
        super().__init__(AccountSnapshot)

    def create(self, session: Session, **kwargs) -> AccountSnapshot:
        """Create new account snapshot"""
        with CorrelationContext():
            try:
                snapshot = AccountSnapshot(**kwargs)
                session.add(snapshot)
                session.flush()

                logger.info(
                    "Account snapshot created",
                    snapshot_id=snapshot.id,
                    account=snapshot.account_number,
                    balance=float(snapshot.balance) if snapshot.balance else None,
                    equity=float(snapshot.equity) if snapshot.equity else None
                )

                return snapshot

            except Exception as e:
                self._handle_db_error("create", e)

    def get_latest_snapshot(self, session: Session, account_number: int) -> Optional[AccountSnapshot]:
        """Get most recent snapshot for account"""
        try:
            return session.query(AccountSnapshot).filter(
                AccountSnapshot.account_number == account_number
            ).order_by(desc(AccountSnapshot.snapshot_time)).first()

        except Exception as e:
            self._handle_db_error("get_latest_snapshot", e)

    def get_snapshots_by_date_range(self, session: Session, account_number: int,
                                    start_date: datetime, end_date: datetime) -> List[AccountSnapshot]:
        """Get snapshots within date range"""
        try:
            return session.query(AccountSnapshot).filter(
                and_(
                    AccountSnapshot.account_number == account_number,
                    AccountSnapshot.snapshot_time >= start_date,
                    AccountSnapshot.snapshot_time <= end_date
                )
            ).order_by(AccountSnapshot.snapshot_time).all()

        except Exception as e:
            self._handle_db_error("get_snapshots_by_date_range", e)


class DailyPerformanceRepository(BaseRepository):
    """Repository for DailyPerformance operations"""

    def __init__(self):
        super().__init__(DailyPerformance)

    def create_or_update(self, session: Session, target_date: date, **kwargs) -> DailyPerformance:
        """Create or update daily performance record"""
        with CorrelationContext():
            try:
                # Convert date to datetime for the date field
                date_dt = datetime.combine(target_date, datetime.min.time())

                perf = session.query(DailyPerformance).filter(
                    DailyPerformance.date == date_dt
                ).first()

                if perf:
                    # Update existing
                    for key, value in kwargs.items():
                        setattr(perf, key, value)
                    perf.updated_at = datetime.utcnow()
                    logger.info("Daily performance updated", date=target_date)
                else:
                    # Create new
                    perf = DailyPerformance(date=date_dt, **kwargs)
                    session.add(perf)
                    logger.info("Daily performance created", date=target_date)

                session.flush()
                return perf

            except Exception as e:
                self._handle_db_error("create_or_update", e)

    def get_by_date(self, session: Session, target_date: date) -> Optional[DailyPerformance]:
        """Get performance for specific date"""
        try:
            date_dt = datetime.combine(target_date, datetime.min.time())
            return session.query(DailyPerformance).filter(
                DailyPerformance.date == date_dt
            ).first()

        except Exception as e:
            self._handle_db_error("get_by_date", e)

    def get_performance_summary(self, session: Session,
                               start_date: Optional[date] = None,
                               end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get aggregated performance summary"""
        try:
            query = session.query(DailyPerformance)

            if start_date:
                query = query.filter(DailyPerformance.date >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                query = query.filter(DailyPerformance.date <= datetime.combine(end_date, datetime.min.time()))

            performances = query.all()

            if not performances:
                return {}

            total_trades = sum(p.total_trades for p in performances)
            total_profit = sum(float(p.net_profit) for p in performances if p.net_profit)
            winning_days = sum(1 for p in performances if p.net_profit and p.net_profit > 0)

            return {
                'total_days': len(performances),
                'winning_days': winning_days,
                'losing_days': len(performances) - winning_days,
                'total_trades': total_trades,
                'total_profit': total_profit,
                'average_daily_profit': total_profit / len(performances) if performances else 0.0,
            }

        except Exception as e:
            self._handle_db_error("get_performance_summary", e)
