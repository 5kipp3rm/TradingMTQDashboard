"""
Configuration Manager Service
Centralized configuration management for currencies, trading settings, and user preferences.
Supports both UI and CLI access with local storage persistence.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CurrencyConfig:
    """Configuration for a trading currency/symbol"""
    symbol: str
    description: str
    category: str
    digits: int
    point: float
    contract_size: int
    min_lot: float = 0.01
    max_lot: float = 100.0
    lot_step: float = 0.01
    spread_typical: float = 0.0
    enabled: bool = True
    custom: bool = False  # Whether user added this (vs default)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CurrencyConfig':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class TradingPreferences:
    """User trading preferences"""
    default_volume: float = 0.10
    default_sl_pips: Optional[float] = None
    default_tp_pips: Optional[float] = None
    max_risk_percent: float = 5.0
    max_daily_loss_percent: float = 10.0
    max_positions: int = 20
    favorite_symbols: List[str] = field(default_factory=list)
    recent_symbols: List[str] = field(default_factory=list)
    max_recent: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingPreferences':
        """Create from dictionary"""
        return cls(**data)


class ConfigManager:
    """
    Centralized configuration manager for TradingMTQ
    Manages currencies, trading preferences, and user settings
    """

    DEFAULT_CURRENCIES = [
        # Forex Majors
        CurrencyConfig(
            symbol='EURUSD',
            description='Euro vs US Dollar',
            category='Forex Majors',
            digits=5,
            point=0.00001,
            contract_size=100000,
            spread_typical=1.5,
            enabled=True
        ),
        CurrencyConfig(
            symbol='GBPUSD',
            description='British Pound vs US Dollar',
            category='Forex Majors',
            digits=5,
            point=0.00001,
            contract_size=100000,
            spread_typical=2.0,
            enabled=True
        ),
        CurrencyConfig(
            symbol='USDJPY',
            description='US Dollar vs Japanese Yen',
            category='Forex Majors',
            digits=3,
            point=0.001,
            contract_size=100000,
            spread_typical=1.5,
            enabled=True
        ),
        CurrencyConfig(
            symbol='USDCHF',
            description='US Dollar vs Swiss Franc',
            category='Forex Majors',
            digits=5,
            point=0.00001,
            contract_size=100000,
            spread_typical=2.0,
            enabled=True
        ),
        # Forex Minors
        CurrencyConfig(
            symbol='AUDUSD',
            description='Australian Dollar vs US Dollar',
            category='Forex Minors',
            digits=5,
            point=0.00001,
            contract_size=100000,
            spread_typical=2.0,
            enabled=True
        ),
        CurrencyConfig(
            symbol='USDCAD',
            description='US Dollar vs Canadian Dollar',
            category='Forex Minors',
            digits=5,
            point=0.00001,
            contract_size=100000,
            spread_typical=2.5,
            enabled=True
        ),
        CurrencyConfig(
            symbol='NZDUSD',
            description='New Zealand Dollar vs US Dollar',
            category='Forex Minors',
            digits=5,
            point=0.00001,
            contract_size=100000,
            spread_typical=2.5,
            enabled=True
        ),
        CurrencyConfig(
            symbol='EURGBP',
            description='Euro vs British Pound',
            category='Forex Minors',
            digits=5,
            point=0.00001,
            contract_size=100000,
            spread_typical=2.0,
            enabled=True
        ),
        CurrencyConfig(
            symbol='EURJPY',
            description='Euro vs Japanese Yen',
            category='Forex Minors',
            digits=3,
            point=0.001,
            contract_size=100000,
            spread_typical=2.0,
            enabled=True
        ),
        CurrencyConfig(
            symbol='GBPJPY',
            description='British Pound vs Japanese Yen',
            category='Forex Minors',
            digits=3,
            point=0.001,
            contract_size=100000,
            spread_typical=3.0,
            enabled=True
        ),
        # Commodities
        CurrencyConfig(
            symbol='XAUUSD',
            description='Gold vs US Dollar',
            category='Commodities',
            digits=2,
            point=0.01,
            contract_size=100,
            spread_typical=30,
            enabled=True
        ),
        CurrencyConfig(
            symbol='XAGUSD',
            description='Silver vs US Dollar',
            category='Commodities',
            digits=3,
            point=0.001,
            contract_size=5000,
            spread_typical=30,
            enabled=True
        ),
        CurrencyConfig(
            symbol='XTIUSD',
            description='WTI Crude Oil',
            category='Commodities',
            digits=2,
            point=0.01,
            contract_size=1000,
            spread_typical=30,
            enabled=True
        ),
        CurrencyConfig(
            symbol='XBRUSD',
            description='Brent Crude Oil',
            category='Commodities',
            digits=2,
            point=0.01,
            contract_size=1000,
            spread_typical=30,
            enabled=True
        ),
        # Indices
        CurrencyConfig(
            symbol='US30',
            description='Dow Jones Industrial Average',
            category='Indices',
            digits=2,
            point=0.01,
            contract_size=1,
            spread_typical=5,
            enabled=True
        ),
        CurrencyConfig(
            symbol='US500',
            description='S&P 500',
            category='Indices',
            digits=2,
            point=0.01,
            contract_size=1,
            spread_typical=5,
            enabled=True
        ),
        CurrencyConfig(
            symbol='NAS100',
            description='NASDAQ 100',
            category='Indices',
            digits=2,
            point=0.01,
            contract_size=1,
            spread_typical=5,
            enabled=True
        ),
        CurrencyConfig(
            symbol='GER40',
            description='German DAX',
            category='Indices',
            digits=2,
            point=0.01,
            contract_size=1,
            spread_typical=5,
            enabled=True
        ),
        # Cryptocurrencies (disabled by default)
        CurrencyConfig(
            symbol='BTCUSD',
            description='Bitcoin vs US Dollar',
            category='Crypto',
            digits=2,
            point=0.01,
            contract_size=1,
            min_lot=0.01,
            max_lot=10.0,
            spread_typical=50,
            enabled=False
        ),
        CurrencyConfig(
            symbol='ETHUSD',
            description='Ethereum vs US Dollar',
            category='Crypto',
            digits=2,
            point=0.01,
            contract_size=1,
            min_lot=0.01,
            max_lot=10.0,
            spread_typical=50,
            enabled=False
        ),
    ]

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration manager

        Args:
            config_file: Path to configuration file. Defaults to ~/.tradingmtq/config.json
        """
        if config_file is None:
            config_dir = Path.home() / '.tradingmtq'
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / 'config.json'

        self.config_file = config_file
        self.currencies: Dict[str, CurrencyConfig] = {}
        self.preferences = TradingPreferences()

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load configuration from file or initialize with defaults"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)

                # Load currencies
                currencies_data = data.get('currencies', {})
                for symbol, curr_data in currencies_data.items():
                    self.currencies[symbol] = CurrencyConfig.from_dict(curr_data)

                # Load preferences
                prefs_data = data.get('preferences', {})
                self.preferences = TradingPreferences.from_dict(prefs_data)

                logger.info(f"Loaded configuration from {self.config_file}")
                logger.info(f"Loaded {len(self.currencies)} currencies")

            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                logger.info("Initializing with default currencies")
                self._initialize_defaults()
        else:
            logger.info("No existing configuration found, initializing defaults")
            self._initialize_defaults()
            self.save()

    def _initialize_defaults(self):
        """Initialize with default currencies"""
        for currency in self.DEFAULT_CURRENCIES:
            currency.created_at = datetime.now().isoformat()
            currency.updated_at = datetime.now().isoformat()
            self.currencies[currency.symbol] = currency

        logger.info(f"Initialized {len(self.currencies)} default currencies")

    def save(self):
        """Save configuration to file"""
        try:
            data = {
                'currencies': {
                    symbol: curr.to_dict()
                    for symbol, curr in self.currencies.items()
                },
                'preferences': self.preferences.to_dict(),
                'updated_at': datetime.now().isoformat()
            }

            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Write configuration
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved configuration to {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    # Currency Management

    def get_currency(self, symbol: str) -> Optional[CurrencyConfig]:
        """Get currency configuration by symbol"""
        return self.currencies.get(symbol)

    def get_all_currencies(self, enabled_only: bool = False) -> List[CurrencyConfig]:
        """Get all currencies"""
        currencies = list(self.currencies.values())
        if enabled_only:
            currencies = [c for c in currencies if c.enabled]
        return sorted(currencies, key=lambda c: (c.category, c.symbol))

    def get_currencies_by_category(self, category: str, enabled_only: bool = False) -> List[CurrencyConfig]:
        """Get currencies by category"""
        currencies = [c for c in self.currencies.values() if c.category == category]
        if enabled_only:
            currencies = [c for c in currencies if c.enabled]
        return sorted(currencies, key=lambda c: c.symbol)

    def get_categories(self) -> List[str]:
        """Get all available categories"""
        categories = set(c.category for c in self.currencies.values())
        return sorted(categories)

    def add_currency(self, currency: CurrencyConfig) -> bool:
        """Add or update currency"""
        try:
            now = datetime.now().isoformat()

            if currency.symbol in self.currencies:
                # Update existing
                currency.updated_at = now
                logger.info(f"Updated currency: {currency.symbol}")
            else:
                # Add new
                currency.custom = True
                currency.created_at = now
                currency.updated_at = now
                logger.info(f"Added new currency: {currency.symbol}")

            self.currencies[currency.symbol] = currency
            self.save()
            return True

        except Exception as e:
            logger.error(f"Failed to add currency {currency.symbol}: {e}")
            return False

    def remove_currency(self, symbol: str) -> bool:
        """Remove currency (only custom currencies can be removed)"""
        try:
            currency = self.currencies.get(symbol)
            if not currency:
                logger.warning(f"Currency not found: {symbol}")
                return False

            if not currency.custom:
                logger.warning(f"Cannot remove default currency: {symbol}")
                return False

            del self.currencies[symbol]
            self.save()
            logger.info(f"Removed currency: {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove currency {symbol}: {e}")
            return False

    def enable_currency(self, symbol: str) -> bool:
        """Enable a currency"""
        return self._set_currency_enabled(symbol, True)

    def disable_currency(self, symbol: str) -> bool:
        """Disable a currency"""
        return self._set_currency_enabled(symbol, False)

    def _set_currency_enabled(self, symbol: str, enabled: bool) -> bool:
        """Set currency enabled status"""
        try:
            currency = self.currencies.get(symbol)
            if not currency:
                logger.warning(f"Currency not found: {symbol}")
                return False

            currency.enabled = enabled
            currency.updated_at = datetime.now().isoformat()
            self.save()

            status = "enabled" if enabled else "disabled"
            logger.info(f"Currency {symbol} {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to set currency {symbol} enabled={enabled}: {e}")
            return False

    # Trading Preferences Management

    def get_preferences(self) -> TradingPreferences:
        """Get trading preferences"""
        return self.preferences

    def update_preferences(self, **kwargs) -> bool:
        """Update trading preferences"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.preferences, key):
                    setattr(self.preferences, key, value)
                else:
                    logger.warning(f"Unknown preference: {key}")

            self.save()
            logger.info(f"Updated preferences: {kwargs.keys()}")
            return True

        except Exception as e:
            logger.error(f"Failed to update preferences: {e}")
            return False

    def add_favorite(self, symbol: str) -> bool:
        """Add symbol to favorites"""
        try:
            if symbol not in self.preferences.favorite_symbols:
                self.preferences.favorite_symbols.append(symbol)
                self.save()
                logger.info(f"Added {symbol} to favorites")
            return True
        except Exception as e:
            logger.error(f"Failed to add favorite {symbol}: {e}")
            return False

    def remove_favorite(self, symbol: str) -> bool:
        """Remove symbol from favorites"""
        try:
            if symbol in self.preferences.favorite_symbols:
                self.preferences.favorite_symbols.remove(symbol)
                self.save()
                logger.info(f"Removed {symbol} from favorites")
            return True
        except Exception as e:
            logger.error(f"Failed to remove favorite {symbol}: {e}")
            return False

    def add_recent(self, symbol: str) -> bool:
        """Add symbol to recent list"""
        try:
            # Remove if already exists
            if symbol in self.preferences.recent_symbols:
                self.preferences.recent_symbols.remove(symbol)

            # Add to front
            self.preferences.recent_symbols.insert(0, symbol)

            # Trim to max
            if len(self.preferences.recent_symbols) > self.preferences.max_recent:
                self.preferences.recent_symbols = self.preferences.recent_symbols[:self.preferences.max_recent]

            self.save()
            return True
        except Exception as e:
            logger.error(f"Failed to add recent {symbol}: {e}")
            return False

    def get_favorites(self) -> List[CurrencyConfig]:
        """Get favorite currencies"""
        return [
            self.currencies[symbol]
            for symbol in self.preferences.favorite_symbols
            if symbol in self.currencies
        ]

    def get_recent(self) -> List[CurrencyConfig]:
        """Get recent currencies"""
        return [
            self.currencies[symbol]
            for symbol in self.preferences.recent_symbols
            if symbol in self.currencies
        ]

    # Export/Import

    def export_config(self, file_path: Path) -> bool:
        """Export configuration to file"""
        try:
            data = {
                'currencies': {
                    symbol: curr.to_dict()
                    for symbol, curr in self.currencies.items()
                },
                'preferences': self.preferences.to_dict(),
                'exported_at': datetime.now().isoformat()
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported configuration to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False

    def import_config(self, file_path: Path, merge: bool = True) -> bool:
        """
        Import configuration from file

        Args:
            file_path: Path to import file
            merge: If True, merge with existing. If False, replace completely.
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            if not merge:
                # Replace completely
                self.currencies.clear()

            # Import currencies
            currencies_data = data.get('currencies', {})
            for symbol, curr_data in currencies_data.items():
                self.currencies[symbol] = CurrencyConfig.from_dict(curr_data)

            # Import preferences (always merge)
            prefs_data = data.get('preferences', {})
            for key, value in prefs_data.items():
                if hasattr(self.preferences, key):
                    setattr(self.preferences, key, value)

            self.save()
            logger.info(f"Imported configuration from {file_path}")
            logger.info(f"Total currencies: {len(self.currencies)}")
            return True

        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False

    # Statistics

    def get_stats(self) -> Dict[str, Any]:
        """Get configuration statistics"""
        categories = {}
        enabled_count = 0
        custom_count = 0

        for currency in self.currencies.values():
            # Count by category
            if currency.category not in categories:
                categories[currency.category] = {'total': 0, 'enabled': 0}
            categories[currency.category]['total'] += 1
            if currency.enabled:
                categories[currency.category]['enabled'] += 1
                enabled_count += 1

            # Count custom
            if currency.custom:
                custom_count += 1

        return {
            'total_currencies': len(self.currencies),
            'enabled_currencies': enabled_count,
            'disabled_currencies': len(self.currencies) - enabled_count,
            'custom_currencies': custom_count,
            'default_currencies': len(self.currencies) - custom_count,
            'categories': categories,
            'favorites_count': len(self.preferences.favorite_symbols),
            'recent_count': len(self.preferences.recent_symbols),
        }


# Global config manager instance (singleton)
_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global config manager instance"""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance
