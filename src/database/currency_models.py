"""
Currency Configuration Database Models

Stores currency pair trading configurations with support for:
- Per-currency trading settings
- Strategy parameters
- Risk management settings
- Position management rules
- Configuration versioning
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
import enum

from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base


class StrategyType(enum.Enum):
    """Trading strategy types"""
    CROSSOVER = "crossover"  # MA crossover strategy
    POSITION = "position"     # MA position strategy (faster signals)


class Timeframe(enum.Enum):
    """Trading timeframes"""
    M1 = "M1"      # 1 minute
    M5 = "M5"      # 5 minutes
    M15 = "M15"    # 15 minutes
    M30 = "M30"    # 30 minutes
    H1 = "H1"      # 1 hour
    H4 = "H4"      # 4 hours
    D1 = "D1"      # 1 day
    W1 = "W1"      # 1 week


class CurrencyConfiguration(Base):
    """
    Currency Pair Trading Configuration

    Stores all trading parameters for a specific currency pair including:
    - Risk management settings
    - Strategy parameters
    - Technical indicator settings
    - Stop Loss / Take Profit
    - Position management rules

    This model supports both database persistence and YAML export/import.
    """
    __tablename__ = 'currency_configurations'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Symbol Identification
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ========================================================================
    # RISK MANAGEMENT
    # ========================================================================

    # Risk per trade (percentage of account balance)
    risk_percent: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Position size limits (in lots)
    max_position_size: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    min_position_size: Mapped[float] = mapped_column(Float, nullable=False, default=0.01)

    # ========================================================================
    # STRATEGY SETTINGS
    # ========================================================================

    # Strategy type: 'crossover' (slower, waits for MA cross) or 'position' (faster, trades on MA position)
    strategy_type: Mapped[str] = mapped_column(String(20), nullable=False, default="position")

    # Trading timeframe: M1, M5, M15, M30, H1, H4, D1, W1
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, default="M15")

    # ========================================================================
    # TECHNICAL INDICATORS
    # ========================================================================

    # Moving Average periods
    fast_period: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    slow_period: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    # ========================================================================
    # STOP LOSS / TAKE PROFIT
    # ========================================================================

    # Stop Loss in pips
    sl_pips: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    # Take Profit in pips
    tp_pips: Mapped[int] = mapped_column(Integer, nullable=False, default=40)

    # ========================================================================
    # TRADING RULES
    # ========================================================================

    # Cooldown period between trades (seconds)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    # Whether to require signal change before re-entry
    trade_on_signal_change: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ========================================================================
    # POSITION STACKING (Multiple positions in same direction)
    # ========================================================================

    # Allow multiple positions in the same direction
    allow_position_stacking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Maximum positions in same direction
    max_positions_same_direction: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Maximum total positions for this symbol
    max_total_positions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Risk multiplier for additional positions (e.g., 0.5 = half size for 2nd position)
    stacking_risk_multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # ========================================================================
    # TRADING HOURS (Optional)
    # ========================================================================

    # Trading hours start (HH:MM format in UTC, NULL = trade 24/7)
    trading_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    # Trading hours end (HH:MM format in UTC, NULL = trade 24/7)
    trading_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    # ========================================================================
    # ADDITIONAL SETTINGS (JSON for extensibility)
    # ========================================================================

    # Additional settings as JSON (for future extensions without schema changes)
    additional_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ========================================================================
    # METADATA
    # ========================================================================

    # Configuration description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Configuration version (incremented on each update for change tracking)
    config_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # ========================================================================
    # AUDIT TRAIL
    # ========================================================================

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Last time this configuration was loaded/activated
    last_loaded: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (f"<CurrencyConfiguration(id={self.id}, symbol='{self.symbol}', "
                f"enabled={self.enabled}, strategy='{self.strategy_type}', "
                f"timeframe='{self.timeframe}', version={self.config_version})>")

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses and YAML export

        Returns:
            dict: All configuration fields as a dictionary
        """
        return {
            'id': self.id,
            'symbol': self.symbol,
            'enabled': self.enabled,

            # Risk Management
            'risk_percent': self.risk_percent,
            'max_position_size': self.max_position_size,
            'min_position_size': self.min_position_size,

            # Strategy
            'strategy_type': self.strategy_type,
            'timeframe': self.timeframe,

            # Indicators
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,

            # SL/TP
            'sl_pips': self.sl_pips,
            'tp_pips': self.tp_pips,

            # Trading Rules
            'cooldown_seconds': self.cooldown_seconds,
            'trade_on_signal_change': self.trade_on_signal_change,

            # Position Stacking
            'allow_position_stacking': self.allow_position_stacking,
            'max_positions_same_direction': self.max_positions_same_direction,
            'max_total_positions': self.max_total_positions,
            'stacking_risk_multiplier': self.stacking_risk_multiplier,

            # Trading Hours
            'trading_hours_start': self.trading_hours_start,
            'trading_hours_end': self.trading_hours_end,

            # Additional
            'additional_settings': self.additional_settings,
            'description': self.description,
            'config_version': self.config_version,

            # Audit
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_loaded': self.last_loaded.isoformat() if self.last_loaded else None,
        }

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate currency configuration

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []

        # Symbol validation
        if not self.symbol or len(self.symbol) < 6:
            errors.append("Symbol must be at least 6 characters (e.g., EURUSD)")

        # Risk validation
        if not (0.1 <= self.risk_percent <= 10.0):
            errors.append("Risk percent must be between 0.1 and 10.0")

        if self.max_position_size <= 0:
            errors.append("Max position size must be greater than 0")

        if self.min_position_size <= 0:
            errors.append("Min position size must be greater than 0")

        if self.min_position_size > self.max_position_size:
            errors.append("Min position size cannot be greater than max position size")

        # Strategy validation
        if self.strategy_type not in ['crossover', 'position']:
            errors.append("Strategy type must be 'crossover' or 'position'")

        if self.timeframe not in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']:
            errors.append("Invalid timeframe")

        # Indicator validation
        if self.fast_period <= 0:
            errors.append("Fast period must be greater than 0")

        if self.slow_period <= 0:
            errors.append("Slow period must be greater than 0")

        if self.fast_period >= self.slow_period:
            errors.append("Fast period must be less than slow period")

        # SL/TP validation
        if self.sl_pips <= 0:
            errors.append("Stop Loss pips must be greater than 0")

        if self.tp_pips <= 0:
            errors.append("Take Profit pips must be greater than 0")

        # Typically TP should be larger than SL (risk:reward ratio)
        # But we'll just warn, not error
        if self.tp_pips < self.sl_pips:
            errors.append("Warning: Take Profit should typically be larger than Stop Loss")

        # Trading rules validation
        if self.cooldown_seconds < 0:
            errors.append("Cooldown seconds cannot be negative")

        # Position stacking validation
        if self.max_positions_same_direction <= 0:
            errors.append("Max positions same direction must be greater than 0")

        if self.max_total_positions <= 0:
            errors.append("Max total positions must be greater than 0")

        if self.stacking_risk_multiplier <= 0:
            errors.append("Stacking risk multiplier must be greater than 0")

        # Trading hours validation
        if self.trading_hours_start and not self._is_valid_time_format(self.trading_hours_start):
            errors.append("Trading hours start must be in HH:MM format")

        if self.trading_hours_end and not self._is_valid_time_format(self.trading_hours_end):
            errors.append("Trading hours end must be in HH:MM format")

        return (len(errors) == 0, errors)

    def _is_valid_time_format(self, time_str: str) -> bool:
        """Check if time string is in HH:MM format"""
        if not time_str or len(time_str) != 5:
            return False

        try:
            hours, minutes = time_str.split(':')
            h = int(hours)
            m = int(minutes)
            return 0 <= h <= 23 and 0 <= m <= 59
        except (ValueError, AttributeError):
            return False
