"""
Configuration loader for TradingMTQ
Loads settings from YAML files and environment variables
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging


logger = logging.getLogger(__name__)


class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None, env_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to YAML config file
            env_file: Path to .env file
        """
        self._config: Dict[str, Any] = {}
        self._env_loaded = False
        
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
            self._env_loaded = True
        elif Path('.env').exists():
            load_dotenv('.env')
            self._env_loaded = True
        
        # Load YAML config
        if config_path and Path(config_path).exists():
            self.load_yaml(config_path)
        elif Path('config/mt5_config.yaml').exists():
            self.load_yaml('config/mt5_config.yaml')
    
    def load_yaml(self, config_path: str) -> None:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports nested keys with dots: 'mt5.trading.default_lot')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get environment variable
        
        Args:
            key: Environment variable name
            default: Default value
            
        Returns:
            Environment variable value
        """
        return os.getenv(key, default)
    
    def get_mt5_credentials(self) -> Dict[str, Any]:
        """Get MT5 connection credentials from environment"""
        return {
            'login': int(self.get_env('MT5_LOGIN', 0)),
            'password': self.get_env('MT5_PASSWORD', ''),
            'server': self.get_env('MT5_SERVER', '')
        }
    
    def get_mt5_config(self) -> Dict[str, Any]:
        """Get MT5 configuration section"""
        return self.get('mt5', {})
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration"""
        return self.get('mt5.trading', {})
    
    def get_symbols(self) -> list:
        """Get list of symbols to trade"""
        forex_symbols = self.get('mt5.symbols.forex', [])
        return forex_symbols
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return self.get('mt5.risk', {})
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.get(key)
    
    def __repr__(self) -> str:
        return f"Config(loaded={bool(self._config)}, env={self._env_loaded})"


# Global config instance
_global_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None, 
               env_file: Optional[str] = None) -> Config:
    """
    Get global configuration instance
    
    Args:
        config_path: Path to config file (only used on first call)
        env_file: Path to .env file (only used on first call)
        
    Returns:
        Config instance
    """
    global _global_config
    
    if _global_config is None:
        _global_config = Config(config_path, env_file)
    
    return _global_config
