"""
Configuration Manager - Loads and reloads trading configuration
Supports hot-reload for on-the-fly modifications
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import os


class ConfigurationManager:
    """
    Manages trading configuration with hot-reload support
    """
    
    def __init__(self, config_file: str = "config/currencies.yaml"):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.last_modified: Optional[float] = None
        self.last_reload: Optional[datetime] = None
        
        # Load initial configuration
        self.reload()
    
    def reload(self) -> bool:
        """
        Reload configuration from file
        
        Returns:
            True if configuration was reloaded, False if unchanged
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        # Check if file was modified
        current_mtime = os.path.getmtime(self.config_file)
        if self.last_modified is not None and current_mtime == self.last_modified:
            return False  # No changes
        
        # Load YAML
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.last_modified = current_mtime
        self.last_reload = datetime.now()
        
        print(f"✓ Configuration reloaded from {self.config_file}")
        return True
    
    def check_and_reload(self) -> bool:
        """
        Check if config file changed and reload if needed
        
        Returns:
            True if reloaded, False otherwise
        """
        if not self.get_auto_reload_enabled():
            return False
        
        return self.reload()
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration settings"""
        return self.config.get('global', {})
    
    def get_emergency_config(self) -> Dict[str, Any]:
        """Get emergency control settings"""
        return self.config.get('emergency', {})
    
    def get_modifications_config(self) -> Dict[str, Any]:
        """Get position modification rules"""
        return self.config.get('modifications', {})
    
    def get_notifications_config(self) -> Dict[str, Any]:
        """Get notification settings"""
        return self.config.get('notifications', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get('logging', {})
    
    def get_currency_config(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific currency
        
        Args:
            symbol: Currency symbol (e.g., 'EURUSD')
            
        Returns:
            Currency configuration or None if not found
        """
        currencies = self.config.get('currencies', {})
        return currencies.get(symbol)
    
    def get_enabled_currencies(self) -> List[str]:
        """
        Get list of enabled currency symbols
        
        Returns:
            List of enabled currency symbols
        """
        currencies = self.config.get('currencies', {})
        return [
            symbol for symbol, config in currencies.items()
            if config.get('enabled', False)
        ]
    
    def get_all_currencies_config(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all currencies"""
        return self.config.get('currencies', {})
    
    def is_currency_enabled(self, symbol: str) -> bool:
        """
        Check if a currency is enabled for trading
        
        Args:
            symbol: Currency symbol
            
        Returns:
            True if enabled, False otherwise
        """
        config = self.get_currency_config(symbol)
        return config.get('enabled', False) if config else False
    
    def is_emergency_stop_active(self) -> bool:
        """Check if emergency stop is activated"""
        emergency = self.get_emergency_config()
        return emergency.get('emergency_stop', False)
    
    def get_auto_reload_enabled(self) -> bool:
        """Check if auto-reload is enabled"""
        global_config = self.get_global_config()
        return global_config.get('auto_reload_config', True)
    
    def get_reload_interval(self) -> int:
        """Get config reload check interval in seconds"""
        global_config = self.get_global_config()
        return global_config.get('reload_check_interval', 60)
    
    def get_max_concurrent_trades(self) -> int:
        """Get maximum concurrent trades limit"""
        global_config = self.get_global_config()
        return global_config.get('max_concurrent_trades', 5)
    
    def get_portfolio_risk_percent(self) -> float:
        """Get portfolio risk percentage limit"""
        global_config = self.get_global_config()
        return global_config.get('portfolio_risk_percent', 10.0)
    
    def get_interval_seconds(self) -> int:
        """Get trading cycle interval in seconds"""
        global_config = self.get_global_config()
        return global_config.get('interval_seconds', 30)
    
    def get_parallel_execution(self) -> bool:
        """Check if parallel execution is enabled"""
        global_config = self.get_global_config()
        return global_config.get('parallel_execution', False)
    
    def get_max_workers(self) -> int:
        """Get maximum parallel workers"""
        global_config = self.get_global_config()
        return global_config.get('max_workers', 3)
    
    def get_currency_risk_percent(self, symbol: str) -> float:
        """Get risk percentage for a currency"""
        config = self.get_currency_config(symbol)
        return config.get('risk_percent', 1.0) if config else 1.0
    
    def get_currency_sl_pips(self, symbol: str) -> int:
        """Get stop loss in pips for a currency"""
        config = self.get_currency_config(symbol)
        return config.get('sl_pips', 20) if config else 20
    
    def get_currency_tp_pips(self, symbol: str) -> int:
        """Get take profit in pips for a currency"""
        config = self.get_currency_config(symbol)
        return config.get('tp_pips', 40) if config else 40
    
    def get_currency_strategy_type(self, symbol: str) -> str:
        """Get strategy type for a currency"""
        config = self.get_currency_config(symbol)
        return config.get('strategy_type', 'position') if config else 'position'
    
    def get_currency_timeframe(self, symbol: str) -> str:
        """Get timeframe for a currency"""
        config = self.get_currency_config(symbol)
        return config.get('timeframe', 'M5') if config else 'M5'
    
    def get_currency_fast_period(self, symbol: str) -> int:
        """Get fast MA period for a currency"""
        config = self.get_currency_config(symbol)
        return config.get('fast_period', 10) if config else 10
    
    def get_currency_slow_period(self, symbol: str) -> int:
        """Get slow MA period for a currency"""
        config = self.get_currency_config(symbol)
        return config.get('slow_period', 20) if config else 20
    
    def get_currency_cooldown(self, symbol: str) -> int:
        """Get cooldown seconds for a currency"""
        config = self.get_currency_config(symbol)
        return config.get('cooldown_seconds', 60) if config else 60
    
    def get_trailing_stop_enabled(self) -> bool:
        """Check if trailing stop is enabled"""
        mods = self.get_modifications_config()
        return mods.get('enable_trailing_stop', False)
    
    def get_trailing_stop_pips(self) -> int:
        """Get trailing stop distance in pips"""
        mods = self.get_modifications_config()
        return mods.get('trailing_stop_pips', 15)
    
    def get_breakeven_enabled(self) -> bool:
        """Check if breakeven is configured"""
        mods = self.get_modifications_config()
        return mods.get('breakeven_trigger_pips', 0) > 0
    
    def get_breakeven_trigger(self) -> int:
        """Get breakeven trigger in pips"""
        mods = self.get_modifications_config()
        return mods.get('breakeven_trigger_pips', 20)
    
    def get_breakeven_offset(self) -> int:
        """Get breakeven offset in pips"""
        mods = self.get_modifications_config()
        return mods.get('breakeven_offset_pips', 2)
    
    def __repr__(self) -> str:
        enabled = len(self.get_enabled_currencies())
        return f"ConfigurationManager(file={self.config_file}, enabled_currencies={enabled})"
