"""
Unit tests for Configuration V2 Builder pattern

Tests fluent interface and builder functionality.
"""

import pytest
from src.config.v2.builder import (
    CurrencyConfigurationBuilder,
    AccountConfigBuilder,
    create_default_risk,
    create_default_execution,
    create_default_position_management,
    create_default_strategy,
)
from src.config.v2.models import (
    RiskConfig,
    StrategyConfig,
    PositionManagementConfig,
    ExecutionConfig,
    TimeFrame,
    StrategyType,
)


class TestCurrencyConfigurationBuilder:
    """Tests for CurrencyConfigurationBuilder"""

    def test_builder_fluent_interface(self):
        """Test builder fluent interface"""
        config = (CurrencyConfigurationBuilder("EURUSD")
            .enabled(True)
            .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
            .with_strategy(StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1
            ))
            .with_position_management(PositionManagementConfig())
            .build())

        assert config.symbol == "EURUSD"
        assert config.enabled is True
        assert config.risk.risk_percent == 2.0
        assert config.strategy.strategy_type == StrategyType.RSI

    def test_builder_uppercase_symbol(self):
        """Test builder converts symbol to uppercase"""
        config = (CurrencyConfigurationBuilder("eurusd")
            .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
            .with_strategy(StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1
            ))
            .with_position_management(PositionManagementConfig())
            .build())

        assert config.symbol == "EURUSD"

    def test_builder_missing_required_fields(self):
        """Test builder fails when required fields are missing"""
        # Missing risk
        with pytest.raises(ValueError, match="Risk configuration is required"):
            (CurrencyConfigurationBuilder("EURUSD")
                .with_strategy(StrategyConfig(
                    strategy_type=StrategyType.RSI,
                    timeframe=TimeFrame.H1
                ))
                .with_position_management(PositionManagementConfig())
                .build())

        # Missing strategy
        with pytest.raises(ValueError, match="Strategy configuration is required"):
            (CurrencyConfigurationBuilder("EURUSD")
                .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
                .with_position_management(PositionManagementConfig())
                .build())

        # Missing position_management
        with pytest.raises(ValueError, match="Position management configuration is required"):
            (CurrencyConfigurationBuilder("EURUSD")
                .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
                .with_strategy(StrategyConfig(
                    strategy_type=StrategyType.RSI,
                    timeframe=TimeFrame.H1
                ))
                .build())


class TestAccountConfigBuilder:
    """Tests for AccountConfigBuilder"""

    def test_builder_fluent_interface(self):
        """Test builder fluent interface"""
        currency = (CurrencyConfigurationBuilder("EURUSD")
            .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
            .with_strategy(StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1
            ))
            .with_position_management(PositionManagementConfig())
            .build())

        config = (AccountConfigBuilder("account-001")
            .with_default_risk(RiskConfig(risk_percent=2.0, max_positions=3))
            .with_default_execution(ExecutionConfig(interval_seconds=30))
            .add_currency(currency)
            .build())

        assert config.account_id == "account-001"
        assert len(config.currencies) == 1
        assert config.default_risk.risk_percent == 2.0

    def test_builder_add_multiple_currencies(self):
        """Test adding multiple currencies"""
        currency1 = (CurrencyConfigurationBuilder("EURUSD")
            .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
            .with_strategy(StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1
            ))
            .with_position_management(PositionManagementConfig())
            .build())

        currency2 = (CurrencyConfigurationBuilder("GBPUSD")
            .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
            .with_strategy(StrategyConfig(
                strategy_type=StrategyType.MACD,
                timeframe=TimeFrame.H4
            ))
            .with_position_management(PositionManagementConfig())
            .build())

        config = (AccountConfigBuilder("account-001")
            .add_currency(currency1)
            .add_currency(currency2)
            .build())

        assert len(config.currencies) == 2
        assert config.currencies[0].symbol == "EURUSD"
        assert config.currencies[1].symbol == "GBPUSD"

    def test_builder_add_currencies_list(self):
        """Test adding currencies as a list"""
        currencies = [
            (CurrencyConfigurationBuilder("EURUSD")
                .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
                .with_strategy(StrategyConfig(
                    strategy_type=StrategyType.RSI,
                    timeframe=TimeFrame.H1
                ))
                .with_position_management(PositionManagementConfig())
                .build()),
            (CurrencyConfigurationBuilder("GBPUSD")
                .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
                .with_strategy(StrategyConfig(
                    strategy_type=StrategyType.MACD,
                    timeframe=TimeFrame.H4
                ))
                .with_position_management(PositionManagementConfig())
                .build())
        ]

        config = (AccountConfigBuilder("account-001")
            .add_currencies(currencies)
            .build())

        assert len(config.currencies) == 2

    def test_builder_missing_currencies(self):
        """Test builder fails when no currencies are added"""
        with pytest.raises(ValueError, match="At least one currency configuration is required"):
            (AccountConfigBuilder("account-001")
                .with_default_risk(RiskConfig(risk_percent=2.0, max_positions=3))
                .build())


class TestConvenienceBuilders:
    """Tests for convenience builder functions"""

    def test_create_default_risk(self):
        """Test create_default_risk"""
        risk = create_default_risk()

        assert risk.risk_percent == 2.0
        assert risk.max_positions == 3
        assert risk.portfolio_risk_percent == 8.0
        assert risk.max_concurrent_trades == 15

    def test_create_default_execution(self):
        """Test create_default_execution"""
        execution = create_default_execution()

        assert execution.interval_seconds == 30
        assert execution.parallel_execution is False
        assert execution.max_workers == 4
        assert execution.use_intelligent_position_manager is True

    def test_create_default_position_management(self):
        """Test create_default_position_management"""
        pm = create_default_position_management()

        assert pm.enable_breakeven is True
        assert pm.breakeven_trigger_pips == 15.0
        assert pm.enable_trailing is True

    def test_create_default_strategy(self):
        """Test create_default_strategy"""
        strategy = create_default_strategy()

        assert strategy.strategy_type == StrategyType.SIMPLE_MA
        assert strategy.timeframe == TimeFrame.H1
        assert strategy.atr_period == 14

        # Test with custom parameters
        strategy = create_default_strategy(
            strategy_type=StrategyType.RSI,
            timeframe=TimeFrame.M15
        )

        assert strategy.strategy_type == StrategyType.RSI
        assert strategy.timeframe == TimeFrame.M15
