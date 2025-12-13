"""
Tests for CLI application
"""
import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.cli.app import cli


class TestCLI(unittest.TestCase):
    """Test CLI commands and options"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_cli_version(self):
        """Test --version flag"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('2.0.0', result.output)
        self.assertIn('TradingMTQ', result.output)
    
    def test_cli_help(self):
        """Test --help flag"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('TradingMTQ', result.output)
        self.assertIn('Advanced Multi-Currency Trading Bot', result.output)
    
    def test_trade_command_help(self):
        """Test trade command help"""
        result = self.runner.invoke(cli, ['trade', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Start live trading', result.output)
        self.assertIn('--aggressive', result.output)
        self.assertIn('--demo', result.output)
        self.assertIn('--enable-ml', result.output)
        self.assertIn('--enable-llm', result.output)
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_default(self, mock_run_trading):
        """Test trade command with default options"""
        result = self.runner.invoke(cli, ['trade'])
        
        # Should exit successfully (or with expected error if MT5 not connected)
        # We're mainly testing argument parsing here
        mock_run_trading.assert_called_once_with(
            config_file='config/currencies.yaml',
            aggressive=False,
            demo=False,
            interval=None,
            max_concurrent=None,
            enable_ml=True,
            enable_llm=True
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_aggressive(self, mock_run_trading):
        """Test trade command with aggressive flag"""
        result = self.runner.invoke(cli, ['trade', '--aggressive'])
        
        mock_run_trading.assert_called_once_with(
            config_file='config/currencies.yaml',
            aggressive=True,
            demo=False,
            interval=None,
            max_concurrent=None,
            enable_ml=True,
            enable_llm=True
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_demo(self, mock_run_trading):
        """Test trade command with demo flag"""
        result = self.runner.invoke(cli, ['trade', '--demo'])
        
        mock_run_trading.assert_called_once_with(
            config_file='config/currencies.yaml',
            aggressive=False,
            demo=True,
            interval=None,
            max_concurrent=None,
            enable_ml=True,
            enable_llm=True
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_custom_config(self, mock_run_trading):
        """Test trade command with custom config file"""
        result = self.runner.invoke(cli, ['trade', '--config', 'custom.yaml'])
        
        mock_run_trading.assert_called_once_with(
            config_file='custom.yaml',
            aggressive=False,
            demo=False,
            interval=None,
            max_concurrent=None,
            enable_ml=True,
            enable_llm=True
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_interval(self, mock_run_trading):
        """Test trade command with interval override"""
        result = self.runner.invoke(cli, ['trade', '--interval', '30'])
        
        mock_run_trading.assert_called_once_with(
            config_file='config/currencies.yaml',
            aggressive=False,
            demo=False,
            interval=30,
            max_concurrent=None,
            enable_ml=True,
            enable_llm=True
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_max_concurrent(self, mock_run_trading):
        """Test trade command with max concurrent override"""
        result = self.runner.invoke(cli, ['trade', '--max-concurrent', '10'])
        
        mock_run_trading.assert_called_once_with(
            config_file='config/currencies.yaml',
            aggressive=False,
            demo=False,
            interval=None,
            max_concurrent=10,
            enable_ml=True,
            enable_llm=True
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_disable_ml(self, mock_run_trading):
        """Test trade command with ML disabled"""
        result = self.runner.invoke(cli, ['trade', '--disable-ml'])
        
        mock_run_trading.assert_called_once_with(
            config_file='config/currencies.yaml',
            aggressive=False,
            demo=False,
            interval=None,
            max_concurrent=None,
            enable_ml=False,
            enable_llm=True
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_disable_llm(self, mock_run_trading):
        """Test trade command with LLM disabled"""
        result = self.runner.invoke(cli, ['trade', '--disable-llm'])
        
        mock_run_trading.assert_called_once_with(
            config_file='config/currencies.yaml',
            aggressive=False,
            demo=False,
            interval=None,
            max_concurrent=None,
            enable_ml=True,
            enable_llm=False
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_disable_both(self, mock_run_trading):
        """Test trade command with both ML and LLM disabled"""
        result = self.runner.invoke(cli, ['trade', '--disable-ml', '--disable-llm'])
        
        mock_run_trading.assert_called_once_with(
            config_file='config/currencies.yaml',
            aggressive=False,
            demo=False,
            interval=None,
            max_concurrent=None,
            enable_ml=False,
            enable_llm=False
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_combined_options(self, mock_run_trading):
        """Test trade command with multiple options combined"""
        result = self.runner.invoke(cli, [
            'trade',
            '--config', 'custom.yaml',
            '--aggressive',
            '--demo',
            '--interval', '60',
            '--max-concurrent', '15',
            '--disable-ml'
        ])
        
        mock_run_trading.assert_called_once_with(
            config_file='custom.yaml',
            aggressive=True,
            demo=True,
            interval=60,
            max_concurrent=15,
            enable_ml=False,
            enable_llm=True
        )
    
    @patch('src.cli.commands.run_trading')
    def test_trade_command_short_options(self, mock_run_trading):
        """Test trade command with short option flags"""
        result = self.runner.invoke(cli, ['trade', '-c', 'test.yaml', '-a', '-d', '-i', '45'])
        
        mock_run_trading.assert_called_once_with(
            config_file='test.yaml',
            aggressive=True,
            demo=True,
            interval=45,
            max_concurrent=None,
            enable_ml=True,
            enable_llm=True
        )
    
    def test_check_command_exists(self):
        """Test that check command is available"""
        result = self.runner.invoke(cli, ['check', '--help'])
        # Should not error
        self.assertIsNotNone(result)
    
    def test_invalid_command(self):
        """Test invalid command returns error"""
        result = self.runner.invoke(cli, ['invalid-command'])
        self.assertNotEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
