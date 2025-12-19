"""
Configuration V2 Repository - Repository Pattern Implementation

Provides abstraction over configuration storage mechanisms.

Design Pattern: Repository Pattern
- Abstracts storage mechanism (YAML, Database, Remote)
- Provides clean interface for CRUD operations
- Enables easy testing with mock implementations

SOLID: Dependency Inversion - depend on IConfigRepository interface
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from src.config.v2.interfaces import IConfigRepository


logger = logging.getLogger(__name__)


class YamlConfigRepository(IConfigRepository):
    """
    YAML file-based configuration repository

    Loads and saves configurations from/to YAML files.

    Example:
        repo = YamlConfigRepository(base_path="config/")
        config = repo.load("currencies.yaml")
        repo.save("currencies.yaml", config)
    """

    def __init__(self, base_path: str = "config"):
        """
        Initialize YAML repository

        Args:
            base_path: Base directory for configuration files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized YamlConfigRepository at {self.base_path.absolute()}")

    def load(self, path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Args:
            path: Relative path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        full_path = self.base_path / path
        logger.debug(f"Loading config from {full_path}")

        if not full_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {full_path}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                logger.warning(f"Empty configuration file: {full_path}")
                return {}

            logger.info(f"Successfully loaded config from {full_path}")
            return config

        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {full_path}: {e}")
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            logger.error(f"Failed to load config from {full_path}: {e}")
            raise

    def save(self, path: str, config: Dict[str, Any]) -> None:
        """
        Save configuration to YAML file

        Args:
            path: Relative path to configuration file
            config: Configuration dictionary

        Raises:
            IOError: If save operation fails
        """
        full_path = self.base_path / path
        logger.debug(f"Saving config to {full_path}")

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    config,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True
                )

            logger.info(f"Successfully saved config to {full_path}")

        except Exception as e:
            logger.error(f"Failed to save config to {full_path}: {e}")
            raise IOError(f"Failed to save configuration: {e}")

    def exists(self, path: str) -> bool:
        """
        Check if configuration file exists

        Args:
            path: Relative path to configuration file

        Returns:
            True if file exists
        """
        full_path = self.base_path / path
        return full_path.exists()

    def list_configs(self, pattern: Optional[str] = None) -> List[str]:
        """
        List configuration files

        Args:
            pattern: Optional glob pattern (e.g., "*.yaml")

        Returns:
            List of relative configuration file paths
        """
        if pattern:
            files = self.base_path.glob(pattern)
        else:
            files = self.base_path.glob("**/*.yaml")

        # Return relative paths as strings
        return [str(f.relative_to(self.base_path)) for f in files if f.is_file()]


class InMemoryConfigRepository(IConfigRepository):
    """
    In-memory configuration repository (for testing)

    Stores configurations in memory without file I/O.

    Example:
        repo = InMemoryConfigRepository()
        repo.save("test.yaml", {"key": "value"})
        config = repo.load("test.yaml")
    """

    def __init__(self):
        """Initialize in-memory storage"""
        self._storage: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized InMemoryConfigRepository")

    def load(self, path: str) -> Dict[str, Any]:
        """Load configuration from memory"""
        if path not in self._storage:
            raise FileNotFoundError(f"Configuration not found: {path}")

        # Return deep copy to prevent mutations
        return json.loads(json.dumps(self._storage[path]))

    def save(self, path: str, config: Dict[str, Any]) -> None:
        """Save configuration to memory"""
        # Store deep copy to prevent mutations
        self._storage[path] = json.loads(json.dumps(config))
        logger.debug(f"Saved config to memory: {path}")

    def exists(self, path: str) -> bool:
        """Check if configuration exists in memory"""
        return path in self._storage

    def list_configs(self, pattern: Optional[str] = None) -> List[str]:
        """List stored configurations"""
        if not pattern:
            return list(self._storage.keys())

        # Simple pattern matching (only supports * wildcard)
        import fnmatch
        return [key for key in self._storage.keys() if fnmatch.fnmatch(key, pattern)]

    def clear(self) -> None:
        """Clear all stored configurations (test utility)"""
        self._storage.clear()
        logger.debug("Cleared in-memory storage")


class DatabaseConfigRepository(IConfigRepository):
    """
    Database-based configuration repository (future implementation)

    Stores configurations in a database (PostgreSQL, MySQL, etc.)

    This is a placeholder for future enhancement.
    """

    def __init__(self, connection_string: str):
        """
        Initialize database repository

        Args:
            connection_string: Database connection string
        """
        self.connection_string = connection_string
        raise NotImplementedError("Database repository not yet implemented")

    def load(self, path: str) -> Dict[str, Any]:
        """Load configuration from database"""
        raise NotImplementedError("Database repository not yet implemented")

    def save(self, path: str, config: Dict[str, Any]) -> None:
        """Save configuration to database"""
        raise NotImplementedError("Database repository not yet implemented")

    def exists(self, path: str) -> bool:
        """Check if configuration exists in database"""
        raise NotImplementedError("Database repository not yet implemented")

    def list_configs(self, pattern: Optional[str] = None) -> List[str]:
        """List configurations from database"""
        raise NotImplementedError("Database repository not yet implemented")
