"""
Configuration V2 Factory - Factory Pattern Implementation

Provides factory methods for creating configuration service instances.

Design Pattern: Factory Pattern
- Centralizes object creation logic
- Provides different creation strategies
- Simplifies dependency injection setup

SOLID: Dependency Inversion - creates appropriate implementations
"""

from typing import Optional
import logging

from src.config.v2.interfaces import IConfigRepository, IMergeStrategy
from src.config.v2.repository import (
    YamlConfigRepository,
    InMemoryConfigRepository,
    DatabaseConfigRepository,
)
from src.config.v2.merge_strategy import (
    DefaultMergeStrategy,
    DeepMergeStrategy,
    SelectiveMergeStrategy,
)
from src.config.v2.service import ConfigurationService


logger = logging.getLogger(__name__)


class ConfigurationFactory:
    """
    Factory for creating ConfigurationService instances

    Provides convenient factory methods for common configurations.

    Example:
        # Create service with YAML storage and default merge
        service = ConfigurationFactory.create_service()

        # Create service with in-memory storage (for testing)
        service = ConfigurationFactory.create_test_service()

        # Create service with custom configuration
        service = ConfigurationFactory.create_service(
            repository_type="yaml",
            merge_strategy_type="deep",
            config_path="config/"
        )
    """

    @staticmethod
    def create_repository(
        repository_type: str = "yaml",
        **kwargs
    ) -> IConfigRepository:
        """
        Create configuration repository

        Args:
            repository_type: Type of repository ("yaml", "memory", "database")
            **kwargs: Repository-specific configuration

        Returns:
            IConfigRepository implementation

        Raises:
            ValueError: If repository_type is unknown
        """
        if repository_type == "yaml":
            base_path = kwargs.get("config_path", "config")
            return YamlConfigRepository(base_path=base_path)

        elif repository_type == "memory":
            return InMemoryConfigRepository()

        elif repository_type == "database":
            connection_string = kwargs.get("connection_string")
            if not connection_string:
                raise ValueError("connection_string required for database repository")
            return DatabaseConfigRepository(connection_string=connection_string)

        else:
            raise ValueError(
                f"Unknown repository type: {repository_type}. "
                f"Valid types: yaml, memory, database"
            )

    @staticmethod
    def create_merge_strategy(
        strategy_type: str = "default",
        **kwargs
    ) -> IMergeStrategy:
        """
        Create merge strategy

        Args:
            strategy_type: Type of strategy ("default", "deep", "selective")
            **kwargs: Strategy-specific configuration

        Returns:
            IMergeStrategy implementation

        Raises:
            ValueError: If strategy_type is unknown
        """
        if strategy_type == "default":
            return DefaultMergeStrategy()

        elif strategy_type == "deep":
            list_merge_key = kwargs.get("list_merge_key", "id")
            return DeepMergeStrategy(list_merge_key=list_merge_key)

        elif strategy_type == "selective":
            merge_fields = kwargs.get("merge_fields", set())
            override_fields = kwargs.get("override_fields", set())
            return SelectiveMergeStrategy(
                merge_fields=merge_fields,
                override_fields=override_fields
            )

        else:
            raise ValueError(
                f"Unknown merge strategy: {strategy_type}. "
                f"Valid types: default, deep, selective"
            )

    @staticmethod
    def create_service(
        repository_type: str = "yaml",
        merge_strategy_type: str = "default",
        config_path: str = "config",
        **kwargs
    ) -> ConfigurationService:
        """
        Create ConfigurationService with specified components

        Args:
            repository_type: Type of repository ("yaml", "memory", "database")
            merge_strategy_type: Type of merge strategy ("default", "deep", "selective")
            config_path: Base path for configuration files (for yaml repository)
            **kwargs: Additional component-specific configuration

        Returns:
            Configured ConfigurationService instance

        Example:
            # Production configuration
            service = ConfigurationFactory.create_service(
                repository_type="yaml",
                merge_strategy_type="default",
                config_path="config/"
            )

            # Deep merge for complex hierarchies
            service = ConfigurationFactory.create_service(
                repository_type="yaml",
                merge_strategy_type="deep",
                config_path="config/",
                list_merge_key="symbol"
            )
        """
        # Create repository
        repository = ConfigurationFactory.create_repository(
            repository_type=repository_type,
            config_path=config_path,
            **kwargs
        )

        # Create merge strategy
        merge_strategy = ConfigurationFactory.create_merge_strategy(
            strategy_type=merge_strategy_type,
            **kwargs
        )

        # Create and return service
        service = ConfigurationService(
            repository=repository,
            merge_strategy=merge_strategy,
        )

        logger.info(
            f"Created ConfigurationService: "
            f"repository={repository_type}, strategy={merge_strategy_type}"
        )

        return service

    @staticmethod
    def create_test_service(
        merge_strategy_type: str = "default"
    ) -> ConfigurationService:
        """
        Create ConfigurationService for testing (in-memory storage)

        Args:
            merge_strategy_type: Type of merge strategy to use

        Returns:
            ConfigurationService with in-memory repository
        """
        return ConfigurationFactory.create_service(
            repository_type="memory",
            merge_strategy_type=merge_strategy_type
        )

    @staticmethod
    def create_yaml_service(
        config_path: str = "config",
        merge_strategy_type: str = "default"
    ) -> ConfigurationService:
        """
        Create ConfigurationService with YAML storage (convenience method)

        Args:
            config_path: Base path for YAML configuration files
            merge_strategy_type: Type of merge strategy to use

        Returns:
            ConfigurationService with YAML repository
        """
        return ConfigurationFactory.create_service(
            repository_type="yaml",
            merge_strategy_type=merge_strategy_type,
            config_path=config_path
        )


# =============================================================================
# Dependency Injection Helpers
# =============================================================================

_service_instance: Optional[ConfigurationService] = None


def get_configuration_service(
    repository_type: str = "yaml",
    merge_strategy_type: str = "default",
    config_path: str = "config",
    singleton: bool = True
) -> ConfigurationService:
    """
    Get or create ConfigurationService instance

    Provides singleton pattern by default for dependency injection.

    Args:
        repository_type: Type of repository
        merge_strategy_type: Type of merge strategy
        config_path: Base path for configuration files
        singleton: If True, return singleton instance

    Returns:
        ConfigurationService instance
    """
    global _service_instance

    if singleton and _service_instance is not None:
        return _service_instance

    service = ConfigurationFactory.create_service(
        repository_type=repository_type,
        merge_strategy_type=merge_strategy_type,
        config_path=config_path
    )

    if singleton:
        _service_instance = service

    return service


def reset_configuration_service() -> None:
    """
    Reset singleton instance (useful for testing)
    """
    global _service_instance
    _service_instance = None
