"""
Configuration loader for API keys and settings
Loads from config/api_keys.yaml with environment variable override
"""
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigLoader:
    """Load configuration from YAML files with env var override"""
    
    def __init__(self):
        # Go up from src/utils to project root
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / 'config'
        self._cache = {}
    
    def load_api_config(self) -> Dict[str, Any]:
        """Load API keys configuration"""
        if 'api_keys' in self._cache:
            return self._cache['api_keys']
        
        config_file = self.config_dir / 'api_keys.yaml'
        
        if not config_file.exists():
            return {}
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            self._cache['api_keys'] = config
            return config
        except Exception as e:
            print(f"Warning: Could not load API config: {e}")
            return {}
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key (env var > config file)"""
        # Check environment variable first
        env_key = os.getenv('OPENAI_API_KEY')
        if env_key:
            return env_key
        
        # Check config file
        config = self.load_api_config()
        return config.get('openai', {}).get('api_key') or None
    
    def get_anthropic_key(self) -> Optional[str]:
        """Get Anthropic API key (env var > config file)"""
        # Check environment variable first
        env_key = os.getenv('ANTHROPIC_API_KEY')
        if env_key:
            return env_key
        
        # Check config file
        config = self.load_api_config()
        return config.get('anthropic', {}).get('api_key') or None
    
    def get_openai_model(self) -> str:
        """Get default OpenAI model"""
        config = self.load_api_config()
        return config.get('openai', {}).get('default_model', 'gpt-4o-mini')
    
    def get_anthropic_model(self) -> str:
        """Get default Anthropic model"""
        config = self.load_api_config()
        return config.get('anthropic', {}).get('default_model', 'claude-3-sonnet-20240229')
    
    def get_telegram_config(self) -> Dict[str, str]:
        """Get Telegram bot configuration"""
        config = self.load_api_config()
        return config.get('telegram', {})
    
    def get_discord_webhook(self) -> Optional[str]:
        """Get Discord webhook URL"""
        config = self.load_api_config()
        return config.get('discord', {}).get('webhook_url')


# Global config loader instance
_config_loader = ConfigLoader()


def get_openai_key() -> Optional[str]:
    """Get OpenAI API key"""
    return _config_loader.get_openai_key()


def get_anthropic_key() -> Optional[str]:
    """Get Anthropic API key"""
    return _config_loader.get_anthropic_key()


def get_openai_model() -> str:
    """Get default OpenAI model"""
    return _config_loader.get_openai_model()


def get_anthropic_model() -> str:
    """Get default Anthropic model"""
    return _config_loader.get_anthropic_model()
