"""
Configuration V2 - Full OOP Architecture

This module provides a fully object-oriented configuration system with:
- Interface-based programming
- Dependency injection
- SOLID principles
- Design patterns (Strategy, Builder, Factory, Repository)
- Immutable value objects
- Hierarchical configuration with inheritance

Usage:
    from src.config.v2 import ConfigurationFactory, AccountConfigBuilder

    # Create configuration service
    config_service = ConfigurationFactory.create_service(
        repository_type="yaml",
        merge_strategy_type="default"
    )

    # Load and merge configurations
    config = config_service.load_account_config("account-001")

    # Or build config manually
    config = (AccountConfigBuilder()
        .with_account_id("account-001")
        .with_risk(RiskConfig(risk_percent=2.0, max_positions=3))
        .with_execution(ExecutionConfig(interval_seconds=30))
        .build())
"""

from src.config.v2.interfaces import (
    IConfigNode,
    IConfigRepository,
    IMergeStrategy,
)

from src.config.v2.models import (
    ExecutionConfig,
    RiskConfig,
    StrategyConfig,
    CurrencyConfiguration,
    AccountConfig,
    GlobalDefaults,
)

from src.config.v2.builder import AccountConfigBuilder

from src.config.v2.factory import ConfigurationFactory

__all__ = [
    # Interfaces
    "IConfigNode",
    "IConfigRepository",
    "IMergeStrategy",
    # Models (Value Objects)
    "ExecutionConfig",
    "RiskConfig",
    "StrategyConfig",
    "CurrencyConfiguration",
    "AccountConfig",
    "GlobalDefaults",
    # Builder
    "AccountConfigBuilder",
    # Factory
    "ConfigurationFactory",
]
