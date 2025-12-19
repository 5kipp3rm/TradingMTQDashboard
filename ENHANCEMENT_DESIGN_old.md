# TradingMTQ Enhancement Design Document

**Created:** 2025-12-19
**Status:** Design Phase - Pending Implementation
**Version:** 1.0

---

## Executive Summary

This document outlines three major enhancements to TradingMTQ:

1. **Enhanced Configuration Structure** - Restructure YAML config for better maintainability and multi-account support
2. **Multi-Worker MT5 Architecture** - Support multiple MT5 instances without disconnecting existing connections
3. **Trading Control API** - Add start/stop trading endpoints with AutoTrading status checks

---

## Table of Contents

1. [Enhancement 1: Configuration Structure Refactor](#enhancement-1-configuration-structure-refactor)
2. [Enhancement 2: Multi-Worker MT5 Architecture](#enhancement-2-multi-worker-mt5-architecture)
3. [Enhancement 3: Trading Control API](#enhancement-3-trading-control-api)
4. [Implementation Plan](#implementation-plan)
5. [Migration Guide](#migration-guide)
6. [Testing Strategy](#testing-strategy)
7. [Rollback Plan](#rollback-plan)

---

# Enhancement 1: Configuration Structure Refactor

## Current Problem

The current configuration structure in `config/currencies.yaml` has several limitations:

1. **Flat structure** - All settings at root level, hard to organize by concern
2. **Mixed accounts** - No clear separation between account-specific and global settings
3. **Repetitive config** - Each currency repeats common settings
4. **No inheritance** - Can't define defaults and override per currency
5. **Single account focus** - Not designed for multi-account trading

**Current Structure:**
```yaml
global:
  max_concurrent_trades: 15
  portfolio_risk_percent: 8.0
  interval_seconds: 30
  use_intelligent_position_manager: true

currencies:
  EURUSD:
    enabled: true
    risk_percent: 0.5
    strategy_type: "position"
    timeframe: "M5"
    fast_period: 10
    slow_period: 20
    sl_pips: 20
    tp_pips: 40
```

## Proposed Solution

### New Hierarchical Structure

```yaml
# ============================================================================
# config/trading_config.yaml - New Master Configuration
# ============================================================================

version: "2.0"  # Configuration schema version

# ----------------------------------------------------------------------------
# GLOBAL DEFAULTS
# ----------------------------------------------------------------------------
defaults:
  # Trading execution
  execution:
    interval_seconds: 30
    parallel_execution: false
    max_workers: 3
    use_intelligent_position_manager: true
    use_ml_enhancement: true
    use_sentiment_filter: true

  # Risk management defaults
  risk:
    portfolio_risk_percent: 8.0
    max_concurrent_trades: 15
    default_risk_percent: 0.5
    max_position_size: 1.0
    min_position_size: 0.01

  # Strategy defaults
  strategy:
    type: "position"  # "position" or "crossover"
    timeframe: "M5"
    fast_period: 10
    slow_period: 20
    sl_pips: 20
    tp_pips: 40

  # Position management defaults
  position_management:
    enabled: true
    check_interval_seconds: 5
    trailing_stop:
      enabled: true
      trigger_pips: 10
      distance_pips: 5
    breakeven:
      enabled: true
      trigger_pips: 15
      offset_pips: 2
    partial_close:
      enabled: false
      trigger_pips: 30
      close_percent: 50

  # Trading rules defaults
  trading_rules:
    cooldown_seconds: 120
    trade_on_signal_change: false
    min_signal_confidence: 0.5

  # Trading hours (optional)
  trading_hours: null  # null = 24/7, or specify {start: "08:00", end: "17:00"}

# ----------------------------------------------------------------------------
# ACCOUNT PROFILES
# ----------------------------------------------------------------------------
accounts:
  # Each account can have its own configuration
  # Account credentials come from database (TradingAccount table)

  default:
    # Account-level overrides (optional)
    risk:
      portfolio_risk_percent: 8.0
      max_concurrent_trades: 15

    execution:
      interval_seconds: 30
      use_intelligent_position_manager: true

    # Account-specific currency configurations
    currencies:
      - symbol: EURUSD
        enabled: true
        risk_percent: 0.5  # Override default
        # All other settings inherited from defaults

      - symbol: GBPUSD
        enabled: true
        risk_percent: 0.5

      - symbol: USDJPY
        enabled: true
        risk_percent: 0.5
        strategy:
          sl_pips: 25  # Override default for USDJPY
          tp_pips: 50

      - symbol: AUDUSD
        enabled: true
        risk_percent: 0.4  # Lower risk for AUD
        trading_hours:
          start: "08:00"  # Override default to trade only during specific hours
          end: "17:00"

      - symbol: USDCAD
        enabled: true

      - symbol: NZDUSD
        enabled: false  # Disabled but config preserved

  aggressive:
    # Aggressive trading profile
    risk:
      portfolio_risk_percent: 12.0
      max_concurrent_trades: 20
      default_risk_percent: 1.0

    execution:
      interval_seconds: 15  # Faster execution
      parallel_execution: true
      max_workers: 5

    strategy:
      fast_period: 8   # More sensitive
      slow_period: 16
      sl_pips: 15      # Tighter stops
      tp_pips: 30

    currencies:
      - symbol: EURUSD
        enabled: true
      - symbol: GBPUSD
        enabled: true
      - symbol: USDJPY
        enabled: true
      - symbol: AUDUSD
        enabled: true
      - symbol: USDCAD
        enabled: true

  conservative:
    # Conservative trading profile
    risk:
      portfolio_risk_percent: 5.0
      max_concurrent_trades: 10
      default_risk_percent: 0.3

    execution:
      interval_seconds: 60  # Slower execution
      use_intelligent_position_manager: true

    strategy:
      fast_period: 20   # Less sensitive
      slow_period: 50
      sl_pips: 30       # Wider stops
      tp_pips: 60

    currencies:
      - symbol: EURUSD
        enabled: true
      - symbol: GBPUSD
        enabled: true
      - symbol: USDJPY
        enabled: true

# ----------------------------------------------------------------------------
# STRATEGY TEMPLATES (Optional - for future extensibility)
# ----------------------------------------------------------------------------
strategy_templates:
  scalping:
    type: "position"
    timeframe: "M1"
    fast_period: 5
    slow_period: 10
    sl_pips: 10
    tp_pips: 15
    cooldown_seconds: 60

  swing:
    type: "crossover"
    timeframe: "H1"
    fast_period: 20
    slow_period: 50
    sl_pips: 50
    tp_pips: 100
    cooldown_seconds: 3600  # 1 hour

# ----------------------------------------------------------------------------
# EMERGENCY CONTROLS
# ----------------------------------------------------------------------------
emergency:
  enabled: false
  stop_all_trading: false
  close_all_positions: false
  max_daily_loss_percent: 10.0  # Stop trading if daily loss exceeds this
  max_drawdown_percent: 15.0    # Stop trading if drawdown exceeds this

# ----------------------------------------------------------------------------
# NOTIFICATIONS (Optional)
# ----------------------------------------------------------------------------
notifications:
  enabled: true
  channels:
    webhook:
      enabled: false
      url: null
    email:
      enabled: false
      recipients: []
  events:
    - trade_opened
    - trade_closed
    - error
    - emergency_stop
```

## Benefits of New Structure

1. **Clear Hierarchy** - Settings organized by concern (risk, execution, strategy, etc.)
2. **Inheritance** - Define defaults once, override only what changes
3. **Multi-Account Support** - Each account can have its own profile
4. **Less Repetition** - Currency config much shorter (only specify overrides)
5. **Strategy Templates** - Reusable strategy presets (scalping, swing, etc.)
6. **Emergency Controls** - Built-in circuit breakers
7. **Extensibility** - Easy to add new settings without restructuring

## Configuration Loading Architecture

```python
# src/config/config_v2.py

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from pathlib import Path
import yaml
from copy import deepcopy

@dataclass
class ExecutionConfig:
    interval_seconds: int = 30
    parallel_execution: bool = False
    max_workers: int = 3
    use_intelligent_position_manager: bool = True
    use_ml_enhancement: bool = True
    use_sentiment_filter: bool = True

@dataclass
class RiskConfig:
    portfolio_risk_percent: float = 8.0
    max_concurrent_trades: int = 15
    default_risk_percent: float = 0.5
    max_position_size: float = 1.0
    min_position_size: float = 0.01

@dataclass
class StrategyConfig:
    type: str = "position"
    timeframe: str = "M5"
    fast_period: int = 10
    slow_period: int = 20
    sl_pips: int = 20
    tp_pips: int = 40

@dataclass
class PositionManagementConfig:
    enabled: bool = True
    check_interval_seconds: int = 5
    trailing_stop: Dict[str, Any] = field(default_factory=dict)
    breakeven: Dict[str, Any] = field(default_factory=dict)
    partial_close: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradingRulesConfig:
    cooldown_seconds: int = 120
    trade_on_signal_change: bool = False
    min_signal_confidence: float = 0.5

@dataclass
class TradingHoursConfig:
    start: Optional[str] = None
    end: Optional[str] = None

@dataclass
class CurrencyConfig:
    symbol: str
    enabled: bool = True
    risk_percent: Optional[float] = None
    strategy: Optional[Dict[str, Any]] = None
    trading_hours: Optional[TradingHoursConfig] = None
    # ... other optional overrides

@dataclass
class AccountConfig:
    name: str
    risk: Optional[RiskConfig] = None
    execution: Optional[ExecutionConfig] = None
    strategy: Optional[StrategyConfig] = None
    position_management: Optional[PositionManagementConfig] = None
    trading_rules: Optional[TradingRulesConfig] = None
    currencies: List[CurrencyConfig] = field(default_factory=list)

@dataclass
class DefaultsConfig:
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    position_management: PositionManagementConfig = field(default_factory=PositionManagementConfig)
    trading_rules: TradingRulesConfig = field(default_factory=TradingRulesConfig)
    trading_hours: Optional[TradingHoursConfig] = None

@dataclass
class EmergencyConfig:
    enabled: bool = False
    stop_all_trading: bool = False
    close_all_positions: bool = False
    max_daily_loss_percent: float = 10.0
    max_drawdown_percent: float = 15.0

@dataclass
class TradingConfig:
    version: str
    defaults: DefaultsConfig
    accounts: Dict[str, AccountConfig]
    emergency: EmergencyConfig
    strategy_templates: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ConfigurationManagerV2:
    """
    Enhanced configuration manager with inheritance and multi-account support.
    """

    def __init__(self, config_path: str = "config/trading_config.yaml"):
        self.config_path = Path(config_path)
        self.config: Optional[TradingConfig] = None
        self.load()

    def load(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            raw_config = yaml.safe_load(f)

        # Parse configuration with inheritance
        self.config = self._parse_config(raw_config)

    def _parse_config(self, raw: Dict[str, Any]) -> TradingConfig:
        """Parse raw YAML into structured config with inheritance."""
        # TODO: Implement parsing logic with deep merge for inheritance
        pass

    def get_account_config(self, account_name: str = "default") -> AccountConfig:
        """
        Get configuration for specific account with all inheritance resolved.

        Returns:
            Fully resolved AccountConfig with defaults merged
        """
        if account_name not in self.config.accounts:
            raise ValueError(f"Account profile '{account_name}' not found")

        account_config = self.config.accounts[account_name]

        # Merge with defaults
        return self._merge_with_defaults(account_config)

    def _merge_with_defaults(self, account: AccountConfig) -> AccountConfig:
        """Merge account config with defaults."""
        # Deep merge logic: account overrides defaults
        merged = deepcopy(self.config.defaults)

        # Override with account-specific settings
        if account.risk:
            merged.risk = account.risk
        if account.execution:
            merged.execution = account.execution
        # ... merge other fields

        return merged

    def get_currency_config(
        self,
        account_name: str,
        symbol: str
    ) -> CurrencyConfig:
        """
        Get fully resolved configuration for a specific currency.

        Merges: defaults → account defaults → currency overrides
        """
        account_config = self.get_account_config(account_name)

        # Find currency in account
        currency = next(
            (c for c in account_config.currencies if c.symbol == symbol),
            None
        )

        if not currency:
            raise ValueError(f"Currency {symbol} not found in account {account_name}")

        # Merge with account and global defaults
        return self._merge_currency_with_defaults(currency, account_config)

    def list_accounts(self) -> List[str]:
        """List all configured account profiles."""
        return list(self.config.accounts.keys())

    def list_currencies(self, account_name: str, enabled_only: bool = True) -> List[str]:
        """List currencies for an account."""
        account = self.config.accounts.get(account_name)
        if not account:
            return []

        currencies = account.currencies
        if enabled_only:
            currencies = [c for c in currencies if c.enabled]

        return [c.symbol for c in currencies]

    def is_emergency_stop(self) -> bool:
        """Check if emergency stop is active."""
        return self.config.emergency.stop_all_trading

    def check_daily_loss_limit(self, daily_loss_percent: float) -> bool:
        """Check if daily loss limit exceeded."""
        if not self.config.emergency.enabled:
            return False

        return daily_loss_percent >= self.config.emergency.max_daily_loss_percent
```

## Migration Strategy

### Phase 1: Backward Compatibility Layer

```python
# src/config/config_migrator.py

class ConfigMigrator:
    """
    Migrate old config format to new format.
    Provides backward compatibility.
    """

    @staticmethod
    def migrate_v1_to_v2(old_config_path: str) -> Dict[str, Any]:
        """
        Convert old config format to new format.

        Old: config/currencies.yaml (flat structure)
        New: config/trading_config.yaml (hierarchical)
        """
        with open(old_config_path, 'r') as f:
            old = yaml.safe_load(f)

        # Build new structure
        new_config = {
            'version': '2.0',
            'defaults': {
                'execution': {
                    'interval_seconds': old['global'].get('interval_seconds', 30),
                    'parallel_execution': old['global'].get('parallel_execution', False),
                    # ... map other settings
                },
                'risk': {
                    'portfolio_risk_percent': old['global'].get('portfolio_risk_percent', 8.0),
                    'max_concurrent_trades': old['global'].get('max_concurrent_trades', 15),
                    # ... map other settings
                },
                # ... other defaults
            },
            'accounts': {
                'default': {
                    'currencies': []
                }
            }
        }

        # Migrate currencies
        for symbol, currency_config in old.get('currencies', {}).items():
            new_config['accounts']['default']['currencies'].append({
                'symbol': symbol,
                'enabled': currency_config.get('enabled', True),
                'risk_percent': currency_config.get('risk_percent'),
                # ... map other currency settings
            })

        return new_config

    @staticmethod
    def auto_detect_version(config_path: str) -> str:
        """Detect config version from file."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if 'version' in config:
            return config['version']
        else:
            return '1.0'  # Old format
```

### Phase 2: Configuration Factory

```python
# src/config/__init__.py

def create_configuration_manager(
    config_path: str = "config/trading_config.yaml",
    auto_migrate: bool = True
) -> Union[ConfigurationManager, ConfigurationManagerV2]:
    """
    Factory function to create appropriate config manager.

    Args:
        config_path: Path to configuration file
        auto_migrate: Automatically migrate old format to new

    Returns:
        Configuration manager instance (V1 or V2)
    """
    migrator = ConfigMigrator()
    version = migrator.auto_detect_version(config_path)

    if version == '1.0':
        if auto_migrate:
            logger.warning(f"Old config format detected. Consider migrating to v2.")
            # Return V1 manager with warning
            return ConfigurationManager(config_path)
        else:
            return ConfigurationManager(config_path)
    else:
        return ConfigurationManagerV2(config_path)
```

---

# Enhancement 2: Multi-Worker MT5 Architecture

## Current Problem

**Issue:** MT5Connector uses `mt5.initialize()` which is process-wide. When connecting to a second account, the first account gets disconnected.

**Root Cause:** The `MetaTrader5` Python library uses a single global connection per process. Multiple `mt5.initialize()` calls overwrite the previous connection.

**Impact:**
- Can't trade multiple accounts simultaneously in same process
- Session manager tracks connections but only one is actually active at a time
- Trading bot service will disconnect account A when connecting to account B

## Proposed Solution: Process-Based Worker Pool

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Main Process                        │
│                    (API Server + Orchestrator)                   │
├─────────────────────────────────────────────────────────────────┤
│  • API Routes (account connections, trading control, etc.)       │
│  • Session Manager (tracks which workers handle which accounts)  │
│  • Worker Pool Manager (spawns/manages worker processes)         │
│  • IPC Bridge (communicates with worker processes via queues)    │
└────────┬────────────────────────────────────────────────────────┘
         │
         │ IPC (multiprocessing.Queue or ZeroMQ)
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Worker Process │ │  Worker Process │ │  Worker Process │ │  Worker Process │
│     (Account 1) │ │     (Account 2) │ │     (Account 3) │ │     (Account N) │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│  MT5 Connector  │ │  MT5 Connector  │ │  MT5 Connector  │ │  MT5 Connector  │
│  (mt5.init #1)  │ │  (mt5.init #2)  │ │  (mt5.init #3)  │ │  (mt5.init #N)  │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│  Orchestrator   │ │  Orchestrator   │ │  Orchestrator   │ │  Orchestrator   │
│  Trading Loop   │ │  Trading Loop   │ │  Trading Loop   │ │  Trading Loop   │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Key Components

#### 1. Worker Process

```python
# src/workers/mt5_worker.py

from multiprocessing import Process, Queue
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from src.connectors.mt5_connector import MT5Connector
from src.trading.orchestrator import MultiCurrencyOrchestrator
from src.database.connection import get_session
from src.database.models import TradingAccount

logger = logging.getLogger(__name__)


class MT5Worker(Process):
    """
    Worker process for isolated MT5 connection.

    Each worker runs in its own process with its own MT5 connection.
    This allows multiple MT5 accounts to be connected simultaneously.
    """

    def __init__(
        self,
        account_id: int,
        account_number: int,
        login: int,
        password: str,
        server: str,
        command_queue: Queue,
        result_queue: Queue,
        config: Dict[str, Any]
    ):
        super().__init__(name=f"MT5Worker-Account{account_id}")
        self.account_id = account_id
        self.account_number = account_number
        self.login = login
        self.password = password
        self.server = server
        self.command_queue = command_queue
        self.result_queue = result_queue
        self.config = config

        self.connector: Optional[MT5Connector] = None
        self.orchestrator: Optional[MultiCurrencyOrchestrator] = None
        self.is_running = False

    def run(self):
        """Main worker loop."""
        logger.info(
            f"Worker started for account {self.account_id} (#{self.account_number})"
        )

        try:
            # Initialize MT5 connection
            self._initialize_mt5()

            # Initialize orchestrator
            self._initialize_orchestrator()

            # Send ready signal
            self.result_queue.put({
                'type': 'worker_ready',
                'account_id': self.account_id,
                'timestamp': datetime.now().isoformat()
            })

            # Main command loop
            self.is_running = True
            while self.is_running:
                try:
                    # Wait for command (with timeout to allow periodic checks)
                    if not self.command_queue.empty():
                        command = self.command_queue.get(timeout=1.0)
                        self._handle_command(command)
                except Empty:
                    # No command received, perform periodic tasks
                    self._periodic_check()
                except Exception as e:
                    logger.error(f"Error in worker loop: {e}", exc_info=True)
                    self.result_queue.put({
                        'type': 'error',
                        'account_id': self.account_id,
                        'error': str(e)
                    })

        except Exception as e:
            logger.error(f"Fatal error in worker: {e}", exc_info=True)
            self.result_queue.put({
                'type': 'worker_failed',
                'account_id': self.account_id,
                'error': str(e)
            })

        finally:
            self._cleanup()

    def _initialize_mt5(self):
        """Initialize MT5 connector in this worker process."""
        self.connector = MT5Connector(
            instance_id=f"worker_{self.account_id}"
        )

        success = self.connector.connect(
            login=self.login,
            password=self.password,
            server=self.server,
            timeout=60000
        )

        if not success:
            raise Exception(f"Failed to connect to MT5 for account {self.account_id}")

        logger.info(f"MT5 connected for account {self.account_id}")

    def _initialize_orchestrator(self):
        """Initialize trading orchestrator."""
        self.orchestrator = MultiCurrencyOrchestrator(
            connector=self.connector,
            max_concurrent_trades=self.config.get('max_concurrent_trades', 15),
            portfolio_risk_percent=self.config.get('portfolio_risk_percent', 8.0),
            use_intelligent_manager=self.config.get('use_intelligent_manager', False)
        )

        # Add currencies from config
        # TODO: Load currencies from database or config

        logger.info(f"Orchestrator initialized for account {self.account_id}")

    def _handle_command(self, command: Dict[str, Any]):
        """Handle command from main process."""
        cmd_type = command.get('type')

        if cmd_type == 'execute_cycle':
            self._execute_trading_cycle()

        elif cmd_type == 'start_trading':
            self._start_trading()

        elif cmd_type == 'stop_trading':
            self._stop_trading()

        elif cmd_type == 'get_status':
            self._send_status()

        elif cmd_type == 'shutdown':
            self.is_running = False

        else:
            logger.warning(f"Unknown command: {cmd_type}")

    def _execute_trading_cycle(self):
        """Execute one trading cycle."""
        try:
            results = self.orchestrator.process_single_cycle()

            self.result_queue.put({
                'type': 'cycle_complete',
                'account_id': self.account_id,
                'results': results,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
            self.result_queue.put({
                'type': 'cycle_error',
                'account_id': self.account_id,
                'error': str(e)
            })

    def _start_trading(self):
        """Start automated trading."""
        self.is_running = True
        self.result_queue.put({
            'type': 'trading_started',
            'account_id': self.account_id
        })

    def _stop_trading(self):
        """Stop automated trading."""
        self.is_running = False
        self.result_queue.put({
            'type': 'trading_stopped',
            'account_id': self.account_id
        })

    def _send_status(self):
        """Send current status to main process."""
        status = {
            'type': 'status_update',
            'account_id': self.account_id,
            'is_running': self.is_running,
            'connected': self.connector.is_connected() if self.connector else False,
            'active_traders': len(self.orchestrator.traders) if self.orchestrator else 0
        }
        self.result_queue.put(status)

    def _periodic_check(self):
        """Perform periodic health checks."""
        # Check connection health
        if self.connector and not self.connector.is_connected():
            logger.warning(f"Connection lost for account {self.account_id}, attempting reconnect")
            try:
                self.connector.reconnect()
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")

    def _cleanup(self):
        """Cleanup resources before exit."""
        logger.info(f"Worker cleanup for account {self.account_id}")

        if self.connector:
            try:
                self.connector.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

        logger.info(f"Worker terminated for account {self.account_id}")
```

#### 2. Worker Pool Manager

```python
# src/workers/worker_pool_manager.py

from multiprocessing import Queue
from typing import Dict, Optional, List
import asyncio
import logging
from datetime import datetime

from src.workers.mt5_worker import MT5Worker
from src.database.models import TradingAccount

logger = logging.getLogger(__name__)


class WorkerPoolManager:
    """
    Manages pool of MT5 worker processes.

    Each worker handles one MT5 account in isolated process.
    Provides IPC bridge for command/result communication.
    """

    def __init__(self):
        self.workers: Dict[int, MT5Worker] = {}  # account_id -> worker
        self.command_queues: Dict[int, Queue] = {}  # account_id -> command queue
        self.result_queue = Queue()  # Shared result queue for all workers
        self._result_reader_task: Optional[asyncio.Task] = None

    async def start_worker(
        self,
        account: TradingAccount,
        config: Dict[str, Any]
    ) -> bool:
        """
        Start worker process for account.

        Args:
            account: Trading account
            config: Trading configuration

        Returns:
            True if worker started successfully
        """
        account_id = account.id

        # Check if worker already exists
        if account_id in self.workers:
            logger.warning(f"Worker already exists for account {account_id}")
            return False

        logger.info(f"Starting worker for account {account_id}")

        # Create command queue for this worker
        command_queue = Queue()
        self.command_queues[account_id] = command_queue

        # Create worker process
        worker = MT5Worker(
            account_id=account_id,
            account_number=account.account_number,
            login=account.login,
            password=account.password_encrypted,  # TODO: Decrypt
            server=account.server,
            command_queue=command_queue,
            result_queue=self.result_queue,
            config=config
        )

        # Start worker process
        worker.start()
        self.workers[account_id] = worker

        # Wait for ready signal (with timeout)
        ready = await self._wait_for_worker_ready(account_id, timeout=30.0)

        if ready:
            logger.info(f"Worker ready for account {account_id}")
            return True
        else:
            logger.error(f"Worker failed to start for account {account_id}")
            await self.stop_worker(account_id)
            return False

    async def stop_worker(self, account_id: int) -> bool:
        """
        Stop worker process for account.

        Args:
            account_id: Account ID

        Returns:
            True if stopped successfully
        """
        if account_id not in self.workers:
            logger.warning(f"No worker found for account {account_id}")
            return False

        logger.info(f"Stopping worker for account {account_id}")

        # Send shutdown command
        await self.send_command(account_id, {'type': 'shutdown'})

        # Wait for worker to terminate
        worker = self.workers[account_id]
        worker.join(timeout=10.0)

        if worker.is_alive():
            logger.warning(f"Worker didn't terminate gracefully, forcing")
            worker.terminate()
            worker.join(timeout=5.0)

        # Cleanup
        del self.workers[account_id]
        if account_id in self.command_queues:
            del self.command_queues[account_id]

        logger.info(f"Worker stopped for account {account_id}")
        return True

    async def send_command(
        self,
        account_id: int,
        command: Dict[str, Any]
    ) -> bool:
        """
        Send command to worker.

        Args:
            account_id: Target account ID
            command: Command dictionary

        Returns:
            True if sent successfully
        """
        if account_id not in self.command_queues:
            logger.error(f"No command queue for account {account_id}")
            return False

        try:
            self.command_queues[account_id].put(command)
            return True
        except Exception as e:
            logger.error(f"Failed to send command to worker {account_id}: {e}")
            return False

    async def execute_trading_cycle(self, account_id: int) -> bool:
        """Execute trading cycle for account."""
        return await self.send_command(account_id, {'type': 'execute_cycle'})

    async def start_trading(self, account_id: int) -> bool:
        """Start automated trading for account."""
        return await self.send_command(account_id, {'type': 'start_trading'})

    async def stop_trading(self, account_id: int) -> bool:
        """Stop automated trading for account."""
        return await self.send_command(account_id, {'type': 'stop_trading'})

    async def get_worker_status(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get status from worker."""
        if account_id not in self.workers:
            return None

        # Send status request
        await self.send_command(account_id, {'type': 'get_status'})

        # Wait for response (with timeout)
        # TODO: Implement response waiting logic

        return None

    def list_active_workers(self) -> List[int]:
        """List account IDs with active workers."""
        return [
            account_id
            for account_id, worker in self.workers.items()
            if worker.is_alive()
        ]

    async def start_result_reader(self):
        """Start background task to read results from workers."""
        if self._result_reader_task:
            return

        self._result_reader_task = asyncio.create_task(self._read_results())

    async def _read_results(self):
        """Background task to read results from queue."""
        while True:
            try:
                if not self.result_queue.empty():
                    result = self.result_queue.get_nowait()
                    await self._handle_result(result)

                await asyncio.sleep(0.1)  # Small delay

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading results: {e}", exc_info=True)

    async def _handle_result(self, result: Dict[str, Any]):
        """Handle result from worker."""
        result_type = result.get('type')
        account_id = result.get('account_id')

        logger.debug(f"Received result from worker {account_id}: {result_type}")

        # TODO: Broadcast to WebSocket clients, update database, etc.

    async def _wait_for_worker_ready(
        self,
        account_id: int,
        timeout: float
    ) -> bool:
        """Wait for worker ready signal."""
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if not self.result_queue.empty():
                result = self.result_queue.get_nowait()
                if (result.get('type') == 'worker_ready' and
                    result.get('account_id') == account_id):
                    return True

            await asyncio.sleep(0.1)

        return False

    async def stop_all_workers(self):
        """Stop all worker processes."""
        logger.info("Stopping all workers")

        account_ids = list(self.workers.keys())
        for account_id in account_ids:
            await self.stop_worker(account_id)

        if self._result_reader_task:
            self._result_reader_task.cancel()
            try:
                await self._result_reader_task
            except asyncio.CancelledError:
                pass


# Global instance
worker_pool_manager = WorkerPoolManager()
```

#### 3. Updated Session Manager

```python
# src/services/session_manager_v2.py (modifications)

class MT5SessionManagerV2:
    """
    Updated session manager that uses worker pool.
    """

    def __init__(self, worker_pool: WorkerPoolManager):
        self.worker_pool = worker_pool
        self._sessions: Dict[int, ConnectionState] = {}
        self._lock = asyncio.Lock()

    async def connect_account(
        self,
        account: TradingAccount,
        config: Dict[str, Any],
        db: Session,
        force_reconnect: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Connect account by starting worker process.
        """
        async with self._lock:
            account_id = account.id

            # Check if already connected
            if account_id in self._sessions and not force_reconnect:
                return True, None

            # Start worker
            success = await self.worker_pool.start_worker(account, config)

            if success:
                # Update session state
                state = ConnectionState(
                    account_id=account_id,
                    account_number=account.account_number,
                    is_connected=True,
                    last_connected_at=datetime.now(timezone.utc)
                )
                self._sessions[account_id] = state

                # Update database
                account.last_connected = state.last_connected_at
                db.commit()

                return True, None
            else:
                return False, "Failed to start worker"

    async def disconnect_account(
        self,
        account_id: int,
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """
        Disconnect account by stopping worker process.
        """
        async with self._lock:
            success = await self.worker_pool.stop_worker(account_id)

            if success and account_id in self._sessions:
                del self._sessions[account_id]

            return success, None if success else "Failed to stop worker"
```

## Benefits of Worker Pool Architecture

1. **True Multi-Account Support** - Each account in isolated process with own MT5 connection
2. **Fault Isolation** - Worker crash doesn't affect other accounts or main process
3. **Resource Management** - OS-level process isolation prevents memory leaks
4. **Scalability** - Can spawn workers on-demand, up to system limits
5. **Monitoring** - Clear process-level metrics (CPU, memory per account)
6. **Clean Shutdown** - Graceful termination of individual workers

## Limitations & Considerations

1. **IPC Overhead** - Queue communication slower than in-process calls (acceptable tradeoff)
2. **Memory Usage** - Each worker has full Python runtime (~50-100MB per process)
3. **Shared State** - Database is shared state; must handle concurrency carefully
4. **Platform Dependency** - `multiprocessing` has platform quirks (test on Windows)
5. **Debugging** - Multi-process debugging more complex than single-process

---

# Enhancement 3: Trading Control API

## Current State

The API has basic endpoints but lacks:
- Start/stop trading per account
- AutoTrading status check
- Per-currency enable/disable
- Real-time trading state visibility

## Proposed API Endpoints

### 1. Trading Bot Control (Global)

```python
# src/api/routes/trading_control.py

@router.post("/trading/start")
async def start_global_trading(db: Session = Depends(get_db)):
    """
    Start automated trading for all connected accounts.

    Returns:
        Success status and list of accounts started
    """
    pass

@router.post("/trading/stop")
async def stop_global_trading(db: Session = Depends(get_db)):
    """
    Stop automated trading for all connected accounts.
    Does NOT close positions, only stops new trades.

    Returns:
        Success status and list of accounts stopped
    """
    pass

@router.get("/trading/status")
async def get_global_trading_status(db: Session = Depends(get_db)):
    """
    Get trading status for all accounts.

    Returns:
        {
            "is_trading": bool,
            "accounts": [
                {
                    "account_id": int,
                    "account_number": int,
                    "is_trading": bool,
                    "autotrading_enabled": bool,
                    "connected": bool,
                    "active_currencies": int,
                    "open_positions": int
                }
            ]
        }
    """
    pass
```

### 2. Per-Account Trading Control

```python
@router.post("/accounts/{account_id}/trading/start")
async def start_account_trading(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Start automated trading for specific account.

    Checks:
        - Account exists and is active
        - Account is connected
        - AutoTrading is enabled in MT5 terminal

    Returns:
        {
            "success": bool,
            "message": str,
            "account_id": int,
            "is_trading": bool,
            "autotrading_enabled": bool
        }
    """
    # Check account exists
    account = db.get(TradingAccount, account_id)
    if not account or not account.is_active:
        raise HTTPException(404, "Account not found or inactive")

    # Check connection
    worker_active = worker_pool_manager.list_active_workers()
    if account_id not in worker_active:
        raise HTTPException(400, "Account not connected")

    # Check AutoTrading status
    autotrading_enabled = await check_autotrading_status(account_id)
    if not autotrading_enabled:
        return {
            "success": False,
            "message": "AutoTrading is disabled in MT5 terminal",
            "account_id": account_id,
            "is_trading": False,
            "autotrading_enabled": False,
            "instructions": {
                "step1": "Open MetaTrader 5 terminal",
                "step2": "Click 'AutoTrading' button in toolbar (or press Alt+A)",
                "step3": "Or go to: Tools -> Options -> Expert Advisors -> Enable algorithmic trading",
                "step4": "Retry this API call after enabling AutoTrading"
            }
        }

    # Start trading
    success = await worker_pool_manager.start_trading(account_id)

    return {
        "success": success,
        "message": "Trading started" if success else "Failed to start trading",
        "account_id": account_id,
        "is_trading": success,
        "autotrading_enabled": True
    }

@router.post("/accounts/{account_id}/trading/stop")
async def stop_account_trading(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Stop automated trading for specific account."""
    pass

@router.get("/accounts/{account_id}/trading/status")
async def get_account_trading_status(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Get trading status for account.

    Returns:
        {
            "account_id": int,
            "account_number": int,
            "is_connected": bool,
            "is_trading": bool,
            "autotrading_enabled": bool,
            "active_currencies": List[str],
            "open_positions": int,
            "total_profit": float,
            "daily_trades": int,
            "last_trade_time": datetime
        }
    """
    pass
```

### 3. AutoTrading Status Check

```python
@router.get("/accounts/{account_id}/autotrading/status")
async def check_autotrading_status_api(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if AutoTrading is enabled in MT5 terminal.

    Returns:
        {
            "account_id": int,
            "autotrading_enabled": bool,
            "trade_allowed": bool,
            "message": str,
            "instructions": dict  # Only present if disabled
        }
    """
    account = db.get(TradingAccount, account_id)
    if not account:
        raise HTTPException(404, "Account not found")

    # Check if worker exists
    if account_id not in worker_pool_manager.list_active_workers():
        raise HTTPException(400, "Account not connected")

    # Query worker for AutoTrading status
    status = await get_autotrading_status_from_worker(account_id)

    if not status['autotrading_enabled']:
        return {
            "account_id": account_id,
            "autotrading_enabled": False,
            "trade_allowed": False,
            "message": "AutoTrading is disabled in MT5 terminal",
            "instructions": {
                "step1": "Open MetaTrader 5 terminal",
                "step2": "Click 'AutoTrading' button in toolbar (or press Alt+A)",
                "step3": "Or go to: Tools -> Options -> Expert Advisors -> Enable algorithmic trading",
                "note": "The Python API cannot enable AutoTrading programmatically for security reasons."
            }
        }

    return {
        "account_id": account_id,
        "autotrading_enabled": True,
        "trade_allowed": True,
        "message": "AutoTrading is enabled"
    }

async def get_autotrading_status_from_worker(account_id: int) -> Dict[str, Any]:
    """Query worker process for AutoTrading status."""
    # Send command to worker
    await worker_pool_manager.send_command(account_id, {
        'type': 'check_autotrading'
    })

    # Wait for response
    # TODO: Implement response waiting

    return {'autotrading_enabled': True}  # Placeholder
```

### 4. Per-Currency Control

```python
@router.post("/accounts/{account_id}/currencies/{symbol}/enable")
async def enable_currency_trading(
    account_id: int,
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Enable trading for specific currency pair.

    Returns:
        {
            "success": bool,
            "account_id": int,
            "symbol": str,
            "enabled": bool
        }
    """
    # Update database
    currency_config = db.query(CurrencyConfiguration).filter(
        CurrencyConfiguration.symbol == symbol
    ).first()

    if not currency_config:
        raise HTTPException(404, f"Currency {symbol} not found in configuration")

    currency_config.enabled = True
    db.commit()

    # Send command to worker to reload config
    await worker_pool_manager.send_command(account_id, {
        'type': 'reload_currencies'
    })

    return {
        "success": True,
        "account_id": account_id,
        "symbol": symbol,
        "enabled": True
    }

@router.post("/accounts/{account_id}/currencies/{symbol}/disable")
async def disable_currency_trading(
    account_id: int,
    symbol: str,
    close_positions: bool = False,
    db: Session = Depends(get_db)
):
    """
    Disable trading for specific currency pair.

    Args:
        close_positions: If True, close all open positions for this currency

    Returns:
        {
            "success": bool,
            "account_id": int,
            "symbol": str,
            "enabled": bool,
            "positions_closed": int  # Only if close_positions=True
        }
    """
    pass
```

---

# Implementation Plan

## Phase 1: Configuration Refactor (Week 1)

### Day 1-2: Design & Schema
- [ ] Finalize configuration schema (defaults, accounts, currencies)
- [ ] Create Pydantic models for new config structure
- [ ] Write configuration loader with inheritance logic
- [ ] Create migration tool (v1 → v2 converter)

### Day 3-4: Implementation
- [ ] Implement `ConfigurationManagerV2` class
- [ ] Implement `ConfigMigrator` class
- [ ] Create factory function with auto-detect
- [ ] Add backward compatibility layer

### Day 5: Testing & Documentation
- [ ] Unit tests for config loading and inheritance
- [ ] Integration tests with existing code
- [ ] Update documentation
- [ ] Create migration guide for users

### Deliverables:
- `src/config/config_v2.py` - New config manager
- `src/config/config_migrator.py` - Migration tool
- `config/trading_config.yaml` - Example new format
- `docs/CONFIGURATION_V2.md` - Documentation
- Tests in `tests/config/test_config_v2.py`

## Phase 2: Worker Pool Architecture (Week 2-3)

### Day 1-3: Worker Process
- [ ] Implement `MT5Worker` class (process-based)
- [ ] Add IPC command handling
- [ ] Implement trading cycle execution in worker
- [ ] Add error handling and recovery
- [ ] Test single worker in isolation

### Day 4-6: Worker Pool Manager
- [ ] Implement `WorkerPoolManager` class
- [ ] Add worker lifecycle management (start/stop)
- [ ] Implement command queue per worker
- [ ] Add shared result queue with async reader
- [ ] Test multiple workers simultaneously

### Day 7-9: Integration
- [ ] Update `MT5SessionManagerV2` to use worker pool
- [ ] Update `TradingBotService` to use worker-based architecture
- [ ] Add worker health monitoring
- [ ] Implement graceful shutdown
- [ ] End-to-end testing with 2-3 accounts

### Day 10: Polish & Documentation
- [ ] Performance testing and optimization
- [ ] Memory leak checks
- [ ] Update architecture documentation
- [ ] Create troubleshooting guide

### Deliverables:
- `src/workers/mt5_worker.py` - Worker process
- `src/workers/worker_pool_manager.py` - Pool manager
- `src/services/session_manager_v2.py` - Updated session manager
- `src/services/trading_bot_service_v2.py` - Updated bot service
- `docs/WORKER_POOL_ARCHITECTURE.md` - Architecture docs
- Tests in `tests/workers/`

## Phase 3: Trading Control API (Week 4)

### Day 1-2: Core Endpoints
- [ ] Implement global trading start/stop endpoints
- [ ] Implement per-account trading control endpoints
- [ ] Add trading status endpoints
- [ ] Update OpenAPI documentation

### Day 3-4: AutoTrading Check
- [ ] Implement AutoTrading status check endpoint
- [ ] Add worker command for AutoTrading query
- [ ] Create response models with instructions
- [ ] Add UI warnings for disabled AutoTrading

### Day 5-6: Per-Currency Control
- [ ] Implement currency enable/disable endpoints
- [ ] Add dynamic currency configuration reload
- [ ] Implement position closing on disable
- [ ] Add currency status queries

### Day 7: Testing & Integration
- [ ] API endpoint tests
- [ ] Integration tests with worker pool
- [ ] Postman collection
- [ ] Update dashboard to use new endpoints

### Deliverables:
- `src/api/routes/trading_control.py` - Trading control endpoints
- `src/api/routes/autotrading.py` - AutoTrading endpoints
- `src/api/routes/currencies_v2.py` - Enhanced currency endpoints
- `docs/API_TRADING_CONTROL.md` - API documentation
- `postman/TradingMTQ_v2.json` - Postman collection
- Tests in `tests/api/test_trading_control.py`

---

# Migration Guide

## For Existing Users

### Step 1: Backup Current Configuration

```bash
cp config/currencies.yaml config/currencies_backup.yaml
```

### Step 2: Convert to New Format

```bash
tradingmtq config migrate \
  --input config/currencies.yaml \
  --output config/trading_config.yaml
```

### Step 3: Review & Customize

Edit `config/trading_config.yaml`:
- Review defaults
- Add additional account profiles if needed
- Customize per-currency settings

### Step 4: Update Environment

```bash
# Optional: Specify new config path
export TRADINGMTQ_CONFIG="config/trading_config.yaml"
```

### Step 5: Test

```bash
# Dry run to validate config
tradingmtq config validate

# Start trading with new config
tradingmtq trade --config config/trading_config.yaml
```

## For API Users

### Breaking Changes

1. **Session Manager** - Now uses worker pool, some methods renamed
2. **Trading Bot Service** - Account-based architecture, different initialization
3. **Configuration Loading** - New loader, backward compatible but with deprecation warnings

### Migration Steps

1. Update API client to use new endpoints:
   - `/trading/start` → Start global trading
   - `/accounts/{id}/trading/start` → Start account trading
   - `/accounts/{id}/autotrading/status` → Check AutoTrading

2. Update WebSocket event handlers:
   - New event types: `worker_started`, `worker_stopped`, `autotrading_disabled`

3. Test with single account before migrating all accounts

---

# Testing Strategy

## Unit Tests

### Configuration Tests
- Config loading with inheritance
- Default merging logic
- Migration v1 → v2
- Invalid config handling
- Schema validation

### Worker Tests
- Worker process lifecycle
- Command handling
- Result reporting
- Error recovery
- Graceful shutdown

### API Tests
- Trading control endpoints
- AutoTrading status checks
- Per-currency control
- Error responses
- Authorization

## Integration Tests

### Multi-Account Trading
- Start 3 accounts simultaneously
- Verify all stay connected
- Execute trades on different accounts
- Monitor resource usage

### Configuration Hot-Reload
- Change config while trading
- Verify only new cycles use new settings
- Test with multiple accounts

### Worker Pool Stress Test
- Start 10 workers
- Execute 100 cycles per worker
- Monitor for memory leaks
- Check queue performance

## Performance Tests

### Benchmarks
- Single worker throughput (cycles/sec)
- Multi-worker overhead
- IPC latency (command → result)
- Memory per worker
- CPU usage per worker

### Load Tests
- 5 accounts x 10 currencies = 50 traders
- Measure latency distribution
- Identify bottlenecks
- Optimize hot paths

---

# Rollback Plan

## If Configuration Refactor Fails

1. Keep old `ConfigurationManager` available as fallback
2. Factory auto-detects v1 format and uses old manager
3. No breaking changes for existing users

## If Worker Pool Fails

1. Keep current `TradingBotService` with in-process trading
2. Add feature flag: `USE_WORKER_POOL=false`
3. Gracefully fall back to single-account mode

## If API Changes Break Clients

1. Version API endpoints: `/v1/trading/...` vs `/v2/trading/...`
2. Maintain v1 endpoints during transition period
3. Provide migration guide with examples

---

# Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Multi-process debugging complexity | High | Medium | Add extensive logging, process monitoring tools |
| IPC queue bottleneck | Medium | Medium | Benchmark early, optimize if needed, use faster IPC (ZeroMQ) |
| Worker process crashes | Medium | High | Auto-restart, health checks, isolated error handling |
| Memory leaks in workers | Low | High | Regular testing, memory profiling, periodic worker restart |
| Configuration migration errors | Medium | Medium | Thorough validation, dry-run mode, keep old format support |
| Breaking API changes | Low | High | Versioned endpoints, comprehensive documentation |

---

# Success Criteria

## Phase 1: Configuration
- ✅ New config format supports inheritance
- ✅ Migration tool converts 100% of old configs
- ✅ Backward compatibility maintained
- ✅ All tests pass

## Phase 2: Worker Pool
- ✅ 5+ accounts trade simultaneously without disconnects
- ✅ Worker crash doesn't affect other accounts
- ✅ Performance: <100ms overhead per IPC roundtrip
- ✅ Memory: <150MB per worker process
- ✅ All tests pass

## Phase 3: API
- ✅ Start/stop trading via API works reliably
- ✅ AutoTrading check detects and reports status correctly
- ✅ Per-currency control works in real-time
- ✅ Dashboard shows accurate trading status
- ✅ All tests pass

---

**End of Design Document**

Ready for implementation? Review this design, provide feedback, and we can proceed with implementation in phases.
