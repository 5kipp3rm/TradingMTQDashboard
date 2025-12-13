"""
SQLAlchemy Database Models for TradingMTQ

Uses Phase 0 patterns:
- Type-safe models with proper validation
- Timestamps for audit trails
- Relationships for data integrity
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, Enum as SQLEnum, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class TradeStatus(enum.Enum):
    """Trade execution status"""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class SignalType(enum.Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Trade(Base):
    """
    Trade execution record

    Stores complete trade lifecycle from signal to closure
    """
    __tablename__ = 'trades'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Trade Identification
    ticket: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    magic_number: Mapped[int] = mapped_column(Integer, default=0)

    # Trade Type and Direction
    trade_type: Mapped[str] = mapped_column(SQLEnum(SignalType), nullable=False)
    status: Mapped[str] = mapped_column(SQLEnum(TradeStatus), default=TradeStatus.PENDING, nullable=False, index=True)

    # Entry Information
    entry_price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=5), nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    volume: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)

    # Risk Management
    stop_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=5), nullable=True)
    take_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=5), nullable=True)

    # Exit Information
    exit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=5), nullable=True)
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # P&L
    profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=2), nullable=True)
    commission: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=2), default=0.0)
    swap: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=2), default=0.0)

    # Performance Metrics
    pips: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=1), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Strategy Information
    strategy_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    signal_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    signal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ML/AI Features
    ml_enhanced: Mapped[bool] = mapped_column(Boolean, default=False)
    ml_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    signal: Mapped[Optional["Signal"]] = relationship("Signal", back_populates="trade", uselist=False)

    def __repr__(self) -> str:
        return (f"<Trade(id={self.id}, ticket={self.ticket}, symbol={self.symbol}, "
                f"type={self.trade_type}, status={self.status}, "
                f"profit={self.profit})>")

    def to_dict(self) -> dict:
        """Convert trade to dictionary"""
        return {
            'id': self.id,
            'ticket': self.ticket,
            'symbol': self.symbol,
            'trade_type': self.trade_type.value if isinstance(self.trade_type, enum.Enum) else self.trade_type,
            'status': self.status.value if isinstance(self.status, enum.Enum) else self.status,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'volume': float(self.volume) if self.volume else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'exit_price': float(self.exit_price) if self.exit_price else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'profit': float(self.profit) if self.profit else None,
            'commission': float(self.commission) if self.commission else None,
            'swap': float(self.swap) if self.swap else None,
            'pips': float(self.pips) if self.pips else None,
            'duration_seconds': self.duration_seconds,
            'strategy_name': self.strategy_name,
            'signal_confidence': self.signal_confidence,
            'ml_enhanced': self.ml_enhanced,
            'ai_approved': self.ai_approved,
        }


class Signal(Base):
    """
    Trading signal record

    Stores all generated signals (executed or not)
    """
    __tablename__ = 'signals'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Signal Identification
    symbol: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(SQLEnum(SignalType), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # Signal Details
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=5), nullable=False)
    stop_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=5), nullable=True)
    take_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=5), nullable=True)

    # Signal Quality
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Strategy Information
    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)

    # ML/AI Enhancement
    ml_enhanced: Mapped[bool] = mapped_column(Boolean, default=False)
    ml_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ml_agreed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Execution Status
    executed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    execution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trade_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('trades.id'), nullable=True)

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    trade: Mapped[Optional["Trade"]] = relationship("Trade", back_populates="signal")

    def __repr__(self) -> str:
        return (f"<Signal(id={self.id}, symbol={self.symbol}, type={self.signal_type}, "
                f"confidence={self.confidence:.2f}, executed={self.executed})>")

    def to_dict(self) -> dict:
        """Convert signal to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'signal_type': self.signal_type.value if isinstance(self.signal_type, enum.Enum) else self.signal_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'price': float(self.price) if self.price else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'confidence': self.confidence,
            'reason': self.reason,
            'strategy_name': self.strategy_name,
            'timeframe': self.timeframe,
            'ml_enhanced': self.ml_enhanced,
            'executed': self.executed,
            'trade_id': self.trade_id,
        }


class AccountSnapshot(Base):
    """
    Account state snapshot

    Periodic snapshots of account balance and equity for tracking
    """
    __tablename__ = 'account_snapshots'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Account Information
    account_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    server: Mapped[str] = mapped_column(String(50), nullable=False)
    broker: Mapped[str] = mapped_column(String(50), nullable=False)

    # Balance and Equity
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    profit: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0.0)

    # Margin
    margin: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0.0)
    margin_free: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0.0)
    margin_level: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=2), nullable=True)

    # Open Positions
    open_positions: Mapped[int] = mapped_column(Integer, default=0)
    total_volume: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), default=0.0)

    # Timestamp
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (f"<AccountSnapshot(id={self.id}, account={self.account_number}, "
                f"balance={self.balance}, equity={self.equity}, "
                f"time={self.snapshot_time})>")

    def to_dict(self) -> dict:
        """Convert snapshot to dictionary"""
        return {
            'id': self.id,
            'account_number': self.account_number,
            'server': self.server,
            'broker': self.broker,
            'balance': float(self.balance) if self.balance else None,
            'equity': float(self.equity) if self.equity else None,
            'profit': float(self.profit) if self.profit else None,
            'margin': float(self.margin) if self.margin else None,
            'margin_free': float(self.margin_free) if self.margin_free else None,
            'margin_level': float(self.margin_level) if self.margin_level else None,
            'open_positions': self.open_positions,
            'total_volume': float(self.total_volume) if self.total_volume else None,
            'snapshot_time': self.snapshot_time.isoformat() if self.snapshot_time else None,
        }


class DailyPerformance(Base):
    """
    Daily performance summary

    Aggregated daily statistics for performance tracking
    """
    __tablename__ = 'daily_performance'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Date
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, unique=True, index=True)

    # Trade Counts
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0)

    # P&L
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0.0)
    gross_loss: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0.0)
    net_profit: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0.0)

    # Performance Metrics
    win_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=5, scale=2), nullable=True)
    profit_factor: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=2), nullable=True)
    average_win: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True)
    average_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True)
    largest_win: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True)
    largest_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True)

    # Account Snapshot at End of Day
    end_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True)
    end_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2), nullable=True)

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (f"<DailyPerformance(date={self.date.date()}, trades={self.total_trades}, "
                f"net_profit={self.net_profit}, win_rate={self.win_rate})>")

    def to_dict(self) -> dict:
        """Convert performance to dictionary"""
        return {
            'id': self.id,
            'date': self.date.date().isoformat() if self.date else None,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'gross_profit': float(self.gross_profit) if self.gross_profit else None,
            'gross_loss': float(self.gross_loss) if self.gross_loss else None,
            'net_profit': float(self.net_profit) if self.net_profit else None,
            'win_rate': float(self.win_rate) if self.win_rate else None,
            'profit_factor': float(self.profit_factor) if self.profit_factor else None,
            'average_win': float(self.average_win) if self.average_win else None,
            'average_loss': float(self.average_loss) if self.average_loss else None,
            'end_balance': float(self.end_balance) if self.end_balance else None,
            'end_equity': float(self.end_equity) if self.end_equity else None,
        }
