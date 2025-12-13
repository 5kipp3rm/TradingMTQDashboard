"""
Tests for logger utility
"""
import unittest
import logging
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from src.utils.logger import ColoredFormatter, setup_logging, get_logger, log_config


class TestColoredFormatter(unittest.TestCase):
    """Test ColoredFormatter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.formatter = ColoredFormatter('%(levelname)s - %(message)s')
    
    def test_format_debug_level(self):
        """Test formatting DEBUG level message"""
        record = logging.LogRecord(
            name='test', level=logging.DEBUG, pathname='', lineno=0,
            msg='debug message', args=(), exc_info=None
        )
        
        result = self.formatter.format(record)
        
        self.assertIn('debug message', result)
        self.assertIn('🔍', result)
    
    def test_format_info_level(self):
        """Test formatting INFO level message"""
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='info message', args=(), exc_info=None
        )
        
        result = self.formatter.format(record)
        
        self.assertIn('info message', result)
        self.assertIn('✓', result)
    
    def test_format_warning_level(self):
        """Test formatting WARNING level message"""
        record = logging.LogRecord(
            name='test', level=logging.WARNING, pathname='', lineno=0,
            msg='warning message', args=(), exc_info=None
        )
        
        result = self.formatter.format(record)
        
        self.assertIn('warning message', result)
        self.assertIn('⚠️', result)
    
    def test_format_error_level(self):
        """Test formatting ERROR level message"""
        record = logging.LogRecord(
            name='test', level=logging.ERROR, pathname='', lineno=0,
            msg='error message', args=(), exc_info=None
        )
        
        result = self.formatter.format(record)
        
        self.assertIn('error message', result)
        self.assertIn('✗', result)
    
    def test_format_critical_level(self):
        """Test formatting CRITICAL level message"""
        record = logging.LogRecord(
            name='test', level=logging.CRITICAL, pathname='', lineno=0,
            msg='critical message', args=(), exc_info=None
        )
        
        result = self.formatter.format(record)
        
        self.assertIn('critical message', result)
        self.assertIn('🚨', result)
    
    def test_format_with_symbol(self):
        """Test formatting message with symbol"""
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='trade executed', args=(), exc_info=None
        )
        record.symbol = 'EURUSD'
        
        result = self.formatter.format(record)
        
        self.assertIn('EURUSD', result)
        self.assertIn('trade executed', result)
    
    def test_format_with_custom_icon(self):
        """Test formatting message with custom icon"""
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='profit target', args=(), exc_info=None
        )
        record.custom_icon = '💰'
        
        result = self.formatter.format(record)
        
        self.assertIn('💰', result)
        self.assertIn('profit target', result)
    
    def test_format_with_symbol_and_icon(self):
        """Test formatting message with both symbol and custom icon"""
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='stop loss hit', args=(), exc_info=None
        )
        record.symbol = 'GBPUSD'
        record.custom_icon = '🛑'
        
        result = self.formatter.format(record)
        
        self.assertIn('GBPUSD', result)
        self.assertIn('🛑', result)
        self.assertIn('stop loss hit', result)


class TestSetupLogging(unittest.TestCase):
    """Test setup_logging function"""
    
    def setUp(self):
        """Create temporary log directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Reset logging
        logging.getLogger().handlers.clear()
    
    def test_setup_logging_creates_directory(self):
        """Test that setup_logging creates log directory"""
        setup_logging(log_dir=str(self.log_dir), log_level="INFO")
        
        self.assertTrue(self.log_dir.exists())
        self.assertTrue(self.log_dir.is_dir())
    
    def test_setup_logging_info_level(self):
        """Test setup with INFO level"""
        logger = setup_logging(log_dir=str(self.log_dir), log_level="INFO")
        
        self.assertEqual(logger.level, logging.INFO)
    
    def test_setup_logging_debug_level(self):
        """Test setup with DEBUG level"""
        logger = setup_logging(log_dir=str(self.log_dir), log_level="DEBUG")
        
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_setup_logging_warning_level(self):
        """Test setup with WARNING level"""
        logger = setup_logging(log_dir=str(self.log_dir), log_level="WARNING")
        
        self.assertEqual(logger.level, logging.WARNING)
    
    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates handlers"""
        logger = setup_logging(log_dir=str(self.log_dir), log_level="INFO")
        
        # Should have console and file handlers
        self.assertGreater(len(logger.handlers), 0)


class TestGetLogger(unittest.TestCase):
    """Test get_logger function"""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance"""
        logger = get_logger("test_module")
        
        self.assertIsInstance(logger, logging.Logger)
    
    def test_get_logger_with_name(self):
        """Test get_logger with specific name"""
        logger = get_logger("my_module")
        
        self.assertEqual(logger.name, "my_module")
    
    def test_get_logger_multiple_calls(self):
        """Test that multiple calls with same name return same logger"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        
        self.assertIs(logger1, logger2)


class TestLogConfigFunction(unittest.TestCase):
    """Test log_config helper function"""
    
    def test_log_config_basic(self):
        """Test basic log_config function call"""
        logger = logging.getLogger("test")
        logger.setLevel(logging.INFO)
        
        # Create a handler to capture output
        handler = logging.handlers.MemoryHandler(capacity=100)
        logger.addHandler(handler)
        
        log_config(logger, "Test message")
        
        # Should not raise an error
        logger.removeHandler(handler)


if __name__ == '__main__':
    unittest.main()
