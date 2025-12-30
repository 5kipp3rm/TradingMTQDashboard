"""
Account-Specific Currency Configuration Models

Per-account currency overrides with foreign key relationships.
Allows each trading account to have custom currency settings while
falling back to global defaults for unspecified fields.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models import Base


class AccountCurrencyConfig(Base):
    """
    Per-Account Currency Configuration Overrides

    Links accounts to currencies with account-specific settings.
    Creates a many-to-many relationship with override capabilities.
    NULL fields fall back to global CurrencyConfiguration defaults.

    Example Flow:
    1. Account 1 wants to trade EURUSD with custom risk
    2. Creates entry: (account_id=1, currency_symbol='EURUSD', risk_percent=2.0)
    3. System uses 2.0% risk for Account 1, but global defaults for other fields
    4. Account 2 uses EURUSD with global settings (no override entry)
    """
    __tablename__ = 'account_currency_configs'

    # ========================================================================
    # PRIMARY KEY & FOREIGN KEYS
    # ========================================================================

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key: Trading Account
    account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('trading_accounts.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Foreign Key: Currency Symbol (references global currency config)
    currency_symbol: Mapped[str] = mapped_column(
        String(20),
        ForeignKey('currency_configurations.symbol', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Unique constraint: one config per account-currency pair
    __table_args__ = (
        UniqueConstraint('account_id', 'currency_symbol', name='uq_account_currency'),
    )

    # ========================================================================
    # STATUS
    # ========================================================================

    # Whether this currency is enabled for this account
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Soft delete flag (for currencies with trade history)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ========================================================================
    # RISK MANAGEMENT OVERRIDES (NULL = use global default)
    # ========================================================================

    risk_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_position_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_position_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ========================================================================
    # STRATEGY OVERRIDES (NULL = use global default)
    # ========================================================================

    strategy_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timeframe: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # ========================================================================
    # TECHNICAL INDICATORS OVERRIDES (NULL = use global default)
    # ========================================================================

    fast_period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    slow_period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ========================================================================
    # STOP LOSS / TAKE PROFIT OVERRIDES (NULL = use global default)
    # ========================================================================

    sl_pips: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tp_pips: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ========================================================================
    # TRADING RULES OVERRIDES (NULL = use global default)
    # ========================================================================

    cooldown_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trade_on_signal_change: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ========================================================================
    # POSITION STACKING OVERRIDES (NULL = use global default)
    # ========================================================================

    allow_position_stacking: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    max_positions_same_direction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_total_positions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stacking_risk_multiplier: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ========================================================================
    # AUDIT TRAIL
    # ========================================================================

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================

    # Relationship to trading account
    account: Mapped["TradingAccount"] = relationship("TradingAccount", back_populates="currency_configs")

    # Relationship to global currency configuration
    currency: Mapped["CurrencyConfiguration"] = relationship("CurrencyConfiguration")

    def __repr__(self) -> str:
        return (f"<AccountCurrencyConfig(account_id={self.account_id}, "
                f"symbol='{self.currency_symbol}', enabled={self.enabled})>")

    def to_dict(self, include_global_defaults: bool = False) -> dict:
        """
        Convert to dictionary

        Args:
            include_global_defaults: If True, includes global values for NULL fields

        Returns:
            dict: Configuration with account-specific overrides
        """
        return {
            'id': self.id,
            'account_id': self.account_id,
            'symbol': self.currency_symbol,
            'enabled': self.enabled,

            # Risk (overrides only)
            'risk_percent': self.risk_percent,
            'max_position_size': self.max_position_size,
            'min_position_size': self.min_position_size,

            # Strategy (overrides only)
            'strategy_type': self.strategy_type,
            'timeframe': self.timeframe,

            # Indicators (overrides only)
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,

            # SL/TP (overrides only)
            'sl_pips': self.sl_pips,
            'tp_pips': self.tp_pips,

            # Trading Rules (overrides only)
            'cooldown_seconds': self.cooldown_seconds,
            'trade_on_signal_change': self.trade_on_signal_change,

            # Position Stacking (overrides only)
            'allow_position_stacking': self.allow_position_stacking,
            'max_positions_same_direction': self.max_positions_same_direction,
            'max_total_positions': self.max_total_positions,
            'stacking_risk_multiplier': self.stacking_risk_multiplier,

            # Metadata
            'is_override': True,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def merge_with_global(self, global_config: "CurrencyConfiguration") -> dict:
        """
        Merge account-specific overrides with global defaults

        Args:
            global_config: Global currency configuration to use as fallback

        Returns:
            dict: Merged configuration with account overrides taking precedence
        """
        return {
            'id': self.id,
            'account_id': self.account_id,
            'symbol': self.currency_symbol,
            'enabled': self.enabled,

            # Use override if present, otherwise global default
            'risk_percent': self.risk_percent if self.risk_percent is not None else global_config.risk_percent,
            'max_position_size': self.max_position_size if self.max_position_size is not None else global_config.max_position_size,
            'min_position_size': self.min_position_size if self.min_position_size is not None else global_config.min_position_size,

            'strategy_type': self.strategy_type or global_config.strategy_type,
            'timeframe': self.timeframe or global_config.timeframe,

            'fast_period': self.fast_period if self.fast_period is not None else global_config.fast_period,
            'slow_period': self.slow_period if self.slow_period is not None else global_config.slow_period,

            'sl_pips': self.sl_pips if self.sl_pips is not None else global_config.sl_pips,
            'tp_pips': self.tp_pips if self.tp_pips is not None else global_config.tp_pips,

            'cooldown_seconds': self.cooldown_seconds if self.cooldown_seconds is not None else global_config.cooldown_seconds,
            'trade_on_signal_change': self.trade_on_signal_change if self.trade_on_signal_change is not None else global_config.trade_on_signal_change,

            'allow_position_stacking': self.allow_position_stacking if self.allow_position_stacking is not None else global_config.allow_position_stacking,
            'max_positions_same_direction': self.max_positions_same_direction if self.max_positions_same_direction is not None else global_config.max_positions_same_direction,
            'max_total_positions': self.max_total_positions if self.max_total_positions is not None else global_config.max_total_positions,
            'stacking_risk_multiplier': self.stacking_risk_multiplier if self.stacking_risk_multiplier is not None else global_config.stacking_risk_multiplier,

            # Metadata
            'is_override': True,
            'description': global_config.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
