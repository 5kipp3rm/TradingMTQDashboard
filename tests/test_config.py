"""
Tests for configuration loader
"""
import pytest
import os
from pathlib import Path
from src.utils.config import Config


def test_config_get():
    """Test getting configuration values"""
    config = Config()
    
    # Test default value
    assert config.get('nonexistent.key', 'default') == 'default'


def test_config_get_env():
    """Test getting environment variables"""
    os.environ['TEST_VAR'] = 'test_value'
    
    config = Config()
    assert config.get_env('TEST_VAR') == 'test_value'
    assert config.get_env('NONEXISTENT', 'default') == 'default'
    
    # Cleanup
    del os.environ['TEST_VAR']


def test_config_dict_access():
    """Test dictionary-like access"""
    config = Config()
    
    # Should not raise error, should return None
    result = config['nonexistent.key']
    assert result is None


def test_mt5_credentials():
    """Test getting MT5 credentials"""
    os.environ['MT5_LOGIN'] = '12345'
    os.environ['MT5_PASSWORD'] = 'testpass'
    os.environ['MT5_SERVER'] = 'TestServer'
    
    config = Config()
    credentials = config.get_mt5_credentials()
    
    assert credentials['login'] == 12345
    assert credentials['password'] == 'testpass'
    assert credentials['server'] == 'TestServer'
    
    # Cleanup
    for key in ['MT5_LOGIN', 'MT5_PASSWORD', 'MT5_SERVER']:
        if key in os.environ:
            del os.environ[key]
