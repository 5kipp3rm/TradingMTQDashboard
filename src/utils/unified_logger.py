"""
Unified Logging System for TradingMTQ

Combines the best features of both structured_logger.py and logger.py into a single
OOP-based logging system that supports:
- JSON structured logging for production
- Colored console output for development
- Correlation ID tracking
- Multiple output formats
- Emoji icons for visual debugging
- Context managers for correlation tracking

Usage:
    from src.utils.unified_logger import UnifiedLogger, LogContext

    # Get logger instance
    logger = UnifiedLogger.get_logger(__name__)

    # Simple logging
    logger.info("Processing started")

    # With correlation tracking
    with LogContext() as ctx:
        logger.info("Trade executed", symbol="EURUSD", action="BUY", volume=0.1)

    # Helper methods
    logger.log_trade("EURUSD", "BUY", 0.1, 1.0850, 12345)
    logger.log_signal("EURUSD", "BUY", 1.0850, 0.85)
"""

import logging
import logging.handlers
import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Literal
from contextvars import ContextVar
import traceback


# Thread-safe correlation ID storage
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class OutputFormat:
    """Available output formats"""
    JSON = "json"           # Machine-parseable JSON
    COLORED = "colored"     # Human-readable with colors and emojis
    PLAIN = "plain"         # Plain text without colors


class ColoredFormatter(logging.Formatter):
    """Colored console formatter with emojis"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
    }

    ICONS = {
        'DEBUG': '[D]',
        'INFO': '[I]',
        'WARNING': '[W]',
        'ERROR': '[E]',
        'CRITICAL': '[C]',
    }

    def format(self, record):
        levelname = record.levelname

        # Add icon
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


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': correlation_id_var.get() or 'none'
        }

        # Add extra context fields from record
        if hasattr(record, 'extra_fields') and record.extra_fields:
            filtered_extra = {k: v for k, v in record.extra_fields.items() if v is not None}
            log_entry.update(filtered_extra)

        # Add exception info if available
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_entry['exception'] = {
                'type': exc_type.__name__ if exc_type else 'Unknown',
                'message': str(exc_value) if exc_value else '',
                'traceback': ''.join(traceback.format_tb(exc_tb)) if exc_tb else ''
            }

        return json.dumps(log_entry, default=str)


class UnifiedLogger:
    """
    Unified logger combining structured and enhanced logging features

    Supports multiple output formats:
    - JSON: Machine-parseable for production/monitoring tools
    - COLORED: Human-readable with colors and emojis for development
    - PLAIN: Plain text without colors

    Features:
    - Correlation ID tracking (thread-safe)
    - Multiple log files (main, errors, trades)
    - Context managers for correlation propagation
    - Helper methods for common logging patterns
    - Configurable output formats per handler
    """

    _loggers: Dict[str, 'UnifiedLogger'] = {}
    _configured: bool = False

    def __init__(self, name: str):
        """
        Initialize unified logger

        Args:
            name: Logger name (typically __name__ from calling module)
        """
        self.logger = logging.getLogger(name)
        self.name = name

    @classmethod
    def configure(
        cls,
        log_dir: str = "logs",
        log_level: str = "INFO",
        console_output: bool = True,
        console_format: str = OutputFormat.COLORED,
        file_output: bool = True,
        file_format: str = OutputFormat.JSON,
    ):
        """
        Configure the unified logging system (call once at startup)

        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Enable console output
            console_format: Console format (json, colored, plain)
            file_output: Enable file output
            file_format: File format (json, colored, plain)
        """
        if cls._configured:
            return

        # Create log directory
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Remove existing handlers
        root_logger.handlers.clear()

        # Create formatters
        formatters = {
            OutputFormat.JSON: JSONFormatter(),
            OutputFormat.COLORED: ColoredFormatter(
                '%(asctime)s %(levelname)s %(message)s',
                datefmt='%H:%M:%S'
            ),
            OutputFormat.PLAIN: logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        }

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatters.get(console_format, formatters[OutputFormat.COLORED]))
            root_logger.addHandler(console_handler)

        # File handlers
        if file_output:
            today = datetime.now().strftime('%Y%m%d')
            file_formatter = formatters.get(file_format, formatters[OutputFormat.JSON])

            # Main log file
            log_file = log_path / f"trading_{today}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=30,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

            # Error log file
            error_file = log_path / f"errors_{today}.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_file,
                maxBytes=10*1024*1024,
                backupCount=30,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)

            # Trade log file (separate with longer retention)
            trade_file = log_path / f"trades_{today}.log"
            trade_handler = logging.handlers.RotatingFileHandler(
                trade_file,
                maxBytes=10*1024*1024,
                backupCount=90,  # Keep trade logs longer
                encoding='utf-8'
            )
            trade_handler.setLevel(logging.INFO)
            trade_handler.setFormatter(file_formatter)
            trade_handler.addFilter(
                lambda record: any(keyword in record.getMessage().lower()
                                  for keyword in ['trade', 'position', 'order', 'signal'])
            )
            root_logger.addHandler(trade_handler)

        cls._configured = True
        root_logger.info("Unified logging system initialized")

    @classmethod
    def get_logger(cls, name: str) -> 'UnifiedLogger':
        """
        Get a logger instance (singleton per name)

        Args:
            name: Logger name (typically __name__)

        Returns:
            UnifiedLogger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = UnifiedLogger(name)
        return cls._loggers[name]

    def _log(self, level: int, message: str, exc_info: bool = False, **kwargs):
        """
        Internal logging method

        Args:
            level: Logging level (logging.INFO, logging.ERROR, etc.)
            message: Log message
            exc_info: Include exception traceback
            **kwargs: Additional context fields
        """
        extra = {'extra_fields': kwargs} if kwargs else {}
        self.logger.log(level, message, exc_info=exc_info, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)

    # Correlation ID methods

    def set_correlation_id(self, correlation_id: Optional[str] = None):
        """Set correlation ID for current context"""
        correlation_id_var.set(correlation_id or str(uuid.uuid4()))

    def clear_correlation_id(self):
        """Clear correlation ID from current context"""
        correlation_id_var.set(None)

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID"""
        return correlation_id_var.get()

    # Helper methods for common logging patterns

    def log_trade(self, symbol: str, action: str, volume: float, price: float, ticket: int,
                  sl: Optional[float] = None, tp: Optional[float] = None):
        """
        Log trade execution

        Args:
            symbol: Trading symbol
            action: Order action (BUY/SELL)
            volume: Order volume in lots
            price: Execution price
            ticket: Order ticket number
            sl: Stop loss price (optional)
            tp: Take profit price (optional)
        """
        self.info(
            f"Trade executed: {action} {volume} {symbol} @ {price:.5f} - Ticket #{ticket}",
            event_type='trade_execution',
            symbol=symbol,
            action=action,
            volume=volume,
            price=price,
            ticket=ticket,
            stop_loss=sl,
            take_profit=tp,
            custom_icon='💰'
        )

    def log_signal(self, symbol: str, signal_type: str, price: float, confidence: float,
                   strategy: Optional[str] = None, indicators: Optional[Dict] = None):
        """
        Log signal generation

        Args:
            symbol: Trading symbol
            signal_type: Signal type (BUY/SELL/HOLD)
            price: Current price
            confidence: Signal confidence (0.0-1.0)
            strategy: Strategy name (optional)
            indicators: Indicator values (optional)
        """
        self.info(
            f"Signal generated: {signal_type} for {symbol} @ {price:.5f} (confidence: {confidence:.1%})",
            event_type='signal_generation',
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            confidence=confidence,
            strategy=strategy,
            indicators=indicators or {},
            custom_icon='📊'
        )

    def log_connection(self, event: str, login: Optional[int] = None, server: Optional[str] = None,
                      success: bool = True, error_message: Optional[str] = None):
        """
        Log connection event

        Args:
            event: Event type (connect/disconnect/reconnect)
            login: MT5 account login (optional)
            server: Broker server (optional)
            success: Whether operation succeeded
            error_message: Error message if failed (optional)
        """
        msg = f"Connection {event}"
        if login:
            msg += f" - Account {login}"
        if server:
            msg += f" @ {server}"
        if error_message:
            msg += f" - {error_message}"

        self.info(
            msg,
            event_type='connection',
            event=event,
            login=login,
            server=server,
            success=success,
            error_message=error_message,
            custom_icon='🔌'
        )

    def log_position_update(self, symbol: str, ticket: int, update_type: str,
                           old_value: Optional[float] = None, new_value: Optional[float] = None):
        """
        Log position update (SL/TP modification)

        Args:
            symbol: Trading symbol
            ticket: Position ticket
            update_type: Type of update (stop_loss/take_profit/close)
            old_value: Previous value (optional)
            new_value: New value (optional)
        """
        msg = f"Position updated: {update_type} for ticket {ticket}"
        if old_value is not None and new_value is not None:
            msg += f" ({old_value:.5f} → {new_value:.5f})"

        self.info(
            msg,
            event_type='position_update',
            symbol=symbol,
            ticket=ticket,
            update_type=update_type,
            old_value=old_value,
            new_value=new_value,
            custom_icon='📝'
        )

    def log_config(self, message: str, **kwargs):
        """Log configuration changes"""
        self.info(message, event_type='configuration', custom_icon='⚙️', **kwargs)

    def log_cycle(self, cycle_num: int, message: str, **kwargs):
        """Log cycle events"""
        self.info(
            f"Cycle #{cycle_num}: {message}",
            event_type='cycle',
            cycle_number=cycle_num,
            custom_icon='🔄',
            **kwargs
        )

    def log_performance_metric(self, metric_name: str, value: float, unit: str,
                              additional_metrics: Optional[Dict] = None):
        """
        Log performance metric

        Args:
            metric_name: Name of metric
            value: Metric value
            unit: Unit of measurement
            additional_metrics: Additional metrics (optional)
        """
        metrics = additional_metrics or {}
        metrics.update({
            'metric_name': metric_name,
            'value': value,
            'unit': unit
        })

        self.info(
            f"Performance metric: {metric_name}={value}{unit}",
            event_type='performance_metric',
            **metrics
        )

    def log_error_with_context(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log error with full context and traceback

        Args:
            error: Exception instance
            context: Additional error context (optional)
        """
        error_context = context or {}
        error_context.update({
            'error_type': type(error).__name__,
            'error_message': str(error),
        })

        # Add custom exception context if available
        if hasattr(error, 'to_dict'):
            error_context.update(error.to_dict())

        self.error(
            f"Error occurred: {str(error)}",
            exc_info=True,
            **error_context
        )


class LogContext:
    """
    Context manager for correlation ID propagation

    Automatically sets and clears correlation IDs for request tracking
    across function calls and components.

    Usage:
        with LogContext() as ctx:
            logger.info("Processing request", user_id=123)
            # All logs within this context will have same correlation_id
    """

    def __init__(self, correlation_id: Optional[str] = None):
        """
        Initialize correlation context

        Args:
            correlation_id: Use specific correlation ID (generated if None)
        """
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.previous_id = None

    def __enter__(self):
        """Enter context: set correlation ID"""
        self.previous_id = correlation_id_var.get()
        correlation_id_var.set(self.correlation_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context: restore previous correlation ID"""
        correlation_id_var.set(self.previous_id)
        return False  # Don't suppress exceptions


# Convenience functions for backward compatibility

def setup_logging(log_dir: str = "logs", log_level: str = "INFO",
                 console_output: bool = True, file_output: bool = True):
    """
    Setup unified logging (backward compatible with logger.py)

    Args:
        log_dir: Directory for log files
        log_level: Logging level
        console_output: Enable console output
        file_output: Enable file output
    """
    UnifiedLogger.configure(
        log_dir=log_dir,
        log_level=log_level,
        console_output=console_output,
        console_format=OutputFormat.COLORED,
        file_output=file_output,
        file_format=OutputFormat.JSON
    )


def get_logger(name: str) -> UnifiedLogger:
    """
    Get a logger instance (backward compatible)

    Args:
        name: Logger name (typically __name__)

    Returns:
        UnifiedLogger instance
    """
    return UnifiedLogger.get_logger(name)


# Aliases for backward compatibility with structured_logger.py
StructuredLogger = UnifiedLogger
CorrelationContext = LogContext
get_structured_logger = get_logger


# Example usage
if __name__ == '__main__':
    # Configure logging system
    UnifiedLogger.configure(
        log_dir="logs",
        log_level="INFO",
        console_output=True,
        console_format=OutputFormat.COLORED,
        file_output=True,
        file_format=OutputFormat.JSON
    )

    # Get logger
    logger = UnifiedLogger.get_logger('trading_example')

    # Simple logging
    logger.info("Application started")

    # With correlation tracking
    with LogContext() as ctx:
        logger.info(
            "Starting trading cycle",
            cycle_number=1,
            symbols=['EURUSD', 'GBPUSD']
        )

        # Helper methods
        logger.log_trade('EURUSD', 'BUY', 0.1, 1.0850, 12345, sl=1.0800, tp=1.0900)
        logger.log_signal('GBPUSD', 'SELL', 1.2750, 0.75, strategy='RSI_Strategy')
        logger.log_connection('connect', login=12345678, server='ICMarkets-Demo', success=True)

    # Error logging
    try:
        raise ValueError("Sample error for demonstration")
    except Exception as e:
        logger.log_error_with_context(e, context={'operation': 'order_execution'})

    # Performance metrics
    logger.log_performance_metric('cycle_time', 2.5, 'seconds', {'api_calls': 15})
