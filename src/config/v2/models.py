"""
Configuration V2 Models - Immutable Value Objects

Defines immutable configuration value objects following:
- Value Object pattern (immutable, validated on creation)
- Single Responsibility Principle
- Fail-fast validation

All models are frozen dataclasses ensuring:
- Immutability (thread-safe)
- No accidental mutations
- Clear data contracts
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

from src.config.v2.interfaces import IConfigNode


# =============================================================================
# Enums for Type Safety
# =============================================================================

class TimeFrame(str, Enum):
    """Supported timeframes"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"


class StrategyType(str, Enum):
    """Supported strategy types"""
    SIMPLE_MA = "simple_ma"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    MULTI_INDICATOR = "multi_indicator"
    ML_STRATEGY = "ml_strategy"


# =============================================================================
# Value Objects (Immutable Configuration Models)
# =============================================================================

@dataclass(frozen=True)
class ExecutionConfig(IConfigNode):
    """
    Execution configuration value object (immutable)

    Defines how and when trading cycles execute.
    """
    interval_seconds: int
    parallel_execution: bool = False
    max_workers: int = 4
    use_intelligent_position_manager: bool = True
    use_ml_enhancement: bool = False
    use_sentiment_filter: bool = False

    def __post_init__(self):
        """Validate on creation (fail-fast)"""
        if self.interval_seconds < 1:
            raise ValueError("interval_seconds must be >= 1")
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "interval_seconds": self.interval_seconds,
            "parallel_execution": self.parallel_execution,
            "max_workers": self.max_workers,
            "use_intelligent_position_manager": self.use_intelligent_position_manager,
            "use_ml_enhancement": self.use_ml_enhancement,
            "use_sentiment_filter": self.use_sentiment_filter,
        }

    def validate(self) -> None:
        """Validation already done in __post_init__"""
        pass


@dataclass(frozen=True)
class RiskConfig(IConfigNode):
    """
    Risk management configuration value object (immutable)

    Defines position sizing and risk parameters.
    """
    risk_percent: float
    max_positions: int
    portfolio_risk_percent: Optional[float] = None
    max_concurrent_trades: Optional[int] = None
    use_dynamic_sizing: bool = False

    def __post_init__(self):
        """Validate on creation (fail-fast)"""
        if not (0.1 <= self.risk_percent <= 10.0):
            raise ValueError("risk_percent must be between 0.1 and 10.0")
        if self.max_positions < 1:
            raise ValueError("max_positions must be >= 1")
        if self.portfolio_risk_percent is not None and not (1.0 <= self.portfolio_risk_percent <= 20.0):
            raise ValueError("portfolio_risk_percent must be between 1.0 and 20.0")
        if self.max_concurrent_trades is not None and self.max_concurrent_trades < 1:
            raise ValueError("max_concurrent_trades must be >= 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "risk_percent": self.risk_percent,
            "max_positions": self.max_positions,
            "portfolio_risk_percent": self.portfolio_risk_percent,
            "max_concurrent_trades": self.max_concurrent_trades,
            "use_dynamic_sizing": self.use_dynamic_sizing,
        }

    def validate(self) -> None:
        """Validation already done in __post_init__"""
        pass


@dataclass(frozen=True)
class StrategyConfig(IConfigNode):
    """
    Trading strategy configuration value object (immutable)

    Defines strategy parameters and behavior.
    """
    strategy_type: StrategyType
    timeframe: TimeFrame
    params: Dict[str, Any] = field(default_factory=dict)

    # ATR-based SL/TP
    atr_period: int = 14
    atr_sl_multiplier: float = 2.0
    atr_tp_multiplier: float = 3.0

    # Fixed SL/TP (optional)
    use_fixed_sl: bool = False
    fixed_sl_pips: Optional[float] = None
    use_fixed_tp: bool = False
    fixed_tp_pips: Optional[float] = None

    def __post_init__(self):
        """Validate on creation (fail-fast)"""
        if not (5 <= self.atr_period <= 50):
            raise ValueError("atr_period must be between 5 and 50")
        if not (0.5 <= self.atr_sl_multiplier <= 5.0):
            raise ValueError("atr_sl_multiplier must be between 0.5 and 5.0")
        if not (1.0 <= self.atr_tp_multiplier <= 10.0):
            raise ValueError("atr_tp_multiplier must be between 1.0 and 10.0")

        # Validate fixed SL/TP consistency
        if self.use_fixed_sl and (self.fixed_sl_pips is None or self.fixed_sl_pips <= 0):
            raise ValueError("fixed_sl_pips must be > 0 when use_fixed_sl is True")
        if self.use_fixed_tp and (self.fixed_tp_pips is None or self.fixed_tp_pips <= 0):
            raise ValueError("fixed_tp_pips must be > 0 when use_fixed_tp is True")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "strategy_type": self.strategy_type.value,
            "timeframe": self.timeframe.value,
            "params": self.params.copy(),
            "atr_period": self.atr_period,
            "atr_sl_multiplier": self.atr_sl_multiplier,
            "atr_tp_multiplier": self.atr_tp_multiplier,
            "use_fixed_sl": self.use_fixed_sl,
            "fixed_sl_pips": self.fixed_sl_pips,
            "use_fixed_tp": self.use_fixed_tp,
            "fixed_tp_pips": self.fixed_tp_pips,
        }

    def validate(self) -> None:
        """Validation already done in __post_init__"""
        pass


@dataclass(frozen=True)
class PositionManagementConfig(IConfigNode):
    """
    Position management configuration value object (immutable)

    Defines SL/TP automation and position management rules.
    """
    # Breakeven
    enable_breakeven: bool = True
    breakeven_trigger_pips: float = 15.0
    breakeven_offset_pips: float = 2.0

    # Trailing stop
    enable_trailing: bool = True
    trailing_start_pips: float = 20.0
    trailing_distance_pips: float = 10.0

    # Partial close
    enable_partial_close: bool = False
    partial_close_percent: float = 50.0
    partial_close_profit_pips: float = 25.0

    def __post_init__(self):
        """Validate on creation (fail-fast)"""
        if not (5.0 <= self.breakeven_trigger_pips <= 100.0):
            raise ValueError("breakeven_trigger_pips must be between 5.0 and 100.0")
        if not (0.0 <= self.breakeven_offset_pips <= 20.0):
            raise ValueError("breakeven_offset_pips must be between 0.0 and 20.0")
        if not (10.0 <= self.trailing_start_pips <= 200.0):
            raise ValueError("trailing_start_pips must be between 10.0 and 200.0")
        if not (5.0 <= self.trailing_distance_pips <= 100.0):
            raise ValueError("trailing_distance_pips must be between 5.0 and 100.0")
        if not (10.0 <= self.partial_close_percent <= 90.0):
            raise ValueError("partial_close_percent must be between 10.0 and 90.0")
        if not (10.0 <= self.partial_close_profit_pips <= 200.0):
            raise ValueError("partial_close_profit_pips must be between 10.0 and 200.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "enable_breakeven": self.enable_breakeven,
            "breakeven_trigger_pips": self.breakeven_trigger_pips,
            "breakeven_offset_pips": self.breakeven_offset_pips,
            "enable_trailing": self.enable_trailing,
            "trailing_start_pips": self.trailing_start_pips,
            "trailing_distance_pips": self.trailing_distance_pips,
            "enable_partial_close": self.enable_partial_close,
            "partial_close_percent": self.partial_close_percent,
            "partial_close_profit_pips": self.partial_close_profit_pips,
        }

    def validate(self) -> None:
        """Validation already done in __post_init__"""
        pass


@dataclass(frozen=True)
class CurrencyConfiguration(IConfigNode):
    """
    Currency-specific configuration value object (immutable)

    Combines all configuration aspects for a single currency pair.
    """
    symbol: str
    enabled: bool
    risk: RiskConfig
    strategy: StrategyConfig
    position_management: PositionManagementConfig
    execution: Optional[ExecutionConfig] = None

    def __post_init__(self):
        """Validate on creation (fail-fast)"""
        if not self.symbol or len(self.symbol) < 6:
            raise ValueError("symbol must be at least 6 characters")
        if not self.symbol.isupper():
            raise ValueError("symbol must be uppercase")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "enabled": self.enabled,
            "risk": self.risk.to_dict(),
            "strategy": self.strategy.to_dict(),
            "position_management": self.position_management.to_dict(),
            "execution": self.execution.to_dict() if self.execution else None,
        }

    def validate(self) -> None:
        """Validate all nested configs"""
        self.risk.validate()
        self.strategy.validate()
        self.position_management.validate()
        if self.execution:
            self.execution.validate()


@dataclass(frozen=True)
class AccountConfig(IConfigNode):
    """
    Account-level configuration value object (immutable)

    Combines account-wide defaults and currency-specific configurations.
    """
    account_id: str
    currencies: List[CurrencyConfiguration]
    default_risk: Optional[RiskConfig] = None
    default_execution: Optional[ExecutionConfig] = None
    default_position_management: Optional[PositionManagementConfig] = None

    def __post_init__(self):
        """Validate on creation (fail-fast)"""
        if not self.account_id:
            raise ValueError("account_id cannot be empty")
        if not self.currencies:
            raise ValueError("currencies list cannot be empty")

        # Validate no duplicate symbols
        symbols = [c.symbol for c in self.currencies]
        if len(symbols) != len(set(symbols)):
            duplicates = [s for s in symbols if symbols.count(s) > 1]
            raise ValueError(f"Duplicate symbols found: {set(duplicates)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "account_id": self.account_id,
            "currencies": [c.to_dict() for c in self.currencies],
            "default_risk": self.default_risk.to_dict() if self.default_risk else None,
            "default_execution": self.default_execution.to_dict() if self.default_execution else None,
            "default_position_management": self.default_position_management.to_dict() if self.default_position_management else None,
        }

    def validate(self) -> None:
        """Validate all nested configs"""
        for currency in self.currencies:
            currency.validate()
        if self.default_risk:
            self.default_risk.validate()
        if self.default_execution:
            self.default_execution.validate()
        if self.default_position_management:
            self.default_position_management.validate()


@dataclass(frozen=True)
class GlobalDefaults(IConfigNode):
    """
    Global default configuration value object (immutable)

    Defines system-wide defaults that can be overridden at account/currency level.
    """
    risk: RiskConfig
    execution: ExecutionConfig
    position_management: PositionManagementConfig
    strategy: StrategyConfig

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "risk": self.risk.to_dict(),
            "execution": self.execution.to_dict(),
            "position_management": self.position_management.to_dict(),
            "strategy": self.strategy.to_dict(),
        }

    def validate(self) -> None:
        """Validate all nested configs"""
        self.risk.validate()
        self.execution.validate()
        self.position_management.validate()
        self.strategy.validate()
