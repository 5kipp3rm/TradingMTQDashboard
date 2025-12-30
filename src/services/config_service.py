"""
Configuration Service

Handles synchronization between database and YAML configuration files.
Provides dual persistence: all changes are saved to both database and YAML.
Supports hot-reload for configuration changes without restarting the application.
"""

import os
import yaml
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import CurrencyConfiguration, get_session
from src.utils.unified_logger import UnifiedLogger

logger = UnifiedLogger.get_logger(__name__)


class ConfigurationService:
    """
    Configuration Service for dual persistence (Database + YAML)

    Responsibilities:
    - Sync currency configurations between database and YAML file
    - Hot-reload configuration changes
    - Validate configuration consistency
    - Export/import configurations
    """

    def __init__(self, yaml_path: str = "config/currencies.yaml"):
        """
        Initialize ConfigurationService

        Args:
            yaml_path: Path to YAML configuration file
        """
        self.yaml_path = Path(yaml_path)
        self.logger = logger

        # Ensure config directory exists
        self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

    def load_from_database(self, db: Session) -> List[CurrencyConfiguration]:
        """
        Load all currency configurations from database

        Args:
            db: Database session

        Returns:
            List of currency configurations
        """
        result = db.execute(select(CurrencyConfiguration).order_by(CurrencyConfiguration.symbol))
        configs = result.scalars().all()

        self.logger.info(f"Loaded {len(configs)} currency configurations from database")
        return configs

    def load_from_yaml(self) -> Dict:
        """
        Load configuration from YAML file

        Returns:
            Dictionary containing YAML configuration

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            yaml.YAMLError: If YAML file is invalid
        """
        if not self.yaml_path.exists():
            self.logger.warning(f"YAML configuration file not found: {self.yaml_path}")
            return {"currencies": {}}

        try:
            with open(self.yaml_path, 'r') as f:
                config = yaml.safe_load(f) or {}

            currency_count = len(config.get('currencies', {}))
            self.logger.info(f"Loaded {currency_count} currencies from YAML: {self.yaml_path}")
            return config

        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading YAML file: {e}")
            raise

    def save_to_yaml(self, db: Session) -> bool:
        """
        Save all currency configurations from database to YAML file

        Args:
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load current YAML to preserve non-currency settings
            if self.yaml_path.exists():
                with open(self.yaml_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = self._get_default_yaml_structure()

            # Get all currencies from database
            currencies = self.load_from_database(db)

            # Convert to YAML format
            currencies_dict = {}
            for curr in currencies:
                currencies_dict[curr.symbol] = {
                    'enabled': curr.enabled,
                    'risk_percent': curr.risk_percent,
                    'max_position_size': curr.max_position_size,
                    'min_position_size': curr.min_position_size,
                    'strategy_type': curr.strategy_type,
                    'timeframe': curr.timeframe,
                    'fast_period': curr.fast_period,
                    'slow_period': curr.slow_period,
                    'sl_pips': curr.sl_pips,
                    'tp_pips': curr.tp_pips,
                    'cooldown_seconds': curr.cooldown_seconds,
                    'trade_on_signal_change': curr.trade_on_signal_change,
                    'allow_position_stacking': curr.allow_position_stacking,
                    'max_positions_same_direction': curr.max_positions_same_direction,
                    'max_total_positions': curr.max_total_positions,
                    'stacking_risk_multiplier': curr.stacking_risk_multiplier,
                }

                # Add optional fields if present
                if curr.trading_hours_start:
                    currencies_dict[curr.symbol]['trading_hours'] = {
                        'start': curr.trading_hours_start,
                        'end': curr.trading_hours_end
                    }

                if curr.description:
                    currencies_dict[curr.symbol]['description'] = curr.description

            # Update currencies section
            config['currencies'] = currencies_dict

            # Write to YAML file
            with open(self.yaml_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

            self.logger.info(f"Saved {len(currencies)} currencies to YAML: {self.yaml_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save to YAML: {e}", exc_info=True)
            return False

    def sync_yaml_to_database(self, db: Session) -> Tuple[int, int, List[str]]:
        """
        Sync currency configurations from YAML to database

        Adds new currencies from YAML that don't exist in database.
        Updates existing currencies if YAML has different values.
        Does NOT delete currencies from database that aren't in YAML.

        Args:
            db: Database session

        Returns:
            Tuple of (added_count, updated_count, errors)
        """
        try:
            yaml_config = self.load_from_yaml()
            currencies_yaml = yaml_config.get('currencies', {})

            added_count = 0
            updated_count = 0
            errors = []

            for symbol, config_data in currencies_yaml.items():
                try:
                    # Check if currency exists in database
                    existing = db.execute(
                        select(CurrencyConfiguration).where(CurrencyConfiguration.symbol == symbol)
                    ).scalar_one_or_none()

                    if existing:
                        # Update existing currency
                        updated = False

                        # Check each field for changes
                        if existing.enabled != config_data.get('enabled', True):
                            existing.enabled = config_data.get('enabled', True)
                            updated = True

                        if existing.risk_percent != config_data.get('risk_percent'):
                            existing.risk_percent = config_data.get('risk_percent', 1.0)
                            updated = True

                        # Add more field checks as needed...

                        if updated:
                            existing.config_version += 1
                            existing.updated_at = datetime.utcnow()
                            updated_count += 1
                            self.logger.info(f"Updated currency from YAML: {symbol}")

                    else:
                        # Add new currency
                        new_currency = CurrencyConfiguration(
                            symbol=symbol,
                            enabled=config_data.get('enabled', True),
                            risk_percent=config_data.get('risk_percent', 1.0),
                            max_position_size=config_data.get('max_position_size', 1.0),
                            min_position_size=config_data.get('min_position_size', 0.01),
                            strategy_type=config_data.get('strategy_type', 'position'),
                            timeframe=config_data.get('timeframe', 'M15'),
                            fast_period=config_data.get('fast_period', 10),
                            slow_period=config_data.get('slow_period', 20),
                            sl_pips=config_data.get('sl_pips', 20),
                            tp_pips=config_data.get('tp_pips', 40),
                            cooldown_seconds=config_data.get('cooldown_seconds', 60),
                            trade_on_signal_change=config_data.get('trade_on_signal_change', True),
                            allow_position_stacking=config_data.get('allow_position_stacking', False),
                            max_positions_same_direction=config_data.get('max_positions_same_direction', 1),
                            max_total_positions=config_data.get('max_total_positions', 5),
                            stacking_risk_multiplier=config_data.get('stacking_risk_multiplier', 1.0),
                        )

                        # Handle trading hours if present
                        trading_hours = config_data.get('trading_hours')
                        if trading_hours:
                            new_currency.trading_hours_start = trading_hours.get('start')
                            new_currency.trading_hours_end = trading_hours.get('end')

                        # Validate before adding
                        is_valid, validation_errors = new_currency.validate()
                        if not is_valid:
                            errors.append(f"{symbol}: {', '.join(validation_errors)}")
                            continue

                        db.add(new_currency)
                        added_count += 1
                        self.logger.info(f"Added new currency from YAML: {symbol}")

                except Exception as e:
                    error_msg = f"Error processing {symbol}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            db.commit()

            self.logger.info(f"YAML sync complete: {added_count} added, {updated_count} updated, {len(errors)} errors")
            return (added_count, updated_count, errors)

        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to sync YAML to database: {e}", exc_info=True)
            return (0, 0, [str(e)])

    def sync_database_to_yaml(self, db: Session) -> bool:
        """
        Sync currency configurations from database to YAML

        This is an alias for save_to_yaml() for consistency.

        Args:
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        return self.save_to_yaml(db)

    def export_to_file(self, db: Session, export_path: str) -> bool:
        """
        Export current database configuration to a file

        Args:
            db: Database session
            export_path: Path to export file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save current yaml_path
            original_path = self.yaml_path

            # Temporarily set export path
            self.yaml_path = Path(export_path)

            # Export
            result = self.save_to_yaml(db)

            # Restore original path
            self.yaml_path = original_path

            if result:
                self.logger.info(f"Exported configuration to: {export_path}")

            return result

        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False

    def import_from_file(self, db: Session, import_path: str) -> Tuple[int, int, List[str]]:
        """
        Import configuration from a file

        Args:
            db: Database session
            import_path: Path to import file

        Returns:
            Tuple of (added_count, updated_count, errors)
        """
        try:
            # Save current yaml_path
            original_path = self.yaml_path

            # Temporarily set import path
            self.yaml_path = Path(import_path)

            # Import
            result = self.sync_yaml_to_database(db)

            # Restore original path
            self.yaml_path = original_path

            self.logger.info(f"Imported configuration from: {import_path}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return (0, 0, [str(e)])

    def validate_consistency(self, db: Session) -> Tuple[bool, List[str]]:
        """
        Validate consistency between database and YAML

        Args:
            db: Database session

        Returns:
            Tuple of (is_consistent, differences)
        """
        try:
            db_currencies = {c.symbol: c for c in self.load_from_database(db)}
            yaml_config = self.load_from_yaml()
            yaml_currencies = set(yaml_config.get('currencies', {}).keys())

            differences = []

            # Check for currencies in DB but not in YAML
            for symbol in db_currencies.keys():
                if symbol not in yaml_currencies:
                    differences.append(f"Currency {symbol} exists in database but not in YAML")

            # Check for currencies in YAML but not in DB
            for symbol in yaml_currencies:
                if symbol not in db_currencies:
                    differences.append(f"Currency {symbol} exists in YAML but not in database")

            is_consistent = len(differences) == 0

            if is_consistent:
                self.logger.info("Configuration is consistent between database and YAML")
            else:
                self.logger.warning(f"Found {len(differences)} configuration inconsistencies")

            return (is_consistent, differences)

        except Exception as e:
            self.logger.error(f"Failed to validate consistency: {e}")
            return (False, [str(e)])

    def _get_default_yaml_structure(self) -> Dict:
        """
        Get default YAML configuration structure

        Returns:
            Dictionary with default structure
        """
        return {
            'global': {
                'max_concurrent_trades': 15,
                'portfolio_risk_percent': 8.0,
                'interval_seconds': 30,
                'parallel_execution': False,
                'auto_reload_config': True,
                'reload_check_interval': 60,
            },
            'currencies': {},
            'emergency': {
                'emergency_stop': False,
                'close_all_on_stop': True,
                'max_daily_loss_percent': 5.0,
                'stop_on_daily_loss': True,
            },
            'modifications': {
                'enable_breakeven': True,
                'breakeven_trigger_pips': 30,
                'breakeven_offset_pips': 5,
                'enable_trailing_stop': True,
                'trailing_stop_pips': 20,
            },
        }


# Singleton instance
_config_service: Optional[ConfigurationService] = None


def get_config_service(yaml_path: str = "config/currencies.yaml") -> ConfigurationService:
    """
    Get or create ConfigurationService singleton instance

    Args:
        yaml_path: Path to YAML configuration file

    Returns:
        ConfigurationService instance
    """
    global _config_service

    if _config_service is None:
        _config_service = ConfigurationService(yaml_path)

    return _config_service
