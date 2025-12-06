"""
Enhanced Logging System for TradingMTQ
Provides colored console output with emojis and structured file logging
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
import sys


class ColoredFormatter(logging.Formatter):
    """Enhanced colored console formatter with emojis"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
        'BOLD': '\033[1m',        # Bold
        'DIM': '\033[2m',         # Dim
    }
    
    ICONS = {
        'DEBUG': '🔍',
        'INFO': '✓',
        'WARNING': '⚠️',
        'ERROR': '✗',
        'CRITICAL': '🚨',
    }
    
    def format(self, record):
        levelname = record.levelname
        
        # Add emoji icon
        icon = self.ICONS.get(levelname, '•')
        
        # Add color
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{self.COLORS['BOLD']}"
                f"{icon} {levelname}{self.COLORS['RESET']}"
            )
        
        # Add symbol formatting if present
        if hasattr(record, 'symbol'):
            symbol = record.symbol
            record.msg = f"[{self.COLORS['BOLD']}{symbol}{self.COLORS['RESET']}] {record.msg}"
        
        # Add custom icon if present
        if hasattr(record, 'custom_icon'):
            record.msg = f"{record.custom_icon} {record.msg}"
        
        return super().format(record)


def setup_logging(log_dir: str = "logs", 
                  log_level: str = "INFO",
                  console_output: bool = True,
                  file_output: bool = True) -> logging.Logger:
    """
    Set up enhanced logging configuration with emojis and colors
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Enable console output
        file_output: Enable file output
        
    Returns:
        Root logger instance
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | [%(filename)s:%(lineno)d] | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = ColoredFormatter(
        '%(asctime)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler with colors and emojis
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler - main log
    if file_output:
        today = datetime.now().strftime('%Y%m%d')
        log_file = log_path / f"trading_{today}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Separate error log
        error_file = log_path / f"errors_{today}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=10*1024*1024,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Trade log (separate file for trade-specific events)
        trade_file = log_path / f"trades_{today}.log"
        trade_handler = logging.handlers.RotatingFileHandler(
            trade_file,
            maxBytes=10*1024*1024,
            backupCount=90,  # Keep trade logs longer
            encoding='utf-8'
        )
        trade_handler.setLevel(logging.INFO)
        trade_handler.setFormatter(detailed_formatter)
        
        # Add filter to only log trade-related messages
        trade_handler.addFilter(lambda record: 'trade' in record.getMessage().lower() or 
                                               'position' in record.getMessage().lower() or
                                               'order' in record.getMessage().lower() or
                                               'signal' in record.getMessage().lower())
        root_logger.addHandler(trade_handler)
    
    root_logger.info("✓ Logging system initialized with enhanced formatting")
    return root_logger


# Helper functions for contextual logging
def log_trade(logger: logging.Logger, symbol: str, action: str, volume: float, 
              price: float, ticket: int):
    """Log trade execution with emoji"""
    extra = {'symbol': symbol, 'custom_icon': '💰'}
    logger.info(
        f"{action} {volume:.2f} lots @ {price:.5f} - Ticket #{ticket}",
        extra=extra
    )


def log_signal(logger: logging.Logger, symbol: str, signal_type: str, 
               price: float, confidence: float):
    """Log signal generation with emoji"""
    extra = {'symbol': symbol, 'custom_icon': '📊'}
    logger.info(
        f"Signal: {signal_type} @ {price:.5f} (confidence: {confidence:.1%})",
        extra=extra
    )


def log_connection(logger: logging.Logger, status: str, details: str = ""):
    """Log connection status with emoji"""
    extra = {'custom_icon': '🔌'}
    msg = f"Connection {status}"
    if details:
        msg += f" - {details}"
    logger.info(msg, extra=extra)


def log_config(logger: logging.Logger, message: str):
    """Log configuration changes with emoji"""
    extra = {'custom_icon': '⚙️'}
    logger.info(message, extra=extra)


def log_cycle(logger: logging.Logger, cycle_num: int, message: str):
    """Log cycle events with emoji"""
    extra = {'custom_icon': '🔄'}
    logger.info(f"Cycle #{cycle_num}: {message}", extra=extra)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
