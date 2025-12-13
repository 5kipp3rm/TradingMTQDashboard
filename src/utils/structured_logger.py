"""
Structured JSON Logger for TradingMTQ

Provides machine-parseable JSON logging with correlation IDs for request tracking
across distributed components. All logs are structured for easy parsing by log
aggregation tools (ELK, Splunk, CloudWatch, etc.).

Features:
- JSON-formatted log output
- Correlation ID propagation (thread-safe)
- Context managers for correlation tracking
- Structured extra fields
- Compatible with existing logging handlers

Usage:
    from src.utils.structured_logger import StructuredLogger, CorrelationContext

    logger = StructuredLogger(__name__)

    # With correlation ID context
    with CorrelationContext() as ctx:
        logger.info(
            "Trade executed",
            symbol="EURUSD",
            action="BUY",
            volume=0.1,
            price=1.0850,
            ticket=12345
        )

    # Output:
    # {"timestamp":"2025-12-13T10:30:45.123Z","level":"INFO","logger":"trading",
    #  "message":"Trade executed","correlation_id":"a1b2c3d4-...",
    #  "symbol":"EURUSD","action":"BUY","volume":0.1,"price":1.085,"ticket":12345}
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from contextvars import ContextVar
import traceback


# Thread-safe correlation ID storage using ContextVar (Python 3.7+)
# ContextVar is isolated per async task and thread
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredLogger:
    """
    JSON structured logger for machine-parseable logs

    Provides structured logging with correlation IDs for request tracking
    across multiple components and services.

    Attributes:
        logger: Underlying Python logger
        name: Logger name (usually module name)
    """

    def __init__(self, name: str):
        """
        Initialize structured logger

        Args:
            name: Logger name (typically __name__ from calling module)
        """
        self.logger = logging.getLogger(name)
        self.name = name

    def _format_message(self, level: str, message: str,
                       extra: Optional[Dict[str, Any]] = None,
                       exc_info: bool = False) -> str:
        """
        Format message as JSON

        Args:
            level: Log level (INFO, ERROR, WARNING, DEBUG)
            message: Log message
            extra: Additional context fields
            exc_info: Include exception traceback

        Returns:
            JSON-formatted log string
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'logger': self.name,
            'message': message,
            'correlation_id': correlation_id_var.get() or 'none'
        }

        # Add extra context fields
        if extra:
            # Filter out None values and add to log entry
            filtered_extra = {k: v for k, v in extra.items() if v is not None}
            log_entry.update(filtered_extra)

        # Add exception info if available
        if exc_info:
            exc_type, exc_value, exc_tb = None, None, None
            import sys
            if sys.exc_info()[0] is not None:
                exc_type, exc_value, exc_tb = sys.exc_info()
                log_entry['exception'] = {
                    'type': exc_type.__name__ if exc_type else 'Unknown',
                    'message': str(exc_value) if exc_value else '',
                    'traceback': ''.join(traceback.format_tb(exc_tb)) if exc_tb else ''
                }

        return json.dumps(log_entry, default=str)

    def info(self, message: str, **kwargs):
        """
        Log info message

        Args:
            message: Log message
            **kwargs: Additional context fields (symbol, action, volume, etc.)
        """
        self.logger.info(self._format_message('INFO', message, kwargs))

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """
        Log error message

        Args:
            message: Error message
            exc_info: Include exception traceback in log
            **kwargs: Additional context fields
        """
        self.logger.error(
            self._format_message('ERROR', message, kwargs, exc_info),
            exc_info=False  # We handle exc_info ourselves in _format_message
        )

    def warning(self, message: str, **kwargs):
        """
        Log warning message

        Args:
            message: Warning message
            **kwargs: Additional context fields
        """
        self.logger.warning(self._format_message('WARNING', message, kwargs))

    def debug(self, message: str, **kwargs):
        """
        Log debug message

        Args:
            message: Debug message
            **kwargs: Additional context fields
        """
        self.logger.debug(self._format_message('DEBUG', message, kwargs))

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """
        Log critical message

        Args:
            message: Critical error message
            exc_info: Include exception traceback
            **kwargs: Additional context fields
        """
        self.logger.critical(
            self._format_message('CRITICAL', message, kwargs, exc_info),
            exc_info=False
        )

    def set_correlation_id(self, correlation_id: Optional[str] = None):
        """
        Set correlation ID for current context

        Args:
            correlation_id: Correlation ID (UUID4 generated if None)
        """
        correlation_id_var.set(correlation_id or str(uuid.uuid4()))

    def clear_correlation_id(self):
        """Clear correlation ID from current context"""
        correlation_id_var.set(None)

    def get_correlation_id(self) -> Optional[str]:
        """
        Get current correlation ID

        Returns:
            Current correlation ID or None
        """
        return correlation_id_var.get()


class CorrelationContext:
    """
    Context manager for correlation ID propagation

    Automatically sets and clears correlation IDs for request tracking
    across function calls and components.

    Usage:
        with CorrelationContext() as ctx:
            logger.info("Processing request", user_id=123)
            # correlation_id automatically included in all logs within this context
            process_trade(symbol, volume)
            # All logs in process_trade() will have same correlation_id

        # Outside context, correlation_id is cleared

    Attributes:
        correlation_id: Unique correlation ID for this context
        previous_id: Previous correlation ID (for nested contexts)
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


# =============================================================================
# Helper Functions for Common Log Patterns
# =============================================================================

def log_trade_execution(logger: StructuredLogger, symbol: str, action: str,
                       volume: float, price: float, ticket: int,
                       sl: Optional[float] = None, tp: Optional[float] = None):
    """
    Log trade execution with structured fields

    Args:
        logger: StructuredLogger instance
        symbol: Trading symbol
        action: Order action (BUY/SELL)
        volume: Order volume in lots
        price: Execution price
        ticket: Order ticket number
        sl: Stop loss price (optional)
        tp: Take profit price (optional)
    """
    logger.info(
        f"Trade executed: {action} {volume} {symbol}",
        event_type='trade_execution',
        symbol=symbol,
        action=action,
        volume=volume,
        price=price,
        ticket=ticket,
        stop_loss=sl,
        take_profit=tp
    )


def log_signal_generation(logger: StructuredLogger, symbol: str,
                         signal_type: str, confidence: float,
                         strategy: str, indicators: Optional[Dict] = None):
    """
    Log signal generation with structured fields

    Args:
        logger: StructuredLogger instance
        symbol: Trading symbol
        signal_type: Signal type (BUY/SELL/HOLD)
        confidence: Signal confidence (0.0-1.0)
        strategy: Strategy name
        indicators: Indicator values (optional)
    """
    logger.info(
        f"Signal generated: {signal_type} for {symbol}",
        event_type='signal_generation',
        symbol=symbol,
        signal_type=signal_type,
        confidence=confidence,
        strategy=strategy,
        indicators=indicators or {}
    )


def log_connection_event(logger: StructuredLogger, event: str,
                        login: int, server: str, success: bool,
                        error_message: Optional[str] = None):
    """
    Log connection event with structured fields

    Args:
        logger: StructuredLogger instance
        event: Event type (connect/disconnect/reconnect)
        login: MT5 account login
        server: Broker server
        success: Whether operation succeeded
        error_message: Error message if failed (optional)
    """
    logger.info(
        f"Connection event: {event}",
        event_type='connection',
        event=event,
        login=login,
        server=server,
        success=success,
        error_message=error_message
    )


def log_position_update(logger: StructuredLogger, symbol: str, ticket: int,
                       update_type: str, old_value: Optional[float] = None,
                       new_value: Optional[float] = None):
    """
    Log position update (SL/TP modification) with structured fields

    Args:
        logger: StructuredLogger instance
        symbol: Trading symbol
        ticket: Position ticket
        update_type: Type of update (stop_loss/take_profit/close)
        old_value: Previous value (optional)
        new_value: New value (optional)
    """
    logger.info(
        f"Position updated: {update_type} for ticket {ticket}",
        event_type='position_update',
        symbol=symbol,
        ticket=ticket,
        update_type=update_type,
        old_value=old_value,
        new_value=new_value
    )


def log_error_with_context(logger: StructuredLogger, error: Exception,
                          context: Optional[Dict[str, Any]] = None):
    """
    Log error with full context and traceback

    Args:
        logger: StructuredLogger instance
        error: Exception instance
        context: Additional error context (optional)
    """
    error_context = context or {}

    # Add error details to context
    error_context.update({
        'error_type': type(error).__name__,
        'error_message': str(error),
    })

    # Add custom exception context if available
    if hasattr(error, 'to_dict'):
        error_context.update(error.to_dict())

    logger.error(
        f"Error occurred: {str(error)}",
        exc_info=True,
        **error_context
    )


def log_performance_metric(logger: StructuredLogger, metric_name: str,
                          value: float, unit: str,
                          additional_metrics: Optional[Dict] = None):
    """
    Log performance metric with structured fields

    Args:
        logger: StructuredLogger instance
        metric_name: Name of metric (cycle_time, api_latency, etc.)
        value: Metric value
        unit: Unit of measurement (ms, seconds, MB, etc.)
        additional_metrics: Additional metrics (optional)
    """
    metrics = additional_metrics or {}
    metrics.update({
        'metric_name': metric_name,
        'value': value,
        'unit': unit
    })

    logger.info(
        f"Performance metric: {metric_name}={value}{unit}",
        event_type='performance_metric',
        **metrics
    )


# =============================================================================
# Factory Function
# =============================================================================

def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == '__main__':
    # Setup basic logging to see output
    logging.basicConfig(level=logging.INFO)

    # Create logger
    logger = get_structured_logger('trading_example')

    # Example 1: Simple log with context
    with CorrelationContext() as ctx:
        logger.info(
            "Starting trading cycle",
            cycle_number=1,
            symbols=['EURUSD', 'GBPUSD']
        )

        # Simulate trade execution
        log_trade_execution(
            logger,
            symbol='EURUSD',
            action='BUY',
            volume=0.1,
            price=1.0850,
            ticket=12345,
            sl=1.0800,
            tp=1.0900
        )

        # Simulate signal generation
        log_signal_generation(
            logger,
            symbol='GBPUSD',
            signal_type='SELL',
            confidence=0.75,
            strategy='RSI_Strategy',
            indicators={'rsi': 72.5, 'macd': 0.0015}
        )

    # Example 2: Error logging with exception
    try:
        raise ValueError("Sample error for demonstration")
    except Exception as e:
        log_error_with_context(
            logger,
            error=e,
            context={'operation': 'order_execution', 'symbol': 'EURUSD'}
        )

    # Example 3: Performance metrics
    log_performance_metric(
        logger,
        metric_name='cycle_time',
        value=2.5,
        unit='seconds',
        additional_metrics={'api_calls': 15, 'trades_executed': 3}
    )
