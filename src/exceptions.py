"""
Custom Exception Hierarchy for TradingMTQ

This module provides a comprehensive exception hierarchy for structured error handling
across the trading platform. All exceptions inherit from TradingMTQError and include
context information for better debugging and logging.

Usage:
    from src.exceptions import OrderExecutionError, ConnectionError

    if not has_sufficient_margin(volume):
        raise InsufficientMarginError(
            f"Insufficient margin for {volume} lots",
            error_code=10019,
            context={
                'symbol': symbol,
                'volume': volume,
                'margin_available': get_margin()
            }
        )
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class TradingMTQError(Exception):
    """
    Base exception for all TradingMTQ errors

    Provides structured error information including error codes, context,
    and timestamps for comprehensive error tracking and debugging.

    Attributes:
        message (str): Human-readable error message
        error_code (Optional[int]): MT5 error code or custom error code
        context (Dict[str, Any]): Additional context (symbol, volume, etc.)
        timestamp (datetime): When the error occurred
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize TradingMTQ error

        Args:
            message: Human-readable error description
            error_code: Optional error code (MT5 code or custom)
            context: Optional context dictionary with error details
        """
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for structured logging

        Returns:
            Dictionary with error type, message, code, context, timestamp
        """
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }

    def __str__(self) -> str:
        """String representation with error code if available"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code}, "
            f"context={self.context})"
        )


# =============================================================================
# Connection & Communication Errors
# =============================================================================

class ConnectionError(TradingMTQError):
    """
    MT5 connection failure or network issues

    Raised when:
    - Cannot connect to MT5 terminal
    - Connection lost during operation
    - Network timeout
    - MT5 terminal not running
    """
    pass


class ReconnectionError(ConnectionError):
    """
    Failed to reconnect to MT5 after connection loss

    Raised when:
    - Auto-reconnection attempts exhausted
    - MT5 terminal unavailable for extended period
    """
    pass


class AuthenticationError(ConnectionError):
    """
    Authentication failure with MT5 server

    Raised when:
    - Invalid credentials (login, password, server)
    - Account locked or disabled
    - Server not responding to auth requests
    """
    pass


# =============================================================================
# Order Execution Errors
# =============================================================================

class OrderExecutionError(TradingMTQError):
    """
    Base class for order execution failures

    Raised when:
    - Order send failed
    - Order modification failed
    - Order closure failed
    """
    pass


class InvalidOrderError(OrderExecutionError):
    """
    Order parameters are invalid

    Raised when:
    - Invalid volume (too small, too large, wrong step)
    - Invalid price (outside allowed range)
    - Invalid stop loss or take profit levels
    - Invalid order type for symbol
    """
    pass


class OrderRejectedError(OrderExecutionError):
    """
    Order rejected by broker/server

    Raised when:
    - Trading disabled for symbol
    - Market closed
    - Price requote
    - Order fills would exceed position limits
    """
    pass


class OrderTimeoutError(OrderExecutionError):
    """
    Order execution timeout

    Raised when:
    - Order request timeout
    - No response from broker within timeout period
    """
    pass


# =============================================================================
# Risk Management Errors
# =============================================================================

class InsufficientMarginError(TradingMTQError):
    """
    Not enough margin to open or maintain position

    Raised when:
    - Account margin insufficient for new order
    - Margin call risk
    - Free margin below threshold
    """
    pass


class PositionLimitError(TradingMTQError):
    """
    Position limit reached

    Raised when:
    - Maximum concurrent positions reached
    - Portfolio risk limit exceeded
    - Per-symbol position limit reached
    """
    pass


class RiskLimitError(TradingMTQError):
    """
    Risk management limit exceeded

    Raised when:
    - Daily loss limit reached
    - Portfolio risk percentage exceeded
    - Drawdown limit hit
    """
    pass


# =============================================================================
# Market & Symbol Errors
# =============================================================================

class InvalidSymbolError(TradingMTQError):
    """
    Symbol not available or invalid

    Raised when:
    - Symbol not found on broker
    - Symbol not subscribed in Market Watch
    - Symbol format invalid
    """
    pass


class MarketClosedError(TradingMTQError):
    """
    Market is closed for trading

    Raised when:
    - Trading session closed
    - Symbol trading disabled
    - Holiday/weekend trading restricted
    """
    pass


class InsufficientLiquidityError(TradingMTQError):
    """
    Insufficient market liquidity

    Raised when:
    - Volume too large for available liquidity
    - Bid-ask spread too wide
    - No quotes available
    """
    pass


# =============================================================================
# Data & API Errors
# =============================================================================

class DataError(TradingMTQError):
    """
    Base class for data-related errors
    """
    pass


class DataNotAvailableError(DataError):
    """
    Requested data not available

    Raised when:
    - Historical bars not available for timeframe
    - Symbol data not synchronized
    - Broker data incomplete
    """
    pass


class DataValidationError(DataError):
    """
    Data validation failed

    Raised when:
    - OHLC data integrity check failed
    - Missing required data fields
    - Data format unexpected
    """
    pass


class RateLimitError(TradingMTQError):
    """
    API rate limit exceeded

    Raised when:
    - Too many requests to MT5 API
    - LLM API rate limit hit (OpenAI, Anthropic)
    - Broker API throttling
    """
    pass


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(TradingMTQError):
    """
    Configuration validation or loading error

    Raised when:
    - Invalid YAML configuration
    - Required config parameter missing
    - Config value out of valid range
    - Config schema validation failed
    """
    pass


class CredentialsError(ConfigurationError):
    """
    Credentials missing or invalid

    Raised when:
    - MT5 credentials not configured
    - API keys missing (OpenAI, Anthropic)
    - Secret manager unavailable
    """
    pass


# =============================================================================
# Strategy & Indicator Errors
# =============================================================================

class StrategyError(TradingMTQError):
    """
    Strategy execution error

    Raised when:
    - Strategy initialization failed
    - Strategy logic error
    - Strategy not compatible with symbol
    """
    pass


class IndicatorCalculationError(TradingMTQError):
    """
    Technical indicator calculation failed

    Raised when:
    - Insufficient data for indicator
    - Invalid indicator parameters
    - Calculation error (division by zero, etc.)
    """
    pass


class SignalGenerationError(TradingMTQError):
    """
    Signal generation failed

    Raised when:
    - Cannot determine signal (conflicting indicators)
    - Signal confidence below threshold
    - Invalid signal parameters
    """
    pass


# =============================================================================
# ML/AI Errors
# =============================================================================

class MLError(TradingMTQError):
    """
    Base class for ML/AI errors
    """
    pass


class MLModelNotFoundError(MLError):
    """
    ML model file not found

    Raised when:
    - Model file missing from models/ directory
    - Model path incorrect
    - Model not trained yet
    """
    pass


class MLPredictionError(MLError):
    """
    ML model prediction failed

    Raised when:
    - Model inference error
    - Input data incompatible with model
    - TensorFlow/scikit-learn error
    """
    pass


class FeatureEngineeringError(MLError):
    """
    Feature engineering/extraction failed

    Raised when:
    - Cannot calculate required features
    - Feature dimensions mismatch
    - Missing required indicators for features
    """
    pass


class LLMError(MLError):
    """
    LLM API error

    Raised when:
    - OpenAI/Anthropic API error
    - LLM rate limit exceeded
    - Invalid LLM response format
    """
    pass


# =============================================================================
# Database & Persistence Errors
# =============================================================================

class DatabaseError(TradingMTQError):
    """
    Database operation error

    Raised when:
    - Database connection failed
    - Query execution error
    - Transaction rollback
    - Data integrity constraint violation
    """
    pass


class DatabaseConnectionError(DatabaseError):
    """
    Cannot connect to database

    Raised when:
    - SQLite file not accessible
    - PostgreSQL server unavailable
    - Connection pool exhausted
    """
    pass


# =============================================================================
# Monitoring & Resilience Errors
# =============================================================================

class CircuitBreakerOpenError(TradingMTQError):
    """
    Circuit breaker is open, operation blocked

    Raised when:
    - Too many consecutive failures detected
    - Service temporarily unavailable
    - Circuit breaker in OPEN state
    """
    pass


class HealthCheckError(TradingMTQError):
    """
    Health check failed

    Raised when:
    - System component unhealthy
    - MT5 connection unhealthy
    - Database unhealthy
    """
    pass


# =============================================================================
# Utility Functions
# =============================================================================

def is_retriable_error(error: Exception) -> bool:
    """
    Determine if an error is retriable

    Args:
        error: Exception to check

    Returns:
        True if error is transient and operation can be retried
    """
    retriable_types = (
        ConnectionError,
        OrderTimeoutError,
        RateLimitError,
        DataNotAvailableError,
        DatabaseConnectionError,
    )

    # Check if instance of retriable error type
    if isinstance(error, retriable_types):
        return True

    # Check if circuit breaker is temporary
    if isinstance(error, CircuitBreakerOpenError):
        return True

    return False


def get_error_severity(error: Exception) -> str:
    """
    Get error severity level for logging/alerting

    Args:
        error: Exception to categorize

    Returns:
        Severity level: 'CRITICAL', 'ERROR', 'WARNING', 'INFO'
    """
    # CRITICAL - System-wide failures
    critical_types = (
        AuthenticationError,
        DatabaseConnectionError,
        CredentialsError,
    )

    # ERROR - Operation failures
    error_types = (
        OrderExecutionError,
        ConnectionError,
        MLError,
        DatabaseError,
    )

    # WARNING - Recoverable issues
    warning_types = (
        RateLimitError,
        CircuitBreakerOpenError,
        DataNotAvailableError,
    )

    if isinstance(error, critical_types):
        return 'CRITICAL'
    elif isinstance(error, error_types):
        return 'ERROR'
    elif isinstance(error, warning_types):
        return 'WARNING'
    else:
        return 'INFO'


# =============================================================================
# Exception Context Builders (Helper Functions)
# =============================================================================

def build_order_context(symbol: str, order_type: str, volume: float,
                       price: Optional[float] = None,
                       sl: Optional[float] = None,
                       tp: Optional[float] = None,
                       ticket: Optional[int] = None) -> Dict[str, Any]:
    """
    Build context dictionary for order-related exceptions

    Args:
        symbol: Trading symbol
        order_type: Order type (BUY, SELL, etc.)
        volume: Order volume in lots
        price: Order price (optional)
        sl: Stop loss (optional)
        tp: Take profit (optional)
        ticket: Order ticket number (optional)

    Returns:
        Context dictionary with order details
    """
    context = {
        'symbol': symbol,
        'order_type': order_type,
        'volume': volume,
        'price': price,
        'stop_loss': sl,
        'take_profit': tp,
        'timestamp': datetime.utcnow().isoformat()
    }
    if ticket is not None:
        context['ticket'] = ticket
    return context


def build_connection_context(login: int, server: str,
                            attempt: Optional[int] = None) -> Dict[str, Any]:
    """
    Build context dictionary for connection-related exceptions

    Args:
        login: MT5 account login
        server: Broker server name
        attempt: Connection attempt number (optional)

    Returns:
        Context dictionary with connection details
    """
    return {
        'login': login,
        'server': server,
        'attempt': attempt,
        'timestamp': datetime.utcnow().isoformat()
    }


def build_indicator_context(indicator_name: str, symbol: str,
                           timeframe: str, period: int) -> Dict[str, Any]:
    """
    Build context dictionary for indicator-related exceptions

    Args:
        indicator_name: Name of indicator (RSI, MACD, etc.)
        symbol: Trading symbol
        timeframe: Timeframe (M5, H1, etc.)
        period: Indicator period parameter

    Returns:
        Context dictionary with indicator details
    """
    return {
        'indicator': indicator_name,
        'symbol': symbol,
        'timeframe': timeframe,
        'period': period,
        'timestamp': datetime.utcnow().isoformat()
    }
