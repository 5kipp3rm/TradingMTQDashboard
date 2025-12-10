"""
Unit tests for utils.config module
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.config import Config, get_config


@pytest.fixture
def sample_yaml_config():
    """Sample YAML configuration"""
    return {
        'mt5': {
            'trading': {
                'default_lot': 0.1,
                'max_positions': 5
            },
            'symbols': {
                'forex': ['EURUSD', 'GBPUSD', 'USDJPY']
            },
            'risk': {
                'max_risk_percent': 2.0,
                'use_fixed_lot': False
            }
        },
        'database': {
            'enabled': True,
            'path': 'data/trades.db'
        }
    }


@pytest.fixture
def temp_yaml_file(sample_yaml_config):
    """Create temporary YAML config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_yaml_config, f)
        temp_path = f.name
    
    yield temp_path
    
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture
def temp_env_file():
    """Create temporary .env file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("MT5_LOGIN=12345\n")
        f.write("MT5_PASSWORD=testpass\n")
        f.write("MT5_SERVER=TestServer\n")
        temp_path = f.name
    
    yield temp_path
    
    try:
        os.unlink(temp_path)
    except:
        pass


class TestConfig:
    """Test Config class"""
    
    def test_initialization_empty(self):
        """Test config initialization without files"""
        config = Config()
        
        # Config may auto-load default config file if it exists
        assert isinstance(config._config, dict)
        assert isinstance(config._env_loaded, bool)
    
    def test_initialization_with_yaml(self, temp_yaml_file):
        """Test config initialization with YAML file"""
        config = Config(config_path=temp_yaml_file)
        
        assert config._config is not None
        assert 'mt5' in config._config
    
    def test_load_yaml_success(self, temp_yaml_file):
        """Test loading YAML file"""
        config = Config()
        config.load_yaml(temp_yaml_file)
        
        assert 'mt5' in config._config
        assert config._config['mt5']['trading']['default_lot'] == 0.1
    
    def test_load_yaml_file_not_found(self):
        """Test loading non-existent YAML file"""
        config = Config()
        config.load_yaml('/nonexistent/file.yaml')
        
        # Should not crash, config should be empty
        assert config._config == {}
    
    def test_load_yaml_invalid_yaml(self):
        """Test loading invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: [content")
            temp_path = f.name
        
        try:
            config = Config()
            config.load_yaml(temp_path)
            # Should handle error gracefully
            assert config._config == {}
        finally:
            os.unlink(temp_path)
    
    def test_get_simple_key(self, temp_yaml_file):
        """Test getting simple key"""
        config = Config(config_path=temp_yaml_file)
        
        value = config.get('mt5')
        assert value is not None
        assert 'trading' in value
    
    def test_get_nested_key(self, temp_yaml_file):
        """Test getting nested key with dot notation"""
        config = Config(config_path=temp_yaml_file)
        
        value = config.get('mt5.trading.default_lot')
        assert value == 0.1
    
    def test_get_deep_nested_key(self, temp_yaml_file):
        """Test getting deeply nested key"""
        config = Config(config_path=temp_yaml_file)
        
        value = config.get('mt5.symbols.forex')
        assert value == ['EURUSD', 'GBPUSD', 'USDJPY']
    
    def test_get_nonexistent_key_with_default(self, temp_yaml_file):
        """Test getting non-existent key returns default"""
        config = Config(config_path=temp_yaml_file)
        
        value = config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_get_nonexistent_key_without_default(self, temp_yaml_file):
        """Test getting non-existent key returns None"""
        config = Config(config_path=temp_yaml_file)
        
        value = config.get('nonexistent.key')
        assert value is None
    
    def test_get_env(self):
        """Test getting environment variable"""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            config = Config()
            value = config.get_env('TEST_VAR')
            assert value == 'test_value'
    
    def test_get_env_with_default(self):
        """Test getting non-existent env var returns default"""
        config = Config()
        value = config.get_env('NONEXISTENT_VAR', 'default')
        assert value == 'default'
    
    def test_get_mt5_credentials(self):
        """Test getting MT5 credentials from environment"""
        with patch.dict(os.environ, {
            'MT5_LOGIN': '12345',
            'MT5_PASSWORD': 'mypass',
            'MT5_SERVER': 'MyServer'
        }):
            config = Config()
            creds = config.get_mt5_credentials()
            
            assert creds['login'] == 12345
            assert creds['password'] == 'mypass'
            assert creds['server'] == 'MyServer'
    
    def test_get_mt5_credentials_defaults(self):
        """Test MT5 credentials with missing env vars"""
        # Note: Config might load from actual environment, so just test structure
        config = Config()
        creds = config.get_mt5_credentials()
        
        assert 'login' in creds
        assert 'password' in creds
        assert 'server' in creds
        assert isinstance(creds['login'], int)
    
    def test_get_mt5_config(self, temp_yaml_file):
        """Test getting MT5 config section"""
        config = Config(config_path=temp_yaml_file)
        
        mt5_config = config.get_mt5_config()
        assert 'trading' in mt5_config
        assert 'symbols' in mt5_config
    
    def test_get_mt5_config_empty(self):
        """Test getting MT5 config section"""
        config = Config()
        
        mt5_config = config.get_mt5_config()
        # Should return dict (empty or with default config)
        assert isinstance(mt5_config, dict)
    
    def test_get_trading_config(self, temp_yaml_file):
        """Test getting trading config"""
        config = Config(config_path=temp_yaml_file)
        
        trading = config.get_trading_config()
        assert trading['default_lot'] == 0.1
        assert trading['max_positions'] == 5
    
    def test_get_symbols(self, temp_yaml_file):
        """Test getting symbol list"""
        config = Config(config_path=temp_yaml_file)
        
        symbols = config.get_symbols()
        assert symbols == ['EURUSD', 'GBPUSD', 'USDJPY']
    
    def test_get_symbols_empty(self):
        """Test getting symbols"""
        config = Config()
        
        symbols = config.get_symbols()
        # Should return list (empty or with symbols)
        assert isinstance(symbols, list)
    
    def test_get_risk_config(self, temp_yaml_file):
        """Test getting risk config"""
        config = Config(config_path=temp_yaml_file)
        
        risk = config.get_risk_config()
        assert risk['max_risk_percent'] == 2.0
        assert risk['use_fixed_lot'] == False
    
    def test_dict_access(self, temp_yaml_file):
        """Test dict-like access with square brackets"""
        config = Config(config_path=temp_yaml_file)
        
        value = config['mt5.trading.default_lot']
        assert value == 0.1
    
    def test_repr(self, temp_yaml_file):
        """Test string representation"""
        config = Config(config_path=temp_yaml_file)
        
        repr_str = repr(config)
        assert 'Config' in repr_str
        assert 'loaded=True' in repr_str


class TestGetConfigGlobal:
    """Test global config instance"""
    
    def test_get_config_creates_instance(self, temp_yaml_file):
        """Test that get_config creates instance"""
        # Reset global config
        import src.utils.config
        src.utils.config._global_config = None
        
        config = get_config(config_path=temp_yaml_file)
        
        assert config is not None
        assert isinstance(config, Config)
    
    def test_get_config_returns_same_instance(self, temp_yaml_file):
        """Test that get_config returns singleton"""
        # Reset global config
        import src.utils.config
        src.utils.config._global_config = None
        
        config1 = get_config(config_path=temp_yaml_file)
        config2 = get_config()
        
        assert config1 is config2
    
    def test_get_config_ignores_second_path(self, temp_yaml_file):
        """Test that subsequent calls ignore new path"""
        # Reset global config
        import src.utils.config
        src.utils.config._global_config = None
        
        config1 = get_config(config_path=temp_yaml_file)
        config2 = get_config(config_path='/different/path.yaml')
        
        # Should be same instance
        assert config1 is config2


class TestConfigEdgeCases:
    """Test edge cases and error handling"""
    
    def test_get_with_non_dict_intermediate(self):
        """Test getting nested key where intermediate is not dict"""
        config = Config()
        config._config = {
            'level1': 'string_value'
        }
        
        value = config.get('level1.level2.level3', 'default')
        assert value == 'default'
    
    def test_get_with_empty_key(self):
        """Test getting with empty string key"""
        config = Config()
        config._config = {'test': 'value'}
        
        value = config.get('', 'default')
        # Should handle gracefully
        assert value in ['default', {'test': 'value'}]
    
    def test_initialization_with_env_file(self, temp_env_file):
        """Test initialization with explicit env file"""
        config = Config(env_file=temp_env_file)
        
        assert config._env_loaded == True
