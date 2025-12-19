# TradingMTQ Enhancement Design Document (OOP Architecture)

**Created:** 2025-12-19
**Status:** Design Phase - Full OOP Implementation
**Version:** 2.0 (OOP-Focused)

---

## Executive Summary

This document outlines a **fully Object-Oriented design** for three major enhancements to TradingMTQ, following SOLID principles, design patterns, and clean architecture:

1. **Enhanced Configuration System** - OOP config hierarchy with strategy pattern
2. **Multi-Worker MT5 Architecture** - Process pool with OOP worker abstraction
3. **Trading Control Service** - Service layer with dependency injection

**OOP Principles Applied:**
- ✅ **Single Responsibility** - Each class has one reason to change
- ✅ **Open/Closed** - Open for extension, closed for modification
- ✅ **Liskov Substitution** - Interfaces and abstract base classes
- ✅ **Interface Segregation** - Small, focused interfaces
- ✅ **Dependency Inversion** - Depend on abstractions, not concretions

**Design Patterns Used:**
- Factory Pattern (configuration creation)
- Strategy Pattern (trading strategies)
- Builder Pattern (complex object construction)
- Observer Pattern (event notifications)
- Command Pattern (worker commands)
- Repository Pattern (data access)
- Service Layer (business logic)
- Dependency Injection (loose coupling)

---

## Table of Contents

1. [Enhancement 1: OOP Configuration System](#enhancement-1-oop-configuration-system)
2. [Enhancement 2: OOP Multi-Worker Architecture](#enhancement-2-oop-multi-worker-architecture)
3. [Enhancement 3: OOP Trading Control Service](#enhancement-3-oop-trading-control-service)
4. [Class Diagrams](#class-diagrams)
5. [Implementation Plan](#implementation-plan)

---

# Enhancement 1: OOP Configuration System

## Design Principles

### 1. Configuration Hierarchy (Composite Pattern)

```python
# src/config/models/base.py

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from dataclasses import dataclass, field


class IConfigNode(ABC):
    """
    Interface for configuration nodes.
    Allows composite structure (nodes can contain other nodes).
    """

    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        pass

    @abstractmethod
    def merge(self, other: 'IConfigNode') -> 'IConfigNode':
        """Merge this node with another node."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate configuration."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        pass


class ConfigNode(IConfigNode):
    """
    Base implementation of configuration node.
    Supports hierarchical structure and value inheritance.
    """

    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self._parent: Optional[IConfigNode] = None

    def set_parent(self, parent: IConfigNode) -> None:
        """Set parent node for inheritance."""
        self._parent = parent

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get value with fallback to parent."""
        if key in self._data:
            return self._data[key]
        elif self._parent:
            return self._parent.get_value(key, default)
        return default

    def merge(self, other: IConfigNode) -> IConfigNode:
        """Merge with another node (child overrides parent)."""
        merged_data = self._data.copy()
        merged_data.update(other.to_dict())
        return ConfigNode(merged_data)

    def validate(self) -> bool:
        """Base validation (override in subclasses)."""
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._data.copy()
```

### 2. Typed Configuration Models (Value Objects)

```python
# src/config/models/execution.py

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExecutionConfig:
    """
    Value object for execution configuration.
    Immutable to prevent accidental modification.
    """
    interval_seconds: int
    parallel_execution: bool
    max_workers: int
    use_intelligent_position_manager: bool
    use_ml_enhancement: bool
    use_sentiment_filter: bool

    def __post_init__(self):
        """Validate on creation."""
        if self.interval_seconds < 1:
            raise ValueError("interval_seconds must be positive")
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionConfig':
        """Factory method to create from dictionary."""
        return cls(
            interval_seconds=data.get('interval_seconds', 30),
            parallel_execution=data.get('parallel_execution', False),
            max_workers=data.get('max_workers', 3),
            use_intelligent_position_manager=data.get('use_intelligent_position_manager', True),
            use_ml_enhancement=data.get('use_ml_enhancement', True),
            use_sentiment_filter=data.get('use_sentiment_filter', True)
        )

    def with_interval(self, interval: int) -> 'ExecutionConfig':
        """Create new instance with modified interval (immutable pattern)."""
        return ExecutionConfig(
            interval_seconds=interval,
            parallel_execution=self.parallel_execution,
            max_workers=self.max_workers,
            use_intelligent_position_manager=self.use_intelligent_position_manager,
            use_ml_enhancement=self.use_ml_enhancement,
            use_sentiment_filter=self.use_sentiment_filter
        )


@dataclass(frozen=True)
class RiskConfig:
    """Value object for risk configuration."""
    portfolio_risk_percent: float
    max_concurrent_trades: int
    default_risk_percent: float
    max_position_size: float
    min_position_size: float

    def __post_init__(self):
        if self.portfolio_risk_percent <= 0:
            raise ValueError("portfolio_risk_percent must be positive")
        if self.max_position_size < self.min_position_size:
            raise ValueError("max_position_size must be >= min_position_size")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskConfig':
        return cls(
            portfolio_risk_percent=data.get('portfolio_risk_percent', 8.0),
            max_concurrent_trades=data.get('max_concurrent_trades', 15),
            default_risk_percent=data.get('default_risk_percent', 0.5),
            max_position_size=data.get('max_position_size', 1.0),
            min_position_size=data.get('min_position_size', 0.01)
        )


@dataclass(frozen=True)
class StrategyConfig:
    """Value object for strategy configuration."""
    type: str
    timeframe: str
    fast_period: int
    slow_period: int
    sl_pips: int
    tp_pips: int

    def __post_init__(self):
        if self.type not in ('position', 'crossover'):
            raise ValueError(f"Invalid strategy type: {self.type}")
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be < slow_period")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyConfig':
        return cls(
            type=data.get('type', 'position'),
            timeframe=data.get('timeframe', 'M5'),
            fast_period=data.get('fast_period', 10),
            slow_period=data.get('slow_period', 20),
            sl_pips=data.get('sl_pips', 20),
            tp_pips=data.get('tp_pips', 40)
        )


@dataclass(frozen=True)
class TradingRulesConfig:
    """Value object for trading rules."""
    cooldown_seconds: int
    trade_on_signal_change: bool
    min_signal_confidence: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingRulesConfig':
        return cls(
            cooldown_seconds=data.get('cooldown_seconds', 120),
            trade_on_signal_change=data.get('trade_on_signal_change', False),
            min_signal_confidence=data.get('min_signal_confidence', 0.5)
        )
```

### 3. Configuration Builder (Builder Pattern)

```python
# src/config/builders/account_config_builder.py

from typing import Optional, List
from src.config.models.execution import ExecutionConfig, RiskConfig, StrategyConfig
from src.config.models.account import AccountConfig, CurrencyConfig


class AccountConfigBuilder:
    """
    Builder for constructing AccountConfig with fluent interface.
    Ensures valid configuration state.
    """

    def __init__(self, name: str):
        self._name = name
        self._risk: Optional[RiskConfig] = None
        self._execution: Optional[ExecutionConfig] = None
        self._strategy: Optional[StrategyConfig] = None
        self._trading_rules: Optional[TradingRulesConfig] = None
        self._currencies: List[CurrencyConfig] = []

    def with_risk(self, risk: RiskConfig) -> 'AccountConfigBuilder':
        """Set risk configuration."""
        self._risk = risk
        return self

    def with_execution(self, execution: ExecutionConfig) -> 'AccountConfigBuilder':
        """Set execution configuration."""
        self._execution = execution
        return self

    def with_strategy(self, strategy: StrategyConfig) -> 'AccountConfigBuilder':
        """Set strategy configuration."""
        self._strategy = strategy
        return self

    def with_trading_rules(self, rules: TradingRulesConfig) -> 'AccountConfigBuilder':
        """Set trading rules."""
        self._trading_rules = rules
        return self

    def add_currency(self, currency: CurrencyConfig) -> 'AccountConfigBuilder':
        """Add currency configuration."""
        self._currencies.append(currency)
        return self

    def add_currencies(self, currencies: List[CurrencyConfig]) -> 'AccountConfigBuilder':
        """Add multiple currencies."""
        self._currencies.extend(currencies)
        return self

    def build(self) -> 'AccountConfig':
        """Build the final AccountConfig."""
        return AccountConfig(
            name=self._name,
            risk=self._risk,
            execution=self._execution,
            strategy=self._strategy,
            trading_rules=self._trading_rules,
            currencies=self._currencies
        )

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'AccountConfig':
        """Convenience method to build from dictionary."""
        builder = cls(name)

        if 'risk' in data:
            builder.with_risk(RiskConfig.from_dict(data['risk']))

        if 'execution' in data:
            builder.with_execution(ExecutionConfig.from_dict(data['execution']))

        if 'strategy' in data:
            builder.with_strategy(StrategyConfig.from_dict(data['strategy']))

        if 'trading_rules' in data:
            builder.with_trading_rules(TradingRulesConfig.from_dict(data['trading_rules']))

        if 'currencies' in data:
            currencies = [
                CurrencyConfig.from_dict(c) for c in data['currencies']
            ]
            builder.add_currencies(currencies)

        return builder.build()
```

### 4. Configuration Repository (Repository Pattern)

```python
# src/config/repositories/config_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List
from pathlib import Path
import yaml


class IConfigRepository(ABC):
    """
    Interface for configuration storage.
    Abstracts away storage mechanism (file, database, remote).
    """

    @abstractmethod
    def load(self, path: str) -> Dict[str, Any]:
        """Load configuration from storage."""
        pass

    @abstractmethod
    def save(self, path: str, config: Dict[str, Any]) -> None:
        """Save configuration to storage."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if configuration exists."""
        pass


class YamlConfigRepository(IConfigRepository):
    """
    YAML file-based configuration repository.
    """

    def __init__(self, base_path: Optional[Path] = None):
        self._base_path = base_path or Path("config")

    def load(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        full_path = self._base_path / path

        if not full_path.exists():
            raise FileNotFoundError(f"Config file not found: {full_path}")

        with open(full_path, 'r') as f:
            return yaml.safe_load(f)

    def save(self, path: str, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file."""
        full_path = self._base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    def exists(self, path: str) -> bool:
        """Check if configuration file exists."""
        return (self._base_path / path).exists()


class DatabaseConfigRepository(IConfigRepository):
    """
    Database-based configuration repository (for future use).
    """

    def __init__(self, db_session):
        self._db = db_session

    def load(self, path: str) -> Dict[str, Any]:
        """Load configuration from database."""
        # TODO: Implement database loading
        raise NotImplementedError()

    def save(self, path: str, config: Dict[str, Any]) -> None:
        """Save configuration to database."""
        # TODO: Implement database saving
        raise NotImplementedError()

    def exists(self, path: str) -> bool:
        """Check if configuration exists in database."""
        # TODO: Implement check
        raise NotImplementedError()
```

### 5. Configuration Service (Service Layer)

```python
# src/config/services/configuration_service.py

from typing import Optional, Dict, Any, List
from src.config.repositories.config_repository import IConfigRepository
from src.config.builders.account_config_builder import AccountConfigBuilder
from src.config.models.account import AccountConfig
from src.config.models.defaults import DefaultsConfig
from src.config.strategies.merge_strategy import IMergeStrategy, DefaultMergeStrategy


class ConfigurationService:
    """
    Service for managing configuration with business logic.
    Coordinates repositories, builders, and merge strategies.

    Single Responsibility: Configuration management
    Open/Closed: Extensible via strategy injection
    Dependency Inversion: Depends on abstractions (IConfigRepository, IMergeStrategy)
    """

    def __init__(
        self,
        repository: IConfigRepository,
        merge_strategy: Optional[IMergeStrategy] = None
    ):
        self._repository = repository
        self._merge_strategy = merge_strategy or DefaultMergeStrategy()
        self._defaults: Optional[DefaultsConfig] = None
        self._accounts: Dict[str, AccountConfig] = {}
        self._version: str = "2.0"

    def load_configuration(self, config_path: str = "trading_config.yaml") -> None:
        """
        Load configuration from repository.

        Args:
            config_path: Path to configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        # Load raw configuration
        raw_config = self._repository.load(config_path)

        # Validate version
        version = raw_config.get('version', '1.0')
        if version != '2.0':
            raise ValueError(f"Unsupported config version: {version}")

        # Parse defaults
        if 'defaults' in raw_config:
            self._defaults = DefaultsConfig.from_dict(raw_config['defaults'])

        # Parse accounts
        if 'accounts' in raw_config:
            for account_name, account_data in raw_config['accounts'].items():
                account_config = AccountConfigBuilder.from_dict(
                    account_name,
                    account_data
                )
                self._accounts[account_name] = account_config

    def get_account_config(
        self,
        account_name: str,
        resolve_inheritance: bool = True
    ) -> AccountConfig:
        """
        Get configuration for specific account.

        Args:
            account_name: Account profile name
            resolve_inheritance: If True, merge with defaults

        Returns:
            Fully resolved AccountConfig

        Raises:
            ValueError: If account not found
        """
        if account_name not in self._accounts:
            raise ValueError(f"Account profile '{account_name}' not found")

        account_config = self._accounts[account_name]

        if resolve_inheritance and self._defaults:
            # Use merge strategy to combine defaults + account config
            return self._merge_strategy.merge_account_with_defaults(
                account_config,
                self._defaults
            )

        return account_config

    def get_currency_config(
        self,
        account_name: str,
        symbol: str
    ) -> 'CurrencyConfig':
        """
        Get fully resolved configuration for a currency.

        Merges: defaults → account → currency

        Args:
            account_name: Account profile name
            symbol: Currency symbol

        Returns:
            Resolved CurrencyConfig

        Raises:
            ValueError: If account or currency not found
        """
        account_config = self.get_account_config(account_name, resolve_inheritance=True)

        # Find currency in account
        currency = next(
            (c for c in account_config.currencies if c.symbol == symbol),
            None
        )

        if not currency:
            raise ValueError(f"Currency {symbol} not found in account {account_name}")

        # Merge with account defaults
        return self._merge_strategy.merge_currency_with_account(
            currency,
            account_config
        )

    def list_accounts(self) -> List[str]:
        """List all configured account profiles."""
        return list(self._accounts.keys())

    def list_currencies(
        self,
        account_name: str,
        enabled_only: bool = True
    ) -> List[str]:
        """List currencies for an account."""
        account = self._accounts.get(account_name)
        if not account:
            return []

        currencies = account.currencies
        if enabled_only:
            currencies = [c for c in currencies if c.enabled]

        return [c.symbol for c in currencies]

    def validate_configuration(self) -> List[str]:
        """
        Validate entire configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate defaults
        if self._defaults and not self._defaults.validate():
            errors.append("Invalid defaults configuration")

        # Validate each account
        for account_name, account_config in self._accounts.items():
            if not account_config.validate():
                errors.append(f"Invalid configuration for account: {account_name}")

        return errors

    def reload(self, config_path: str = "trading_config.yaml") -> bool:
        """
        Reload configuration from repository.

        Returns:
            True if reload successful
        """
        try:
            self.load_configuration(config_path)
            return True
        except Exception as e:
            # Log error but don't crash
            # TODO: Add proper logging
            return False
```

### 6. Merge Strategy (Strategy Pattern)

```python
# src/config/strategies/merge_strategy.py

from abc import ABC, abstractmethod
from src.config.models.account import AccountConfig, CurrencyConfig
from src.config.models.defaults import DefaultsConfig


class IMergeStrategy(ABC):
    """
    Interface for configuration merge strategies.
    Allows different merge algorithms (deep merge, shallow merge, etc.)
    """

    @abstractmethod
    def merge_account_with_defaults(
        self,
        account: AccountConfig,
        defaults: DefaultsConfig
    ) -> AccountConfig:
        """Merge account config with defaults."""
        pass

    @abstractmethod
    def merge_currency_with_account(
        self,
        currency: CurrencyConfig,
        account: AccountConfig
    ) -> CurrencyConfig:
        """Merge currency config with account defaults."""
        pass


class DefaultMergeStrategy(IMergeStrategy):
    """
    Default merge strategy: child overrides parent.
    Deep merge for nested objects.
    """

    def merge_account_with_defaults(
        self,
        account: AccountConfig,
        defaults: DefaultsConfig
    ) -> AccountConfig:
        """
        Merge account with defaults.
        Account values override defaults.
        """
        return AccountConfig(
            name=account.name,
            risk=account.risk or defaults.risk,
            execution=account.execution or defaults.execution,
            strategy=account.strategy or defaults.strategy,
            trading_rules=account.trading_rules or defaults.trading_rules,
            position_management=account.position_management or defaults.position_management,
            trading_hours=account.trading_hours or defaults.trading_hours,
            currencies=account.currencies
        )

    def merge_currency_with_account(
        self,
        currency: CurrencyConfig,
        account: AccountConfig
    ) -> CurrencyConfig:
        """
        Merge currency with account defaults.
        Currency values override account values.
        """
        return CurrencyConfig(
            symbol=currency.symbol,
            enabled=currency.enabled,
            risk_percent=currency.risk_percent if currency.risk_percent is not None else account.risk.default_risk_percent,
            strategy=currency.strategy or account.strategy,
            trading_hours=currency.trading_hours or account.trading_hours,
            # ... merge other fields
        )
```

### 7. Configuration Factory (Factory Pattern)

```python
# src/config/factories/configuration_factory.py

from typing import Optional
from src.config.services.configuration_service import ConfigurationService
from src.config.repositories.config_repository import (
    IConfigRepository,
    YamlConfigRepository,
    DatabaseConfigRepository
)
from src.config.strategies.merge_strategy import IMergeStrategy, DefaultMergeStrategy


class ConfigurationFactory:
    """
    Factory for creating ConfigurationService instances.
    Encapsulates creation logic and dependency wiring.
    """

    @staticmethod
    def create_yaml_based(
        config_path: str = "trading_config.yaml",
        merge_strategy: Optional[IMergeStrategy] = None
    ) -> ConfigurationService:
        """
        Create YAML-based configuration service.

        Args:
            config_path: Path to YAML config file
            merge_strategy: Custom merge strategy (optional)

        Returns:
            Configured ConfigurationService instance
        """
        repository = YamlConfigRepository()
        strategy = merge_strategy or DefaultMergeStrategy()

        service = ConfigurationService(repository, strategy)
        service.load_configuration(config_path)

        return service

    @staticmethod
    def create_database_based(
        db_session,
        merge_strategy: Optional[IMergeStrategy] = None
    ) -> ConfigurationService:
        """
        Create database-based configuration service.

        Args:
            db_session: Database session
            merge_strategy: Custom merge strategy (optional)

        Returns:
            Configured ConfigurationService instance
        """
        repository = DatabaseConfigRepository(db_session)
        strategy = merge_strategy or DefaultMergeStrategy()

        return ConfigurationService(repository, strategy)

    @staticmethod
    def create_with_auto_detection(
        config_path: str = "trading_config.yaml",
        db_session=None
    ) -> ConfigurationService:
        """
        Auto-detect configuration source and create appropriate service.

        Priority: Database > YAML file

        Args:
            config_path: Path to YAML config
            db_session: Database session (optional)

        Returns:
            Configured ConfigurationService instance
        """
        if db_session:
            # Try database first
            try:
                return ConfigurationFactory.create_database_based(db_session)
            except:
                pass

        # Fall back to YAML
        return ConfigurationFactory.create_yaml_based(config_path)
```

---

# Enhancement 2: OOP Multi-Worker Architecture

## Design Principles

### 1. Worker Abstraction (Abstract Base Class)

```python
# src/workers/abstractions/base_worker.py

from abc import ABC, abstractmethod
from multiprocessing import Process, Queue
from typing import Dict, Any, Optional
from enum import Enum


class WorkerState(Enum):
    """Worker lifecycle states."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class IWorker(ABC):
    """
    Interface for worker processes.
    Defines contract for all worker implementations.

    Open/Closed: Open for extension (new worker types), closed for modification
    """

    @abstractmethod
    def start(self) -> bool:
        """Start the worker process."""
        pass

    @abstractmethod
    def stop(self, timeout: float = 10.0) -> bool:
        """Stop the worker process gracefully."""
        pass

    @abstractmethod
    def send_command(self, command: 'ICommand') -> bool:
        """Send command to worker."""
        pass

    @abstractmethod
    def get_state(self) -> WorkerState:
        """Get current worker state."""
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """Check if worker process is alive."""
        pass


class BaseWorker(Process, IWorker):
    """
    Base class for worker processes.
    Implements common worker functionality.

    Template Method Pattern: run() defines skeleton, subclasses implement details
    """

    def __init__(
        self,
        worker_id: str,
        command_queue: Queue,
        result_queue: Queue
    ):
        super().__init__(name=f"Worker-{worker_id}")
        self._worker_id = worker_id
        self._command_queue = command_queue
        self._result_queue = result_queue
        self._state = WorkerState.IDLE
        self._is_running = False

    # Template method
    def run(self) -> None:
        """
        Main worker loop (template method).
        Subclasses override hook methods.
        """
        try:
            self._state = WorkerState.STARTING
            self._on_start()
            self._state = WorkerState.RUNNING

            self._is_running = True
            while self._is_running:
                self._process_commands()
                self._on_idle()

        except Exception as e:
            self._state = WorkerState.ERROR
            self._on_error(e)
        finally:
            self._on_stop()
            self._state = WorkerState.STOPPED

    # Hook methods (to be overridden)
    @abstractmethod
    def _on_start(self) -> None:
        """Called when worker starts."""
        pass

    @abstractmethod
    def _on_stop(self) -> None:
        """Called when worker stops."""
        pass

    @abstractmethod
    def _on_command(self, command: 'ICommand') -> None:
        """Called when command is received."""
        pass

    def _on_error(self, error: Exception) -> None:
        """Called when error occurs."""
        self._result_queue.put({
            'type': 'error',
            'worker_id': self._worker_id,
            'error': str(error)
        })

    def _on_idle(self) -> None:
        """Called during idle time (default: do nothing)."""
        pass

    # Command processing
    def _process_commands(self) -> None:
        """Process commands from queue."""
        try:
            if not self._command_queue.empty():
                command = self._command_queue.get(timeout=0.1)
                self._on_command(command)
        except Empty:
            pass

    # IWorker implementation
    def send_command(self, command: 'ICommand') -> bool:
        """Send command to worker."""
        try:
            self._command_queue.put(command.to_dict())
            return True
        except Exception:
            return False

    def get_state(self) -> WorkerState:
        """Get current state."""
        return self._state

    def is_alive(self) -> bool:
        """Check if process is alive."""
        return super().is_alive()
```

### 2. Command Pattern for Worker Commands

```python
# src/workers/commands/base_command.py

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass


class ICommand(ABC):
    """
    Interface for worker commands.
    Command Pattern: Encapsulates request as object.
    """

    @abstractmethod
    def get_type(self) -> str:
        """Get command type identifier."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for IPC."""
        pass

    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ICommand':
        """Create command from dictionary."""
        pass


@dataclass
class ExecuteTradingCycleCommand(ICommand):
    """Command to execute one trading cycle."""

    def get_type(self) -> str:
        return "execute_cycle"

    def to_dict(self) -> Dict[str, Any]:
        return {'type': self.get_type()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecuteTradingCycleCommand':
        return cls()


@dataclass
class StartTradingCommand(ICommand):
    """Command to start automated trading."""

    def get_type(self) -> str:
        return "start_trading"

    def to_dict(self) -> Dict[str, Any]:
        return {'type': self.get_type()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StartTradingCommand':
        return cls()


@dataclass
class StopTradingCommand(ICommand):
    """Command to stop automated trading."""

    def get_type(self) -> str:
        return "stop_trading"

    def to_dict(self) -> Dict[str, Any]:
        return {'type': self.get_type()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StopTradingCommand':
        return cls()


@dataclass
class GetStatusCommand(ICommand):
    """Command to get worker status."""

    def get_type(self) -> str:
        return "get_status"

    def to_dict(self) -> Dict[str, Any]:
        return {'type': self.get_type()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GetStatusCommand':
        return cls()


@dataclass
class ShutdownCommand(ICommand):
    """Command to shutdown worker."""

    def get_type(self) -> str:
        return "shutdown"

    def to_dict(self) -> Dict[str, Any]:
        return {'type': self.get_type()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShutdownCommand':
        return cls()


class CommandFactory:
    """
    Factory for creating commands from dictionary.
    """

    _command_registry: Dict[str, type] = {
        'execute_cycle': ExecuteTradingCycleCommand,
        'start_trading': StartTradingCommand,
        'stop_trading': StopTradingCommand,
        'get_status': GetStatusCommand,
        'shutdown': ShutdownCommand
    }

    @classmethod
    def create_command(cls, data: Dict[str, Any]) -> ICommand:
        """Create command from dictionary."""
        cmd_type = data.get('type')
        if cmd_type not in cls._command_registry:
            raise ValueError(f"Unknown command type: {cmd_type}")

        command_class = cls._command_registry[cmd_type]
        return command_class.from_dict(data)

    @classmethod
    def register_command(cls, cmd_type: str, command_class: type) -> None:
        """Register new command type."""
        cls._command_registry[cmd_type] = command_class
```

### 3. MT5 Worker Implementation

```python
# src/workers/mt5_worker.py

from typing import Optional, Dict, Any
from datetime import datetime

from src.workers.abstractions.base_worker import BaseWorker, WorkerState
from src.workers.commands.base_command import ICommand, CommandFactory
from src.connectors.mt5_connector import MT5Connector
from src.trading.orchestrator import MultiCurrencyOrchestrator
from src.config.services.configuration_service import ConfigurationService


class MT5Worker(BaseWorker):
    """
    Worker process for isolated MT5 trading account.

    Single Responsibility: Manage one MT5 account
    Dependency Inversion: Depends on abstractions (ICommand, ConfigurationService)
    """

    def __init__(
        self,
        account_id: int,
        account_number: int,
        credentials: 'AccountCredentials',
        config_service: ConfigurationService,
        command_queue: Queue,
        result_queue: Queue
    ):
        super().__init__(
            worker_id=f"account_{account_id}",
            command_queue=command_queue,
            result_queue=result_queue
        )
        self._account_id = account_id
        self._account_number = account_number
        self._credentials = credentials
        self._config_service = config_service

        self._connector: Optional[MT5Connector] = None
        self._orchestrator: Optional[MultiCurrencyOrchestrator] = None
        self._trading_active = False

    # Template method hooks
    def _on_start(self) -> None:
        """Initialize MT5 connection and orchestrator."""
        # Create connector
        self._connector = MT5Connector(
            instance_id=f"worker_{self._account_id}"
        )

        # Connect to MT5
        success = self._connector.connect(
            login=self._credentials.login,
            password=self._credentials.password,
            server=self._credentials.server,
            timeout=60000
        )

        if not success:
            raise Exception(f"Failed to connect MT5 for account {self._account_id}")

        # Get configuration
        account_config = self._config_service.get_account_config("default")

        # Create orchestrator
        self._orchestrator = MultiCurrencyOrchestrator(
            connector=self._connector,
            max_concurrent_trades=account_config.risk.max_concurrent_trades,
            portfolio_risk_percent=account_config.risk.portfolio_risk_percent,
            use_intelligent_manager=account_config.execution.use_intelligent_position_manager
        )

        # Add currencies
        for currency_config in account_config.currencies:
            if currency_config.enabled:
                # TODO: Create and add currency trader
                pass

        # Send ready signal
        self._result_queue.put({
            'type': 'worker_ready',
            'worker_id': self._worker_id,
            'account_id': self._account_id,
            'timestamp': datetime.now().isoformat()
        })

    def _on_stop(self) -> None:
        """Cleanup resources."""
        if self._connector:
            try:
                self._connector.disconnect()
            except Exception as e:
                # Log error but continue cleanup
                pass

    def _on_command(self, command_data: Dict[str, Any]) -> None:
        """Handle commands using Command Pattern."""
        try:
            command = CommandFactory.create_command(command_data)

            # Dispatch based on command type
            if isinstance(command, ExecuteTradingCycleCommand):
                self._handle_execute_cycle()

            elif isinstance(command, StartTradingCommand):
                self._handle_start_trading()

            elif isinstance(command, StopTradingCommand):
                self._handle_stop_trading()

            elif isinstance(command, GetStatusCommand):
                self._handle_get_status()

            elif isinstance(command, ShutdownCommand):
                self._handle_shutdown()

        except Exception as e:
            self._result_queue.put({
                'type': 'command_error',
                'worker_id': self._worker_id,
                'error': str(e)
            })

    def _on_idle(self) -> None:
        """Periodic tasks during idle."""
        # Check connection health
        if self._connector and not self._connector.is_connected():
            try:
                self._connector.reconnect()
            except Exception as e:
                pass

    # Command handlers
    def _handle_execute_cycle(self) -> None:
        """Execute one trading cycle."""
        if not self._orchestrator:
            return

        try:
            results = self._orchestrator.process_single_cycle()

            self._result_queue.put({
                'type': 'cycle_complete',
                'worker_id': self._worker_id,
                'account_id': self._account_id,
                'results': results,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            self._result_queue.put({
                'type': 'cycle_error',
                'worker_id': self._worker_id,
                'account_id': self._account_id,
                'error': str(e)
            })

    def _handle_start_trading(self) -> None:
        """Start automated trading."""
        self._trading_active = True
        self._result_queue.put({
            'type': 'trading_started',
            'worker_id': self._worker_id,
            'account_id': self._account_id
        })

    def _handle_stop_trading(self) -> None:
        """Stop automated trading."""
        self._trading_active = False
        self._result_queue.put({
            'type': 'trading_stopped',
            'worker_id': self._worker_id,
            'account_id': self._account_id
        })

    def _handle_get_status(self) -> None:
        """Send status update."""
        status = {
            'type': 'status_update',
            'worker_id': self._worker_id,
            'account_id': self._account_id,
            'state': self._state.value,
            'trading_active': self._trading_active,
            'connected': self._connector.is_connected() if self._connector else False,
            'active_traders': len(self._orchestrator.traders) if self._orchestrator else 0
        }
        self._result_queue.put(status)

    def _handle_shutdown(self) -> None:
        """Shutdown worker."""
        self._is_running = False
```

### 4. Worker Pool Manager (Facade + Factory)

```python
# src/workers/managers/worker_pool_manager.py

from typing import Dict, Optional, List
from multiprocessing import Queue
import asyncio
from datetime import datetime

from src.workers.mt5_worker import MT5Worker
from src.workers.commands.base_command import *
from src.workers.abstractions.base_worker import IWorker, WorkerState
from src.config.services.configuration_service import ConfigurationService
from src.database.models import TradingAccount


class WorkerHandle:
    """
    Handle for managing a worker.
    Encapsulates worker reference and communication queues.
    """

    def __init__(
        self,
        worker: IWorker,
        command_queue: Queue,
        account_id: int
    ):
        self.worker = worker
        self.command_queue = command_queue
        self.account_id = account_id
        self.created_at = datetime.now()

    def is_alive(self) -> bool:
        """Check if worker is alive."""
        return self.worker.is_alive()

    def send_command(self, command: ICommand) -> bool:
        """Send command to worker."""
        return self.worker.send_command(command)


class WorkerPoolManager:
    """
    Facade for worker pool operations.
    Provides simple interface for complex worker management.

    Facade Pattern: Simplifies complex subsystem (workers, queues, commands)
    Factory Pattern: Creates workers
    """

    def __init__(self, config_service: ConfigurationService):
        self._config_service = config_service
        self._workers: Dict[int, WorkerHandle] = {}  # account_id -> handle
        self._result_queue = Queue()  # Shared result queue
        self._result_reader_task: Optional[asyncio.Task] = None
        self._observers: List['IWorkerObserver'] = []  # Observer pattern

    async def start_worker(
        self,
        account: TradingAccount
    ) -> bool:
        """
        Start worker for account.

        Factory method: Creates appropriate worker type.

        Args:
            account: Trading account

        Returns:
            True if started successfully
        """
        account_id = account.id

        # Check if already exists
        if account_id in self._workers:
            return False

        # Create command queue
        command_queue = Queue()

        # Create credentials value object
        credentials = AccountCredentials(
            login=account.login,
            password=account.password_encrypted,  # TODO: Decrypt
            server=account.server
        )

        # Create worker
        worker = MT5Worker(
            account_id=account_id,
            account_number=account.account_number,
            credentials=credentials,
            config_service=self._config_service,
            command_queue=command_queue,
            result_queue=self._result_queue
        )

        # Start worker process
        worker.start()

        # Store handle
        handle = WorkerHandle(worker, command_queue, account_id)
        self._workers[account_id] = handle

        # Wait for ready signal
        ready = await self._wait_for_worker_ready(account_id, timeout=30.0)

        if ready:
            # Notify observers
            self._notify_observers('worker_started', account_id)
            return True
        else:
            await self.stop_worker(account_id)
            return False

    async def stop_worker(self, account_id: int) -> bool:
        """
        Stop worker for account.

        Args:
            account_id: Account ID

        Returns:
            True if stopped successfully
        """
        if account_id not in self._workers:
            return False

        handle = self._workers[account_id]

        # Send shutdown command
        handle.send_command(ShutdownCommand())

        # Wait for termination
        handle.worker.join(timeout=10.0)

        if handle.is_alive():
            # Force terminate
            handle.worker.terminate()
            handle.worker.join(timeout=5.0)

        # Remove handle
        del self._workers[account_id]

        # Notify observers
        self._notify_observers('worker_stopped', account_id)

        return True

    async def execute_trading_cycle(self, account_id: int) -> bool:
        """Execute trading cycle for account."""
        if account_id not in self._workers:
            return False

        handle = self._workers[account_id]
        return handle.send_command(ExecuteTradingCycleCommand())

    async def start_trading(self, account_id: int) -> bool:
        """Start automated trading for account."""
        if account_id not in self._workers:
            return False

        handle = self._workers[account_id]
        return handle.send_command(StartTradingCommand())

    async def stop_trading(self, account_id: int) -> bool:
        """Stop automated trading for account."""
        if account_id not in self._workers:
            return False

        handle = self._workers[account_id]
        return handle.send_command(StopTradingCommand())

    async def get_worker_status(self, account_id: int) -> Optional[Dict]:
        """Get status from worker."""
        if account_id not in self._workers:
            return None

        handle = self._workers[account_id]
        handle.send_command(GetStatusCommand())

        # TODO: Wait for response with timeout
        return None

    def list_active_workers(self) -> List[int]:
        """List account IDs with active workers."""
        return [
            account_id
            for account_id, handle in self._workers.items()
            if handle.is_alive()
        ]

    # Observer pattern
    def add_observer(self, observer: 'IWorkerObserver') -> None:
        """Add observer for worker events."""
        self._observers.append(observer)

    def remove_observer(self, observer: 'IWorkerObserver') -> None:
        """Remove observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, event_type: str, account_id: int) -> None:
        """Notify all observers of event."""
        for observer in self._observers:
            observer.on_worker_event(event_type, account_id)

    # Result reader
    async def start_result_reader(self):
        """Start background task to read results."""
        if self._result_reader_task:
            return

        self._result_reader_task = asyncio.create_task(self._read_results())

    async def _read_results(self):
        """Read results from shared queue."""
        while True:
            try:
                if not self._result_queue.empty():
                    result = self._result_queue.get_nowait()
                    await self._handle_result(result)

                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error
                pass

    async def _handle_result(self, result: Dict[str, Any]):
        """Handle result from worker."""
        result_type = result.get('type')
        account_id = result.get('account_id')

        # Notify observers
        for observer in self._observers:
            observer.on_worker_result(result_type, account_id, result)

    async def _wait_for_worker_ready(
        self,
        account_id: int,
        timeout: float
    ) -> bool:
        """Wait for worker ready signal."""
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if not self._result_queue.empty():
                result = self._result_queue.get_nowait()
                if (result.get('type') == 'worker_ready' and
                    result.get('account_id') == account_id):
                    return True

            await asyncio.sleep(0.1)

        return False

    async def stop_all_workers(self):
        """Stop all workers."""
        account_ids = list(self._workers.keys())
        for account_id in account_ids:
            await self.stop_worker(account_id)

        if self._result_reader_task:
            self._result_reader_task.cancel()
            try:
                await self._result_reader_task
            except asyncio.CancelledError:
                pass
```

### 5. Observer Interface for Worker Events

```python
# src/workers/observers/worker_observer.py

from abc import ABC, abstractmethod
from typing import Dict, Any


class IWorkerObserver(ABC):
    """
    Observer interface for worker events.
    Observer Pattern: Allows loose coupling between workers and event handlers.
    """

    @abstractmethod
    def on_worker_event(self, event_type: str, account_id: int) -> None:
        """Called when worker event occurs (started, stopped, etc.)."""
        pass

    @abstractmethod
    def on_worker_result(self, result_type: str, account_id: int, result: Dict[str, Any]) -> None:
        """Called when worker sends result."""
        pass


class WebSocketObserver(IWorkerObserver):
    """
    Observer that broadcasts worker events via WebSocket.
    """

    def __init__(self, connection_manager: 'ConnectionManager'):
        self._connection_manager = connection_manager

    def on_worker_event(self, event_type: str, account_id: int) -> None:
        """Broadcast event to WebSocket clients."""
        asyncio.create_task(
            self._connection_manager.broadcast({
                'type': 'worker_event',
                'event': event_type,
                'account_id': account_id
            })
        )

    def on_worker_result(self, result_type: str, account_id: int, result: Dict[str, Any]) -> None:
        """Broadcast result to WebSocket clients."""
        asyncio.create_task(
            self._connection_manager.broadcast({
                'type': 'worker_result',
                'result_type': result_type,
                'account_id': account_id,
                'data': result
            })
        )


class DatabaseObserver(IWorkerObserver):
    """
    Observer that persists worker events to database.
    """

    def __init__(self, db_session):
        self._db = db_session

    def on_worker_event(self, event_type: str, account_id: int) -> None:
        """Save event to database."""
        # TODO: Implement database persistence
        pass

    def on_worker_result(self, result_type: str, account_id: int, result: Dict[str, Any]) -> None:
        """Save result to database."""
        # TODO: Implement database persistence
        pass
```

---

# Enhancement 3: OOP Trading Control Service

## Design Principles

### 1. Trading Control Service (Service Layer)

```python
# src/services/trading_control_service.py

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.workers.managers.worker_pool_manager import WorkerPoolManager
from src.database.repositories.trading_account_repository import ITradingAccountRepository
from src.services.autotrading_checker import IAutoTradingChecker


class TradingStatus(Enum):
    """Trading status enum."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class TradingControlResult:
    """
    Value object for trading control operation result.
    """
    success: bool
    message: str
    account_id: Optional[int] = None
    status: Optional[TradingStatus] = None
    autotrading_enabled: Optional[bool] = None
    errors: List[str] = field(default_factory=list)


class TradingControlService:
    """
    Service for trading control operations.

    Single Responsibility: Trading lifecycle management
    Dependency Inversion: Depends on abstractions (IWorkerPoolManager, IRepository)
    """

    def __init__(
        self,
        worker_pool: WorkerPoolManager,
        account_repository: ITradingAccountRepository,
        autotrading_checker: IAutoTradingChecker
    ):
        self._worker_pool = worker_pool
        self._account_repo = account_repository
        self._autotrading_checker = autotrading_checker

    async def start_account_trading(
        self,
        account_id: int,
        check_autotrading: bool = True
    ) -> TradingControlResult:
        """
        Start automated trading for account.

        Args:
            account_id: Account ID
            check_autotrading: Verify AutoTrading is enabled

        Returns:
            TradingControlResult with operation outcome
        """
        # Get account
        account = self._account_repo.get_by_id(account_id)
        if not account or not account.is_active:
            return TradingControlResult(
                success=False,
                message="Account not found or inactive",
                account_id=account_id
            )

        # Check if worker exists
        active_workers = self._worker_pool.list_active_workers()
        if account_id not in active_workers:
            return TradingControlResult(
                success=False,
                message="Account not connected",
                account_id=account_id,
                status=TradingStatus.STOPPED
            )

        # Check AutoTrading if requested
        if check_autotrading:
            autotrading_status = await self._autotrading_checker.check_status(
                account_id
            )

            if not autotrading_status.enabled:
                return TradingControlResult(
                    success=False,
                    message="AutoTrading is disabled in MT5 terminal",
                    account_id=account_id,
                    status=TradingStatus.STOPPED,
                    autotrading_enabled=False,
                    errors=[
                        "Open MetaTrader 5 terminal",
                        "Click 'AutoTrading' button (Alt+A)",
                        "Enable algorithmic trading in options"
                    ]
                )

        # Start trading
        success = await self._worker_pool.start_trading(account_id)

        if success:
            return TradingControlResult(
                success=True,
                message="Trading started successfully",
                account_id=account_id,
                status=TradingStatus.RUNNING,
                autotrading_enabled=True
            )
        else:
            return TradingControlResult(
                success=False,
                message="Failed to start trading",
                account_id=account_id,
                status=TradingStatus.ERROR
            )

    async def stop_account_trading(
        self,
        account_id: int
    ) -> TradingControlResult:
        """
        Stop automated trading for account.
        Does not close positions.

        Args:
            account_id: Account ID

        Returns:
            TradingControlResult with operation outcome
        """
        # Check if worker exists
        active_workers = self._worker_pool.list_active_workers()
        if account_id not in active_workers:
            return TradingControlResult(
                success=False,
                message="Account not connected",
                account_id=account_id,
                status=TradingStatus.STOPPED
            )

        # Stop trading
        success = await self._worker_pool.stop_trading(account_id)

        if success:
            return TradingControlResult(
                success=True,
                message="Trading stopped successfully",
                account_id=account_id,
                status=TradingStatus.STOPPED
            )
        else:
            return TradingControlResult(
                success=False,
                message="Failed to stop trading",
                account_id=account_id,
                status=TradingStatus.ERROR
            )

    async def start_all_trading(self) -> List[TradingControlResult]:
        """
        Start trading for all connected accounts.

        Returns:
            List of results for each account
        """
        results = []
        active_workers = self._worker_pool.list_active_workers()

        for account_id in active_workers:
            result = await self.start_account_trading(account_id)
            results.append(result)

        return results

    async def stop_all_trading(self) -> List[TradingControlResult]:
        """
        Stop trading for all connected accounts.

        Returns:
            List of results for each account
        """
        results = []
        active_workers = self._worker_pool.list_active_workers()

        for account_id in active_workers:
            result = await self.stop_account_trading(account_id)
            results.append(result)

        return results

    async def get_account_trading_status(
        self,
        account_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get trading status for account.

        Args:
            account_id: Account ID

        Returns:
            Status dictionary or None if not found
        """
        status = await self._worker_pool.get_worker_status(account_id)

        if status:
            # Enhance with account info
            account = self._account_repo.get_by_id(account_id)
            if account:
                status['account_number'] = account.account_number
                status['account_name'] = account.account_name

        return status

    async def get_global_trading_status(self) -> Dict[str, Any]:
        """
        Get trading status for all accounts.

        Returns:
            Global status dictionary
        """
        active_workers = self._worker_pool.list_active_workers()

        account_statuses = []
        for account_id in active_workers:
            status = await self.get_account_trading_status(account_id)
            if status:
                account_statuses.append(status)

        return {
            'is_trading': len(account_statuses) > 0,
            'active_accounts': len(account_statuses),
            'accounts': account_statuses
        }
```

### 2. AutoTrading Checker (Strategy Pattern)

```python
# src/services/autotrading_checker.py

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from src.workers.managers.worker_pool_manager import WorkerPoolManager


@dataclass
class AutoTradingStatus:
    """Value object for AutoTrading status."""
    enabled: bool
    trade_allowed: bool
    message: str


class IAutoTradingChecker(ABC):
    """
    Interface for AutoTrading status checking.
    Strategy Pattern: Different checking strategies.
    """

    @abstractmethod
    async def check_status(self, account_id: int) -> AutoTradingStatus:
        """Check if AutoTrading is enabled."""
        pass


class WorkerBasedAutoTradingChecker(IAutoTradingChecker):
    """
    Check AutoTrading status by querying worker process.
    """

    def __init__(self, worker_pool: WorkerPoolManager):
        self._worker_pool = worker_pool

    async def check_status(self, account_id: int) -> AutoTradingStatus:
        """
        Check AutoTrading status via worker.

        Args:
            account_id: Account ID

        Returns:
            AutoTradingStatus
        """
        # Send command to worker
        # TODO: Implement command and response handling

        # For now, return placeholder
        return AutoTradingStatus(
            enabled=True,
            trade_allowed=True,
            message="AutoTrading is enabled"
        )


class CachedAutoTradingChecker(IAutoTradingChecker):
    """
    Caching decorator for AutoTrading checker.
    Decorator Pattern: Adds caching to another checker.
    """

    def __init__(
        self,
        checker: IAutoTradingChecker,
        cache_ttl_seconds: int = 60
    ):
        self._checker = checker
        self._cache_ttl = cache_ttl_seconds
        self._cache: Dict[int, Tuple[AutoTradingStatus, float]] = {}

    async def check_status(self, account_id: int) -> AutoTradingStatus:
        """Check status with caching."""
        import time

        # Check cache
        if account_id in self._cache:
            status, timestamp = self._cache[account_id]
            if (time.time() - timestamp) < self._cache_ttl:
                return status

        # Cache miss or expired, check real status
        status = await self._checker.check_status(account_id)
        self._cache[account_id] = (status, time.time())

        return status
```

### 3. API Controllers (Dependency Injection)

```python
# src/api/controllers/trading_control_controller.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from src.services.trading_control_service import (
    TradingControlService,
    TradingControlResult,
    TradingStatus
)
from src.api.dependencies import get_trading_control_service
from src.api.models.trading_control import (
    StartTradingRequest,
    StartTradingResponse,
    TradingStatusResponse
)


class TradingControlController:
    """
    Controller for trading control endpoints.
    Thin layer that delegates to service.

    Single Responsibility: HTTP request/response handling
    Dependency Inversion: Depends on service interface
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api/trading", tags=["Trading Control"])
        self._register_routes()

    def _register_routes(self):
        """Register all routes."""
        self.router.add_api_route(
            "/start",
            self.start_global_trading,
            methods=["POST"],
            response_model=List[StartTradingResponse]
        )

        self.router.add_api_route(
            "/stop",
            self.stop_global_trading,
            methods=["POST"],
            response_model=List[StartTradingResponse]
        )

        self.router.add_api_route(
            "/status",
            self.get_global_status,
            methods=["GET"],
            response_model=TradingStatusResponse
        )

        self.router.add_api_route(
            "/accounts/{account_id}/start",
            self.start_account_trading,
            methods=["POST"],
            response_model=StartTradingResponse
        )

        self.router.add_api_route(
            "/accounts/{account_id}/stop",
            self.stop_account_trading,
            methods=["POST"],
            response_model=StartTradingResponse
        )

        self.router.add_api_route(
            "/accounts/{account_id}/status",
            self.get_account_status,
            methods=["GET"],
            response_model=Dict[str, Any]
        )

    async def start_global_trading(
        self,
        service: TradingControlService = Depends(get_trading_control_service)
    ) -> List[StartTradingResponse]:
        """Start trading for all accounts."""
        results = await service.start_all_trading()

        return [
            StartTradingResponse(
                success=r.success,
                message=r.message,
                account_id=r.account_id,
                status=r.status.value if r.status else None,
                autotrading_enabled=r.autotrading_enabled,
                errors=r.errors
            )
            for r in results
        ]

    async def stop_global_trading(
        self,
        service: TradingControlService = Depends(get_trading_control_service)
    ) -> List[StartTradingResponse]:
        """Stop trading for all accounts."""
        results = await service.stop_all_trading()

        return [
            StartTradingResponse(
                success=r.success,
                message=r.message,
                account_id=r.account_id,
                status=r.status.value if r.status else None
            )
            for r in results
        ]

    async def get_global_status(
        self,
        service: TradingControlService = Depends(get_trading_control_service)
    ) -> TradingStatusResponse:
        """Get global trading status."""
        status = await service.get_global_trading_status()

        return TradingStatusResponse(**status)

    async def start_account_trading(
        self,
        account_id: int,
        service: TradingControlService = Depends(get_trading_control_service)
    ) -> StartTradingResponse:
        """Start trading for specific account."""
        result = await service.start_account_trading(account_id)

        return StartTradingResponse(
            success=result.success,
            message=result.message,
            account_id=result.account_id,
            status=result.status.value if result.status else None,
            autotrading_enabled=result.autotrading_enabled,
            errors=result.errors
        )

    async def stop_account_trading(
        self,
        account_id: int,
        service: TradingControlService = Depends(get_trading_control_service)
    ) -> StartTradingResponse:
        """Stop trading for specific account."""
        result = await service.stop_account_trading(account_id)

        return StartTradingResponse(
            success=result.success,
            message=result.message,
            account_id=result.account_id,
            status=result.status.value if result.status else None
        )

    async def get_account_status(
        self,
        account_id: int,
        service: TradingControlService = Depends(get_trading_control_service)
    ) -> Dict[str, Any]:
        """Get status for specific account."""
        status = await service.get_account_trading_status(account_id)

        if not status:
            raise HTTPException(status_code=404, detail="Account not found")

        return status


# Create controller instance
trading_control_controller = TradingControlController()
```

### 4. Dependency Injection Container

```python
# src/api/dependencies.py

from functools import lru_cache

from src.services.trading_control_service import TradingControlService
from src.services.autotrading_checker import (
    IAutoTradingChecker,
    WorkerBasedAutoTradingChecker,
    CachedAutoTradingChecker
)
from src.workers.managers.worker_pool_manager import WorkerPoolManager
from src.database.repositories.trading_account_repository import TradingAccountRepository
from src.config.services.configuration_service import ConfigurationService
from src.config.factories.configuration_factory import ConfigurationFactory


@lru_cache()
def get_configuration_service() -> ConfigurationService:
    """Get or create ConfigurationService instance."""
    return ConfigurationFactory.create_yaml_based("config/trading_config.yaml")


@lru_cache()
def get_worker_pool_manager() -> WorkerPoolManager:
    """Get or create WorkerPoolManager instance."""
    config_service = get_configuration_service()
    return WorkerPoolManager(config_service)


@lru_cache()
def get_trading_account_repository() -> TradingAccountRepository:
    """Get or create TradingAccountRepository instance."""
    return TradingAccountRepository()


@lru_cache()
def get_autotrading_checker() -> IAutoTradingChecker:
    """Get or create AutoTradingChecker instance."""
    worker_pool = get_worker_pool_manager()

    # Create base checker
    base_checker = WorkerBasedAutoTradingChecker(worker_pool)

    # Wrap with caching decorator
    cached_checker = CachedAutoTradingChecker(base_checker, cache_ttl_seconds=60)

    return cached_checker


@lru_cache()
def get_trading_control_service() -> TradingControlService:
    """Get or create TradingControlService instance."""
    return TradingControlService(
        worker_pool=get_worker_pool_manager(),
        account_repository=get_trading_account_repository(),
        autotrading_checker=get_autotrading_checker()
    )
```

---

# Class Diagrams

## Configuration System Class Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    <<interface>>                             │
│                   IConfigRepository                          │
├─────────────────────────────────────────────────────────────┤
│ + load(path: str): Dict                                      │
│ + save(path: str, config: Dict): void                        │
│ + exists(path: str): bool                                    │
└──────────────────┬──────────────────────────────────────────┘
                   △
                   │ implements
        ┌──────────┴──────────┐
        │                     │
┌───────┴────────┐   ┌────────┴──────────┐
│ YamlConfig     │   │ DatabaseConfig    │
│ Repository     │   │ Repository        │
└────────────────┘   └───────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 ConfigurationService                         │
├─────────────────────────────────────────────────────────────┤
│ - _repository: IConfigRepository                             │
│ - _merge_strategy: IMergeStrategy                            │
│ - _defaults: DefaultsConfig                                  │
│ - _accounts: Dict[str, AccountConfig]                        │
├─────────────────────────────────────────────────────────────┤
│ + load_configuration(path: str): void                        │
│ + get_account_config(name: str): AccountConfig              │
│ + get_currency_config(account, symbol): CurrencyConfig      │
│ + list_accounts(): List[str]                                 │
│ + validate_configuration(): List[str]                        │
└─────────────────────────────────────────────────────────────┘
```

## Worker Pool Class Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    <<interface>>                             │
│                       IWorker                                │
├─────────────────────────────────────────────────────────────┤
│ + start(): bool                                              │
│ + stop(timeout: float): bool                                 │
│ + send_command(command: ICommand): bool                      │
│ + get_state(): WorkerState                                   │
│ + is_alive(): bool                                           │
└──────────────────┬──────────────────────────────────────────┘
                   △
                   │ implements
        ┌──────────┴──────────┐
        │                     │
┌───────┴────────┐   ┌────────┴──────────┐
│  BaseWorker    │   │   MT5Worker       │
│  (abstract)    │   │  (concrete)       │
└────────────────┘   └───────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 WorkerPoolManager                            │
├─────────────────────────────────────────────────────────────┤
│ - _workers: Dict[int, WorkerHandle]                          │
│ - _result_queue: Queue                                       │
│ - _observers: List[IWorkerObserver]                          │
├─────────────────────────────────────────────────────────────┤
│ + start_worker(account): bool                                │
│ + stop_worker(account_id): bool                              │
│ + execute_trading_cycle(account_id): bool                    │
│ + start_trading(account_id): bool                            │
│ + stop_trading(account_id): bool                             │
│ + add_observer(observer): void                               │
└─────────────────────────────────────────────────────────────┘
```

## Trading Control Service Class Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              TradingControlService                           │
├─────────────────────────────────────────────────────────────┤
│ - _worker_pool: WorkerPoolManager                            │
│ - _account_repo: ITradingAccountRepository                   │
│ - _autotrading_checker: IAutoTradingChecker                  │
├─────────────────────────────────────────────────────────────┤
│ + start_account_trading(id): TradingControlResult           │
│ + stop_account_trading(id): TradingControlResult            │
│ + start_all_trading(): List[TradingControlResult]           │
│ + stop_all_trading(): List[TradingControlResult]            │
│ + get_account_trading_status(id): Dict                      │
│ + get_global_trading_status(): Dict                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│         TradingControlController (API Layer)                 │
├─────────────────────────────────────────────────────────────┤
│ + router: APIRouter                                          │
├─────────────────────────────────────────────────────────────┤
│ + start_global_trading(service): Response                    │
│ + stop_global_trading(service): Response                     │
│ + start_account_trading(id, service): Response              │
│ + stop_account_trading(id, service): Response               │
│ + get_global_status(service): Response                      │
│ + get_account_status(id, service): Response                 │
└─────────────────────────────────────────────────────────────┘
```

---

# Implementation Plan

## Phase 1: OOP Configuration System (Week 1)

### Day 1-2: Core Models & Interfaces
- [ ] Create value objects (ExecutionConfig, RiskConfig, StrategyConfig)
- [ ] Implement IConfigNode interface and ConfigNode
- [ ] Create AccountConfig and CurrencyConfig models
- [ ] Write unit tests for models

### Day 3: Builder & Repository
- [ ] Implement AccountConfigBuilder
- [ ] Create IConfigRepository interface
- [ ] Implement YamlConfigRepository
- [ ] Write unit tests

### Day 4: Service & Strategy
- [ ] Implement ConfigurationService
- [ ] Create IMergeStrategy and DefaultMergeStrategy
- [ ] Write integration tests
- [ ] Test inheritance resolution

### Day 5: Factory & Testing
- [ ] Implement ConfigurationFactory
- [ ] Create migration tool (v1 → v2)
- [ ] Full integration testing
- [ ] Documentation

## Phase 2: OOP Worker Pool (Week 2-3)

### Day 1-2: Worker Base Classes
- [ ] Create IWorker interface
- [ ] Implement BaseWorker (template method)
- [ ] Define WorkerState enum
- [ ] Write unit tests

### Day 3-4: Command Pattern
- [ ] Create ICommand interface
- [ ] Implement concrete commands
- [ ] Create CommandFactory
- [ ] Write unit tests

### Day 5-6: MT5Worker Implementation
- [ ] Implement MT5Worker class
- [ ] Add connection management
- [ ] Add trading cycle execution
- [ ] Test single worker

### Day 7-8: Worker Pool Manager
- [ ] Implement WorkerHandle
- [ ] Create WorkerPoolManager (facade)
- [ ] Add worker lifecycle management
- [ ] Test multiple workers

### Day 9: Observer Pattern
- [ ] Create IWorkerObserver interface
- [ ] Implement WebSocketObserver
- [ ] Implement DatabaseObserver
- [ ] Integration testing

### Day 10: Polish & Documentation
- [ ] Performance optimization
- [ ] Memory leak checks
- [ ] Full integration testing
- [ ] Architecture documentation

## Phase 3: OOP Trading Control (Week 4)

### Day 1-2: Service Layer
- [ ] Create TradingControlService
- [ ] Define TradingControlResult value object
- [ ] Implement all service methods
- [ ] Write unit tests

### Day 3: AutoTrading Checker
- [ ] Create IAutoTradingChecker interface
- [ ] Implement WorkerBasedAutoTradingChecker
- [ ] Add CachedAutoTradingChecker (decorator)
- [ ] Write tests

### Day 4-5: API Controllers
- [ ] Implement TradingControlController
- [ ] Create request/response models
- [ ] Add dependency injection
- [ ] Write API tests

### Day 6: Integration
- [ ] Wire all components together
- [ ] End-to-end testing
- [ ] WebSocket integration
- [ ] Database integration

### Day 7: Documentation & Polish
- [ ] API documentation (OpenAPI)
- [ ] Postman collection
- [ ] User guide
- [ ] Final testing

---

## Success Criteria (OOP-Focused)

### Configuration System
- ✅ All classes follow Single Responsibility Principle
- ✅ Configuration is immutable (value objects)
- ✅ Dependency injection used throughout
- ✅ 100% test coverage for core classes
- ✅ Strategy pattern allows custom merge logic

### Worker Pool
- ✅ Clear separation of concerns (worker, manager, observer)
- ✅ Command pattern for all worker operations
- ✅ Observer pattern for event notifications
- ✅ Template method for worker lifecycle
- ✅ Facade provides simple interface

### Trading Control
- ✅ Service layer isolates business logic
- ✅ Controllers are thin (no business logic)
- ✅ Dependency injection for testability
- ✅ Strategy pattern for AutoTrading checking
- ✅ Value objects for all data transfer

---

**End of OOP Design Document**

This design is fully Object-Oriented with proper use of interfaces, abstract classes, design patterns, and SOLID principles. Ready for implementation?
