"""
Unit tests for ConfigurationManager
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
from src.config_manager import ConfigurationManager


@pytest.fixture
def sample_config():
    """Sample configuration data"""
    return {
        'global': {
            'max_concurrent_trades': 10,
            'portfolio_risk_percent': 5.0,
            'interval_seconds': 30,
            'use_intelligent_position_manager': True,
            'use_ml_enhancement': True,
        },
        'currencies': {
            'EURUSD': {
                'enabled': True,
                'risk_percent': 1.0,
                'strategy_type': 'position',
                'timeframe': 'H1',
                'fast_period': 10,
                'slow_period': 20,
                'sl_pips': 20,
                'tp_pips': 40,
                'cooldown_seconds': 60,
            },
            'GBPUSD': {
                'enabled': False,
                'risk_percent': 0.8,
                'strategy_type': 'crossover',
                'timeframe': 'M15',
                'fast_period': 8,
                'slow_period': 21,
            }
        },
        'emergency': {
            'emergency_stop': False,
            'max_daily_loss_percent': 5.0,
        },
        'modifications': {
            'enable_breakeven': True,
            'breakeven_trigger_pips': 20,
            'enable_trailing_stop': True,
            'trailing_stop_pips': 15,
        }
    }


@pytest.fixture
def temp_config_file(sample_config):
    """Create temporary config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_config, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass


class TestConfigurationManager:
    """Test ConfigurationManager class"""
    
    def test_initialization(self, temp_config_file):
        """Test manager initialization"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.config is not None
        assert isinstance(manager.config, dict)
        # Config file should be set
        assert manager.config_file is not None
    
    def test_load_config(self, temp_config_file, sample_config):
        """Test config loading"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.config['global']['max_concurrent_trades'] == 10
        assert manager.config['currencies']['EURUSD']['enabled'] == True
    
    def test_get_max_concurrent_trades(self, temp_config_file):
        """Test getting max concurrent trades"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.get_max_concurrent_trades() == 10
    
    def test_get_portfolio_risk_percent(self, temp_config_file):
        """Test getting portfolio risk"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.get_portfolio_risk_percent() == 5.0
    
    def test_get_interval_seconds(self, temp_config_file):
        """Test getting interval"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.get_interval_seconds() == 30
    
    def test_get_enabled_currencies(self, temp_config_file):
        """Test getting enabled currencies"""
        manager = ConfigurationManager(temp_config_file)
        enabled = manager.get_enabled_currencies()
        assert len(enabled) == 1
        assert 'EURUSD' in enabled
        assert 'GBPUSD' not in enabled
    
    def test_get_currency_config(self, temp_config_file):
        """Test getting currency config"""
        manager = ConfigurationManager(temp_config_file)
        config = manager.get_currency_config('EURUSD')
        assert config['risk_percent'] == 1.0
        assert config['timeframe'] == 'H1'
        assert config['fast_period'] == 10
    
    def test_is_emergency_stop_active(self, temp_config_file):
        """Test emergency stop check"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.is_emergency_stop_active() == False
    
    def test_get_emergency_config(self, temp_config_file):
        """Test getting emergency config"""
        manager = ConfigurationManager(temp_config_file)
        emergency = manager.get_emergency_config()
        assert emergency['emergency_stop'] == False
        assert emergency['max_daily_loss_percent'] == 5.0
    
    def test_get_parallel_execution(self, temp_config_file):
        """Test getting parallel execution setting"""
        manager = ConfigurationManager(temp_config_file)
        # Default should be False if not specified
        parallel = manager.get_parallel_execution()
        assert isinstance(parallel, bool)
    
    def test_get_auto_reload_enabled(self, temp_config_file):
        """Test getting auto reload setting"""
        manager = ConfigurationManager(temp_config_file)
        auto_reload = manager.get_auto_reload_enabled()
        assert isinstance(auto_reload, bool)
    
    def test_get_trailing_stop_enabled(self, temp_config_file):
        """Test getting trailing stop setting"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.get_trailing_stop_enabled() == True
    
    def test_get_trailing_stop_pips(self, temp_config_file):
        """Test getting trailing stop pips"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.get_trailing_stop_pips() == 15
    
    def test_get_breakeven_enabled(self, temp_config_file):
        """Test getting breakeven setting"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.get_breakeven_enabled() == True
    
    def test_get_breakeven_trigger(self, temp_config_file):
        """Test getting breakeven trigger"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.get_breakeven_trigger() == 20
    
    def test_check_and_reload(self, temp_config_file, sample_config):
        """Test config reload detection"""
        manager = ConfigurationManager(temp_config_file)
        
        # First check - should not reload (file not modified)
        reloaded = manager.check_and_reload()
        assert reloaded == False
        
        # Modify file
        sample_config['global']['max_concurrent_trades'] = 20
        with open(temp_config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        # Wait a bit for file modification time to change
        import time
        time.sleep(0.1)
        
        # Check again - should reload
        reloaded = manager.check_and_reload()
        assert reloaded == True
        assert manager.get_max_concurrent_trades() == 20
    
    def test_missing_config_file(self):
        """Test handling of missing config file"""
        with pytest.raises(FileNotFoundError):
            ConfigurationManager('/nonexistent/config.yaml')
    
    def test_invalid_yaml(self):
        """Test handling of invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):
                ConfigurationManager(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_missing_currency_config(self, temp_config_file):
        """Test getting config for non-existent currency"""
        manager = ConfigurationManager(temp_config_file)
        config = manager.get_currency_config('NONEXISTENT')
        # Should return empty dict or None
        assert config is None or config == {}
    
    def test_defaults_when_missing(self, temp_config_file):
        """Test default values when keys missing"""
        manager = ConfigurationManager(temp_config_file)
        
        # Test defaults for missing values
        assert isinstance(manager.get_parallel_execution(), bool)
        assert isinstance(manager.get_auto_reload_enabled(), bool)
        assert manager.get_reload_interval() > 0
    
    def test_get_global_config(self, temp_config_file):
        """Test getting global config"""
        manager = ConfigurationManager(temp_config_file)
        global_config = manager.get_global_config()
        assert isinstance(global_config, dict)
        assert global_config.get('max_concurrent_trades') == 10
    
    def test_get_modifications_config(self, temp_config_file):
        """Test getting modifications config"""
        manager = ConfigurationManager(temp_config_file)
        mods = manager.get_modifications_config()
        assert isinstance(mods, dict)
        assert mods.get('enable_breakeven') == True
    
    def test_get_notifications_config(self, temp_config_file):
        """Test getting notifications config"""
        manager = ConfigurationManager(temp_config_file)
        notifications = manager.get_notifications_config()
        assert isinstance(notifications, dict)
    
    def test_get_logging_config(self, temp_config_file):
        """Test getting logging config"""
        manager = ConfigurationManager(temp_config_file)
        logging = manager.get_logging_config()
        assert isinstance(logging, dict)
    
    def test_get_all_currencies_config(self, temp_config_file):
        """Test getting all currencies config"""
        manager = ConfigurationManager(temp_config_file)
        currencies = manager.get_all_currencies_config()
        assert isinstance(currencies, dict)
        assert 'EURUSD' in currencies
        assert 'GBPUSD' in currencies
    
    def test_is_currency_enabled(self, temp_config_file):
        """Test checking if currency is enabled"""
        manager = ConfigurationManager(temp_config_file)
        assert manager.is_currency_enabled('EURUSD') == True
        assert manager.is_currency_enabled('GBPUSD') == False
        assert manager.is_currency_enabled('NONEXISTENT') == False
    
    def test_get_max_workers(self, temp_config_file):
        """Test getting max workers"""
        manager = ConfigurationManager(temp_config_file)
        workers = manager.get_max_workers()
        assert isinstance(workers, int)
        assert workers >= 1
    
    def test_get_currency_specific_values(self, temp_config_file):
        """Test getting currency-specific configuration values"""
        manager = ConfigurationManager(temp_config_file)
        
        # Test all currency-specific getters for EURUSD
        assert manager.get_currency_risk_percent('EURUSD') == 1.0
        assert manager.get_currency_sl_pips('EURUSD') == 20
        assert manager.get_currency_tp_pips('EURUSD') == 40
        assert manager.get_currency_strategy_type('EURUSD') == 'position'
        assert manager.get_currency_timeframe('EURUSD') == 'H1'
        assert manager.get_currency_fast_period('EURUSD') == 10
        assert manager.get_currency_slow_period('EURUSD') == 20
        assert manager.get_currency_cooldown('EURUSD') == 60
    
    def test_get_currency_defaults_for_nonexistent(self, temp_config_file):
        """Test default values for non-existent currency"""
        manager = ConfigurationManager(temp_config_file)
        
        # Should return defaults for non-existent currency
        assert manager.get_currency_risk_percent('NONEXISTENT') == 1.0
        assert manager.get_currency_sl_pips('NONEXISTENT') == 20
        assert manager.get_currency_tp_pips('NONEXISTENT') == 40
        assert manager.get_currency_strategy_type('NONEXISTENT') == 'position'
        assert manager.get_currency_timeframe('NONEXISTENT') == 'M5'
        assert manager.get_currency_fast_period('NONEXISTENT') == 10
        assert manager.get_currency_slow_period('NONEXISTENT') == 20
        assert manager.get_currency_cooldown('NONEXISTENT') == 60
    
    def test_get_breakeven_offset(self, temp_config_file):
        """Test getting breakeven offset"""
        manager = ConfigurationManager(temp_config_file)
        offset = manager.get_breakeven_offset()
        assert isinstance(offset, int)
    
    def test_check_and_reload_when_disabled(self, temp_config_file, sample_config):
        """Test check_and_reload when auto-reload is disabled"""
        # Disable auto-reload
        sample_config['global']['auto_reload_config'] = False
        with open(temp_config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        manager = ConfigurationManager(temp_config_file)
        
        # Modify file
        sample_config['global']['max_concurrent_trades'] = 99
        with open(temp_config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        # Should not reload because auto_reload is disabled
        reloaded = manager.check_and_reload()
        assert reloaded == False
        assert manager.get_max_concurrent_trades() != 99
    
    def test_repr(self, temp_config_file):
        """Test string representation"""
        manager = ConfigurationManager(temp_config_file)
        repr_str = repr(manager)
        assert 'ConfigurationManager' in repr_str
        assert 'enabled_currencies=1' in repr_str
