"""
Unit tests for Configuration V2 value objects (models)

Tests immutability, validation, and value object behavior.
"""

import pytest
from src.config.v2.models import (
    ExecutionConfig,
    RiskConfig,
    StrategyConfig,
    PositionManagementConfig,
    CurrencyConfiguration,
    AccountConfig,
    GlobalDefaults,
    TimeFrame,
    StrategyType,
)


class TestExecutionConfig:
    """Tests for ExecutionConfig value object"""

    def test_create_valid_execution_config(self):
        """Test creating valid ExecutionConfig"""
        config = ExecutionConfig(
            interval_seconds=30,
            parallel_execution=True,
            max_workers=4
        )

        assert config.interval_seconds == 30
        assert config.parallel_execution is True
        assert config.max_workers == 4

    def test_execution_config_immutable(self):
        """Test that ExecutionConfig is immutable"""
        config = ExecutionConfig(interval_seconds=30)

        with pytest.raises(AttributeError):
            config.interval_seconds = 60  # Should raise error (frozen dataclass)

    def test_execution_config_validation(self):
        """Test ExecutionConfig validation"""
        # Invalid interval_seconds
        with pytest.raises(ValueError, match="interval_seconds must be >= 1"):
            ExecutionConfig(interval_seconds=0)

        # Invalid max_workers
        with pytest.raises(ValueError, match="max_workers must be >= 1"):
            ExecutionConfig(interval_seconds=30, max_workers=0)

    def test_execution_config_to_dict(self):
        """Test converting ExecutionConfig to dictionary"""
        config = ExecutionConfig(
            interval_seconds=30,
            parallel_execution=True,
            max_workers=4
        )

        config_dict = config.to_dict()

        assert config_dict["interval_seconds"] == 30
        assert config_dict["parallel_execution"] is True
        assert config_dict["max_workers"] == 4


class TestRiskConfig:
    """Tests for RiskConfig value object"""

    def test_create_valid_risk_config(self):
        """Test creating valid RiskConfig"""
        config = RiskConfig(
            risk_percent=2.0,
            max_positions=3,
            portfolio_risk_percent=8.0
        )

        assert config.risk_percent == 2.0
        assert config.max_positions == 3
        assert config.portfolio_risk_percent == 8.0

    def test_risk_config_immutable(self):
        """Test that RiskConfig is immutable"""
        config = RiskConfig(risk_percent=2.0, max_positions=3)

        with pytest.raises(AttributeError):
            config.risk_percent = 5.0  # Should raise error

    def test_risk_config_validation(self):
        """Test RiskConfig validation"""
        # Invalid risk_percent (too low)
        with pytest.raises(ValueError, match="risk_percent must be between 0.1 and 10.0"):
            RiskConfig(risk_percent=0.05, max_positions=3)

        # Invalid risk_percent (too high)
        with pytest.raises(ValueError, match="risk_percent must be between 0.1 and 10.0"):
            RiskConfig(risk_percent=15.0, max_positions=3)

        # Invalid max_positions
        with pytest.raises(ValueError, match="max_positions must be >= 1"):
            RiskConfig(risk_percent=2.0, max_positions=0)

        # Invalid portfolio_risk_percent
        with pytest.raises(ValueError, match="portfolio_risk_percent must be between 1.0 and 20.0"):
            RiskConfig(
                risk_percent=2.0,
                max_positions=3,
                portfolio_risk_percent=25.0
            )


class TestStrategyConfig:
    """Tests for StrategyConfig value object"""

    def test_create_valid_strategy_config(self):
        """Test creating valid StrategyConfig"""
        config = StrategyConfig(
            strategy_type=StrategyType.RSI,
            timeframe=TimeFrame.H1,
            atr_period=14,
            atr_sl_multiplier=2.0,
            atr_tp_multiplier=3.0
        )

        assert config.strategy_type == StrategyType.RSI
        assert config.timeframe == TimeFrame.H1
        assert config.atr_period == 14

    def test_strategy_config_immutable(self):
        """Test that StrategyConfig is immutable"""
        config = StrategyConfig(
            strategy_type=StrategyType.SIMPLE_MA,
            timeframe=TimeFrame.H1
        )

        with pytest.raises(AttributeError):
            config.atr_period = 20  # Should raise error

    def test_strategy_config_validation(self):
        """Test StrategyConfig validation"""
        # Invalid ATR period
        with pytest.raises(ValueError, match="atr_period must be between 5 and 50"):
            StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1,
                atr_period=100
            )

        # Invalid fixed SL (use_fixed_sl=True but no pips)
        with pytest.raises(ValueError, match="fixed_sl_pips must be > 0 when use_fixed_sl is True"):
            StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1,
                use_fixed_sl=True,
                fixed_sl_pips=None
            )


class TestCurrencyConfiguration:
    """Tests for CurrencyConfiguration value object"""

    def test_create_valid_currency_config(self):
        """Test creating valid CurrencyConfiguration"""
        config = CurrencyConfiguration(
            symbol="EURUSD",
            enabled=True,
            risk=RiskConfig(risk_percent=2.0, max_positions=3),
            strategy=StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1
            ),
            position_management=PositionManagementConfig()
        )

        assert config.symbol == "EURUSD"
        assert config.enabled is True
        assert config.risk.risk_percent == 2.0

    def test_currency_config_validation(self):
        """Test CurrencyConfiguration validation"""
        # Invalid symbol (too short)
        with pytest.raises(ValueError, match="symbol must be at least 6 characters"):
            CurrencyConfiguration(
                symbol="EUR",
                enabled=True,
                risk=RiskConfig(risk_percent=2.0, max_positions=3),
                strategy=StrategyConfig(
                    strategy_type=StrategyType.RSI,
                    timeframe=TimeFrame.H1
                ),
                position_management=PositionManagementConfig()
            )

        # Invalid symbol (not uppercase)
        with pytest.raises(ValueError, match="symbol must be uppercase"):
            CurrencyConfiguration(
                symbol="eurusd",
                enabled=True,
                risk=RiskConfig(risk_percent=2.0, max_positions=3),
                strategy=StrategyConfig(
                    strategy_type=StrategyType.RSI,
                    timeframe=TimeFrame.H1
                ),
                position_management=PositionManagementConfig()
            )


class TestAccountConfig:
    """Tests for AccountConfig value object"""

    def test_create_valid_account_config(self):
        """Test creating valid AccountConfig"""
        currency = CurrencyConfiguration(
            symbol="EURUSD",
            enabled=True,
            risk=RiskConfig(risk_percent=2.0, max_positions=3),
            strategy=StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1
            ),
            position_management=PositionManagementConfig()
        )

        config = AccountConfig(
            account_id="account-001",
            currencies=[currency],
            default_risk=RiskConfig(risk_percent=2.0, max_positions=3)
        )

        assert config.account_id == "account-001"
        assert len(config.currencies) == 1
        assert config.currencies[0].symbol == "EURUSD"

    def test_account_config_validation(self):
        """Test AccountConfig validation"""
        # Empty account_id
        with pytest.raises(ValueError, match="account_id cannot be empty"):
            AccountConfig(
                account_id="",
                currencies=[]
            )

        # Empty currencies list
        with pytest.raises(ValueError, match="currencies list cannot be empty"):
            AccountConfig(
                account_id="account-001",
                currencies=[]
            )

        # Duplicate symbols
        currency1 = CurrencyConfiguration(
            symbol="EURUSD",
            enabled=True,
            risk=RiskConfig(risk_percent=2.0, max_positions=3),
            strategy=StrategyConfig(
                strategy_type=StrategyType.RSI,
                timeframe=TimeFrame.H1
            ),
            position_management=PositionManagementConfig()
        )

        currency2 = CurrencyConfiguration(
            symbol="EURUSD",  # Duplicate
            enabled=True,
            risk=RiskConfig(risk_percent=2.0, max_positions=3),
            strategy=StrategyConfig(
                strategy_type=StrategyType.MACD,
                timeframe=TimeFrame.H4
            ),
            position_management=PositionManagementConfig()
        )

        with pytest.raises(ValueError, match="Duplicate symbols found"):
            AccountConfig(
                account_id="account-001",
                currencies=[currency1, currency2]
            )


class TestGlobalDefaults:
    """Tests for GlobalDefaults value object"""

    def test_create_valid_global_defaults(self):
        """Test creating valid GlobalDefaults"""
        defaults = GlobalDefaults(
            risk=RiskConfig(risk_percent=2.0, max_positions=3),
            execution=ExecutionConfig(interval_seconds=30),
            position_management=PositionManagementConfig(),
            strategy=StrategyConfig(
                strategy_type=StrategyType.SIMPLE_MA,
                timeframe=TimeFrame.H1
            )
        )

        assert defaults.risk.risk_percent == 2.0
        assert defaults.execution.interval_seconds == 30

    def test_global_defaults_immutable(self):
        """Test that GlobalDefaults is immutable"""
        defaults = GlobalDefaults(
            risk=RiskConfig(risk_percent=2.0, max_positions=3),
            execution=ExecutionConfig(interval_seconds=30),
            position_management=PositionManagementConfig(),
            strategy=StrategyConfig(
                strategy_type=StrategyType.SIMPLE_MA,
                timeframe=TimeFrame.H1
            )
        )

        with pytest.raises(AttributeError):
            defaults.risk = RiskConfig(risk_percent=5.0, max_positions=5)
