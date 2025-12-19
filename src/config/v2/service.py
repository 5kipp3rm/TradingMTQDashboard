"""
Configuration V2 Service - Service Layer Implementation

Provides business logic for configuration management.

Design Pattern: Service Layer
- Encapsulates business logic
- Coordinates between repositories and domain models
- Provides high-level operations

SOLID: Single Responsibility - focuses on configuration business logic
"""

from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

from src.config.v2.interfaces import IConfigRepository, IMergeStrategy
from src.config.v2.models import (
    AccountConfig,
    CurrencyConfiguration,
    GlobalDefaults,
    ExecutionConfig,
    RiskConfig,
    StrategyConfig,
    PositionManagementConfig,
    TimeFrame,
    StrategyType,
)
from src.config.v2.builder import AccountConfigBuilder, CurrencyConfigurationBuilder


logger = logging.getLogger(__name__)


class ConfigurationService:
    """
    Configuration Service - Business Logic Layer

    Provides high-level operations for configuration management:
    - Load and merge hierarchical configurations
    - Apply inheritance (defaults → account → currency)
    - Validate configurations
    - Convert between formats

    Dependencies injected via constructor (DI principle).

    Example:
        service = ConfigurationService(
            repository=YamlConfigRepository(),
            merge_strategy=DefaultMergeStrategy()
        )

        # Load account config with inheritance
        config = service.load_account_config(
            account_id="account-001",
            apply_defaults=True
        )
    """

    def __init__(
        self,
        repository: IConfigRepository,
        merge_strategy: IMergeStrategy,
    ):
        """
        Initialize configuration service

        Args:
            repository: Configuration repository (injected dependency)
            merge_strategy: Merge strategy (injected dependency)
        """
        self.repository = repository
        self.merge_strategy = merge_strategy
        logger.info(
            f"Initialized ConfigurationService with "
            f"{repository.__class__.__name__} and {merge_strategy.__class__.__name__}"
        )

    def load_global_defaults(self, path: str = "defaults.yaml") -> GlobalDefaults:
        """
        Load global default configuration

        Args:
            path: Path to defaults configuration file

        Returns:
            GlobalDefaults value object

        Raises:
            FileNotFoundError: If defaults file not found
            ValueError: If configuration is invalid
        """
        logger.debug(f"Loading global defaults from {path}")

        config_dict = self.repository.load(path)

        # Build GlobalDefaults from dict
        return self._build_global_defaults(config_dict)

    def load_account_config(
        self,
        account_id: str,
        apply_defaults: bool = True,
        defaults_path: str = "defaults.yaml"
    ) -> AccountConfig:
        """
        Load account configuration with optional default inheritance

        Args:
            account_id: Account identifier
            apply_defaults: If True, merge with global defaults
            defaults_path: Path to defaults configuration

        Returns:
            AccountConfig value object

        Raises:
            FileNotFoundError: If account config not found
            ValueError: If configuration is invalid
        """
        logger.debug(f"Loading account config for {account_id}")

        # Load account config
        account_path = f"accounts/{account_id}.yaml"
        account_dict = self.repository.load(account_path)

        # Apply defaults if requested
        if apply_defaults and self.repository.exists(defaults_path):
            defaults_dict = self.repository.load(defaults_path)
            merged_dict = self.merge_strategy.merge(defaults_dict, account_dict)
        else:
            merged_dict = account_dict

        # Build AccountConfig from merged dict
        return self._build_account_config(account_id, merged_dict)

    def save_account_config(self, config: AccountConfig) -> None:
        """
        Save account configuration

        Args:
            config: AccountConfig to save

        Raises:
            IOError: If save operation fails
        """
        logger.debug(f"Saving account config for {config.account_id}")

        # Convert to dict
        config_dict = config.to_dict()

        # Save to repository
        account_path = f"accounts/{config.account_id}.yaml"
        self.repository.save(account_path, config_dict)

        logger.info(f"Saved account config for {config.account_id}")

    def list_accounts(self) -> List[str]:
        """
        List all available account configurations

        Returns:
            List of account IDs
        """
        configs = self.repository.list_configs("accounts/*.yaml")
        # Extract account IDs from filenames
        return [Path(c).stem for c in configs]

    def merge_account_with_defaults(
        self,
        account_dict: Dict[str, Any],
        defaults_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge account configuration with defaults

        Args:
            account_dict: Account-specific configuration
            defaults_dict: Global defaults configuration

        Returns:
            Merged configuration dictionary
        """
        return self.merge_strategy.merge(defaults_dict, account_dict)

    def _build_global_defaults(self, config_dict: Dict[str, Any]) -> GlobalDefaults:
        """
        Build GlobalDefaults value object from dictionary

        Args:
            config_dict: Raw configuration dictionary

        Returns:
            GlobalDefaults value object

        Raises:
            ValueError: If configuration is invalid
        """
        # Extract sub-configurations
        risk_dict = config_dict.get("risk", {})
        execution_dict = config_dict.get("execution", {})
        position_mgmt_dict = config_dict.get("position_management", {})
        strategy_dict = config_dict.get("strategy", {})

        # Build value objects
        risk = RiskConfig(
            risk_percent=risk_dict.get("risk_percent", 2.0),
            max_positions=risk_dict.get("max_positions", 3),
            portfolio_risk_percent=risk_dict.get("portfolio_risk_percent", 8.0),
            max_concurrent_trades=risk_dict.get("max_concurrent_trades", 15),
            use_dynamic_sizing=risk_dict.get("use_dynamic_sizing", False),
        )

        execution = ExecutionConfig(
            interval_seconds=execution_dict.get("interval_seconds", 30),
            parallel_execution=execution_dict.get("parallel_execution", False),
            max_workers=execution_dict.get("max_workers", 4),
            use_intelligent_position_manager=execution_dict.get("use_intelligent_position_manager", True),
            use_ml_enhancement=execution_dict.get("use_ml_enhancement", False),
            use_sentiment_filter=execution_dict.get("use_sentiment_filter", False),
        )

        position_mgmt = PositionManagementConfig(
            enable_breakeven=position_mgmt_dict.get("enable_breakeven", True),
            breakeven_trigger_pips=position_mgmt_dict.get("breakeven_trigger_pips", 15.0),
            breakeven_offset_pips=position_mgmt_dict.get("breakeven_offset_pips", 2.0),
            enable_trailing=position_mgmt_dict.get("enable_trailing", True),
            trailing_start_pips=position_mgmt_dict.get("trailing_start_pips", 20.0),
            trailing_distance_pips=position_mgmt_dict.get("trailing_distance_pips", 10.0),
            enable_partial_close=position_mgmt_dict.get("enable_partial_close", False),
            partial_close_percent=position_mgmt_dict.get("partial_close_percent", 50.0),
            partial_close_profit_pips=position_mgmt_dict.get("partial_close_profit_pips", 25.0),
        )

        strategy = StrategyConfig(
            strategy_type=StrategyType(strategy_dict.get("strategy_type", "simple_ma")),
            timeframe=TimeFrame(strategy_dict.get("timeframe", "H1")),
            params=strategy_dict.get("params", {}),
            atr_period=strategy_dict.get("atr_period", 14),
            atr_sl_multiplier=strategy_dict.get("atr_sl_multiplier", 2.0),
            atr_tp_multiplier=strategy_dict.get("atr_tp_multiplier", 3.0),
            use_fixed_sl=strategy_dict.get("use_fixed_sl", False),
            fixed_sl_pips=strategy_dict.get("fixed_sl_pips"),
            use_fixed_tp=strategy_dict.get("use_fixed_tp", False),
            fixed_tp_pips=strategy_dict.get("fixed_tp_pips"),
        )

        return GlobalDefaults(
            risk=risk,
            execution=execution,
            position_management=position_mgmt,
            strategy=strategy,
        )

    def _build_account_config(
        self,
        account_id: str,
        config_dict: Dict[str, Any]
    ) -> AccountConfig:
        """
        Build AccountConfig value object from dictionary

        Args:
            account_id: Account identifier
            config_dict: Raw configuration dictionary

        Returns:
            AccountConfig value object

        Raises:
            ValueError: If configuration is invalid
        """
        builder = AccountConfigBuilder(account_id)

        # Extract account-level defaults if present
        if "default_risk" in config_dict:
            default_risk = self._build_risk_config(config_dict["default_risk"])
            builder.with_default_risk(default_risk)

        if "default_execution" in config_dict:
            default_execution = self._build_execution_config(config_dict["default_execution"])
            builder.with_default_execution(default_execution)

        if "default_position_management" in config_dict:
            default_pm = self._build_position_management_config(
                config_dict["default_position_management"]
            )
            builder.with_default_position_management(default_pm)

        # Build currency configurations
        currencies_list = config_dict.get("currencies", [])
        for currency_dict in currencies_list:
            currency_config = self._build_currency_config(currency_dict)
            builder.add_currency(currency_config)

        return builder.build()

    def _build_currency_config(self, config_dict: Dict[str, Any]) -> CurrencyConfiguration:
        """Build CurrencyConfiguration from dictionary"""
        symbol = config_dict.get("symbol", "")
        enabled = config_dict.get("enabled", True)

        # Build sub-configs
        risk = self._build_risk_config(config_dict.get("risk", {}))
        strategy = self._build_strategy_config(config_dict.get("strategy", {}))
        position_mgmt = self._build_position_management_config(
            config_dict.get("position_management", {})
        )

        execution = None
        if "execution" in config_dict:
            execution = self._build_execution_config(config_dict["execution"])

        return CurrencyConfiguration(
            symbol=symbol,
            enabled=enabled,
            risk=risk,
            strategy=strategy,
            position_management=position_mgmt,
            execution=execution,
        )

    def _build_risk_config(self, config_dict: Dict[str, Any]) -> RiskConfig:
        """Build RiskConfig from dictionary"""
        return RiskConfig(
            risk_percent=config_dict.get("risk_percent", 2.0),
            max_positions=config_dict.get("max_positions", 3),
            portfolio_risk_percent=config_dict.get("portfolio_risk_percent"),
            max_concurrent_trades=config_dict.get("max_concurrent_trades"),
            use_dynamic_sizing=config_dict.get("use_dynamic_sizing", False),
        )

    def _build_execution_config(self, config_dict: Dict[str, Any]) -> ExecutionConfig:
        """Build ExecutionConfig from dictionary"""
        return ExecutionConfig(
            interval_seconds=config_dict.get("interval_seconds", 30),
            parallel_execution=config_dict.get("parallel_execution", False),
            max_workers=config_dict.get("max_workers", 4),
            use_intelligent_position_manager=config_dict.get("use_intelligent_position_manager", True),
            use_ml_enhancement=config_dict.get("use_ml_enhancement", False),
            use_sentiment_filter=config_dict.get("use_sentiment_filter", False),
        )

    def _build_strategy_config(self, config_dict: Dict[str, Any]) -> StrategyConfig:
        """Build StrategyConfig from dictionary"""
        return StrategyConfig(
            strategy_type=StrategyType(config_dict.get("strategy_type", "simple_ma")),
            timeframe=TimeFrame(config_dict.get("timeframe", "H1")),
            params=config_dict.get("params", {}),
            atr_period=config_dict.get("atr_period", 14),
            atr_sl_multiplier=config_dict.get("atr_sl_multiplier", 2.0),
            atr_tp_multiplier=config_dict.get("atr_tp_multiplier", 3.0),
            use_fixed_sl=config_dict.get("use_fixed_sl", False),
            fixed_sl_pips=config_dict.get("fixed_sl_pips"),
            use_fixed_tp=config_dict.get("use_fixed_tp", False),
            fixed_tp_pips=config_dict.get("fixed_tp_pips"),
        )

    def _build_position_management_config(
        self,
        config_dict: Dict[str, Any]
    ) -> PositionManagementConfig:
        """Build PositionManagementConfig from dictionary"""
        return PositionManagementConfig(
            enable_breakeven=config_dict.get("enable_breakeven", True),
            breakeven_trigger_pips=config_dict.get("breakeven_trigger_pips", 15.0),
            breakeven_offset_pips=config_dict.get("breakeven_offset_pips", 2.0),
            enable_trailing=config_dict.get("enable_trailing", True),
            trailing_start_pips=config_dict.get("trailing_start_pips", 20.0),
            trailing_distance_pips=config_dict.get("trailing_distance_pips", 10.0),
            enable_partial_close=config_dict.get("enable_partial_close", False),
            partial_close_percent=config_dict.get("partial_close_percent", 50.0),
            partial_close_profit_pips=config_dict.get("partial_close_profit_pips", 25.0),
        )
