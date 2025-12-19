"""
Configuration V2 Interfaces

Defines abstract interfaces for the OOP configuration system following:
- Interface Segregation Principle (ISP)
- Dependency Inversion Principle (DIP)
- Open/Closed Principle (OCP)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class IConfigNode(ABC):
    """
    Interface for configuration nodes (Composite Pattern)

    All configuration entities implement this interface to enable
    hierarchical configuration structures with uniform access.

    SOLID: Interface Segregation - minimal interface for config nodes
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration node to dictionary representation

        Returns:
            Dictionary representation of configuration
        """
        pass

    @abstractmethod
    def validate(self) -> None:
        """
        Validate configuration node

        Raises:
            ValueError: If configuration is invalid
        """
        pass


class IConfigRepository(ABC):
    """
    Interface for configuration storage/retrieval (Repository Pattern)

    Abstracts the storage mechanism allowing different implementations:
    - YAML files
    - Database storage
    - Remote configuration service
    - In-memory cache

    SOLID: Dependency Inversion - depend on abstraction, not concrete storage
    """

    @abstractmethod
    def load(self, path: str) -> Dict[str, Any]:
        """
        Load configuration from storage

        Args:
            path: Configuration path/identifier

        Returns:
            Raw configuration dictionary

        Raises:
            FileNotFoundError: If configuration not found
            ValueError: If configuration format is invalid
        """
        pass

    @abstractmethod
    def save(self, path: str, config: Dict[str, Any]) -> None:
        """
        Save configuration to storage

        Args:
            path: Configuration path/identifier
            config: Configuration dictionary to save

        Raises:
            IOError: If save operation fails
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Check if configuration exists

        Args:
            path: Configuration path/identifier

        Returns:
            True if configuration exists
        """
        pass

    @abstractmethod
    def list_configs(self, pattern: Optional[str] = None) -> list[str]:
        """
        List available configurations

        Args:
            pattern: Optional filter pattern

        Returns:
            List of configuration identifiers
        """
        pass


class IMergeStrategy(ABC):
    """
    Interface for configuration merge strategies (Strategy Pattern)

    Defines how configurations are merged in the hierarchy:
    - DefaultMergeStrategy: Simple override merge
    - DeepMergeStrategy: Deep merge with nested updates
    - SelectiveMergeStrategy: Custom field-level merge rules

    SOLID: Open/Closed - open for extension (new strategies), closed for modification
    """

    @abstractmethod
    def merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any],
        merge_lists: bool = False
    ) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries

        Args:
            base: Base configuration (lower priority)
            override: Override configuration (higher priority)
            merge_lists: If True, merge list values; if False, override replaces

        Returns:
            Merged configuration dictionary

        Notes:
            - Override values take precedence over base values
            - None values in override are skipped (don't override)
            - Nested dictionaries are merged recursively
        """
        pass

    @abstractmethod
    def merge_multiple(
        self,
        configs: list[Dict[str, Any]],
        merge_lists: bool = False
    ) -> Dict[str, Any]:
        """
        Merge multiple configurations in order

        Args:
            configs: List of configurations (ascending priority)
            merge_lists: If True, merge list values

        Returns:
            Merged configuration dictionary
        """
        pass


class IConfigValidator(ABC):
    """
    Interface for configuration validation (Strategy Pattern)

    Allows different validation strategies:
    - SchemaValidator: JSON/YAML schema validation
    - BusinessRuleValidator: Custom business rules
    - CrossFieldValidator: Multi-field validation

    SOLID: Single Responsibility - validation logic separated from models
    """

    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If configuration is invalid with detailed message
        """
        pass

    @abstractmethod
    def get_validation_errors(self, config: Dict[str, Any]) -> list[str]:
        """
        Get list of validation errors without raising exception

        Args:
            config: Configuration dictionary to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        pass
