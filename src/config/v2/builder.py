"""
Configuration V2 Builder - Builder Pattern Implementation

Provides fluent interface for constructing complex configuration objects.

Design Pattern: Builder Pattern
- Separates construction from representation
- Provides fluent interface
- Handles complex object creation
- Validates on build()

SOLID: Single Responsibility - focuses only on object construction
"""

from typing import Optional, List
from src.config.v2.models import (
    ExecutionConfig,
    RiskConfig,
    StrategyConfig,
    PositionManagementConfig,
    CurrencyConfiguration,
    AccountConfig,
    TimeFrame,
    StrategyType,
)


class CurrencyConfigurationBuilder:
    """
    Builder for CurrencyConfiguration value objects

    Provides fluent interface for constructing currency configurations.

    Example:
        config = (CurrencyConfigurationBuilder("EURUSD")
            .enabled(True)
            .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
            .with_strategy(StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1
            ))
            .build())
    """

    def __init__(self, symbol: str):
        """
        Initialize builder with required symbol

        Args:
            symbol: Currency pair symbol (e.g., "EURUSD")
        """
        self._symbol = symbol.upper()
        self._enabled = True
        self._risk: Optional[RiskConfig] = None
        self._strategy: Optional[StrategyConfig] = None
        self._position_management: Optional[PositionManagementConfig] = None
        self._execution: Optional[ExecutionConfig] = None

    def enabled(self, enabled: bool) -> 'CurrencyConfigurationBuilder':
        """Set enabled flag"""
        self._enabled = enabled
        return self

    def with_risk(self, risk: RiskConfig) -> 'CurrencyConfigurationBuilder':
        """Set risk configuration"""
        self._risk = risk
        return self

    def with_strategy(self, strategy: StrategyConfig) -> 'CurrencyConfigurationBuilder':
        """Set strategy configuration"""
        self._strategy = strategy
        return self

    def with_position_management(
        self,
        position_management: PositionManagementConfig
    ) -> 'CurrencyConfigurationBuilder':
        """Set position management configuration"""
        self._position_management = position_management
        return self

    def with_execution(self, execution: ExecutionConfig) -> 'CurrencyConfigurationBuilder':
        """Set execution configuration"""
        self._execution = execution
        return self

    def build(self) -> CurrencyConfiguration:
        """
        Build and validate CurrencyConfiguration

        Returns:
            Validated CurrencyConfiguration value object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Ensure required fields are set
        if not self._risk:
            raise ValueError("Risk configuration is required")
        if not self._strategy:
            raise ValueError("Strategy configuration is required")
        if not self._position_management:
            raise ValueError("Position management configuration is required")

        # Build immutable value object
        return CurrencyConfiguration(
            symbol=self._symbol,
            enabled=self._enabled,
            risk=self._risk,
            strategy=self._strategy,
            position_management=self._position_management,
            execution=self._execution,
        )


class AccountConfigBuilder:
    """
    Builder for AccountConfig value objects

    Provides fluent interface for constructing account configurations.

    Example:
        config = (AccountConfigBuilder("account-001")
            .with_default_risk(RiskConfig(risk_percent=2.0, max_positions=3))
            .with_default_execution(ExecutionConfig(interval_seconds=30))
            .add_currency(currency_config)
            .build())
    """

    def __init__(self, account_id: str):
        """
        Initialize builder with required account ID

        Args:
            account_id: Unique account identifier
        """
        self._account_id = account_id
        self._currencies: List[CurrencyConfiguration] = []
        self._default_risk: Optional[RiskConfig] = None
        self._default_execution: Optional[ExecutionConfig] = None
        self._default_position_management: Optional[PositionManagementConfig] = None

    def with_default_risk(self, risk: RiskConfig) -> 'AccountConfigBuilder':
        """Set default risk configuration"""
        self._default_risk = risk
        return self

    def with_default_execution(self, execution: ExecutionConfig) -> 'AccountConfigBuilder':
        """Set default execution configuration"""
        self._default_execution = execution
        return self

    def with_default_position_management(
        self,
        position_management: PositionManagementConfig
    ) -> 'AccountConfigBuilder':
        """Set default position management configuration"""
        self._default_position_management = position_management
        return self

    def add_currency(self, currency: CurrencyConfiguration) -> 'AccountConfigBuilder':
        """
        Add a currency configuration

        Args:
            currency: Currency configuration to add

        Returns:
            Self for method chaining
        """
        self._currencies.append(currency)
        return self

    def add_currencies(self, currencies: List[CurrencyConfiguration]) -> 'AccountConfigBuilder':
        """
        Add multiple currency configurations

        Args:
            currencies: List of currency configurations to add

        Returns:
            Self for method chaining
        """
        self._currencies.extend(currencies)
        return self

    def build(self) -> AccountConfig:
        """
        Build and validate AccountConfig

        Returns:
            Validated AccountConfig value object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Ensure at least one currency is configured
        if not self._currencies:
            raise ValueError("At least one currency configuration is required")

        # Build immutable value object
        return AccountConfig(
            account_id=self._account_id,
            currencies=self._currencies.copy(),  # Copy to ensure immutability
            default_risk=self._default_risk,
            default_execution=self._default_execution,
            default_position_management=self._default_position_management,
        )


# =============================================================================
# Convenience Builders for Common Configurations
# =============================================================================

def create_default_risk() -> RiskConfig:
    """Create default risk configuration"""
    return RiskConfig(
        risk_percent=2.0,
        max_positions=3,
        portfolio_risk_percent=8.0,
        max_concurrent_trades=15,
        use_dynamic_sizing=False,
    )


def create_default_execution() -> ExecutionConfig:
    """Create default execution configuration"""
    return ExecutionConfig(
        interval_seconds=30,
        parallel_execution=False,
        max_workers=4,
        use_intelligent_position_manager=True,
        use_ml_enhancement=False,
        use_sentiment_filter=False,
    )


def create_default_position_management() -> PositionManagementConfig:
    """Create default position management configuration"""
    return PositionManagementConfig(
        enable_breakeven=True,
        breakeven_trigger_pips=15.0,
        breakeven_offset_pips=2.0,
        enable_trailing=True,
        trailing_start_pips=20.0,
        trailing_distance_pips=10.0,
        enable_partial_close=False,
        partial_close_percent=50.0,
        partial_close_profit_pips=25.0,
    )


def create_default_strategy(
    strategy_type: StrategyType = StrategyType.SIMPLE_MA,
    timeframe: TimeFrame = TimeFrame.H1
) -> StrategyConfig:
    """
    Create default strategy configuration

    Args:
        strategy_type: Strategy type to use
        timeframe: Timeframe to use

    Returns:
        Default StrategyConfig
    """
    return StrategyConfig(
        strategy_type=strategy_type,
        timeframe=timeframe,
        params={},
        atr_period=14,
        atr_sl_multiplier=2.0,
        atr_tp_multiplier=3.0,
        use_fixed_sl=False,
        fixed_sl_pips=None,
        use_fixed_tp=False,
        fixed_tp_pips=None,
    )
