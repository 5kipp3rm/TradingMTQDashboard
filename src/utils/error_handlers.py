"""
Error Handlers & Retry Logic for TradingMTQ

Provides decorators and context managers for robust error handling with:
- Automatic retry with exponential backoff
- Circuit breaker pattern awareness
- Structured error logging
- Fallback values for graceful degradation

Usage:
    from src.utils.error_handlers import handle_mt5_errors, retry_on_failure

    @handle_mt5_errors(retry_count=3, fallback_return=None)
    def get_symbol_tick(symbol: str):
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise ConnectionError(f"Failed to get tick for {symbol}")
        return tick

    @retry_on_failure(max_attempts=5, delay=2.0, backoff=2.0)
    def connect_to_mt5(login, password, server):
        if not mt5.initialize(login=login, password=password, server=server):
            raise ConnectionError("MT5 initialization failed")
        return True
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Tuple
from datetime import datetime, timedelta

# Import custom exceptions
try:
    from src.exceptions import (
        TradingMTQError, ConnectionError, OrderTimeoutError,
        RateLimitError, CircuitBreakerOpenError, is_retriable_error
    )
except ImportError:
    # Fallback if exceptions module not yet imported
    class TradingMTQError(Exception):
        pass

    class ConnectionError(TradingMTQError):
        pass

    class OrderTimeoutError(TradingMTQError):
        pass

    class RateLimitError(TradingMTQError):
        pass

    class CircuitBreakerOpenError(TradingMTQError):
        pass

    def is_retriable_error(error: Exception) -> bool:
        return isinstance(error, (ConnectionError, OrderTimeoutError, RateLimitError))


logger = logging.getLogger(__name__)


# =============================================================================
# Retry Decorator with Exponential Backoff
# =============================================================================

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for automatic retry with exponential backoff

    Retries failed operations with increasing delays between attempts.
    Useful for transient failures like network issues, timeouts, or
    temporary service unavailability.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Exponential backoff multiplier (default: 2.0)
        exceptions: Tuple of exception types to catch (default: all exceptions)
        on_retry: Optional callback function called on each retry
                 Signature: (exception, attempt_number) -> None

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_failure(max_attempts=5, delay=2.0, backoff=2.0)
        def connect_to_database():
            return db.connect()

        # Retry schedule with default params (delay=1.0, backoff=2.0):
        # Attempt 1: immediate
        # Attempt 2: after 1 second
        # Attempt 3: after 2 seconds (1 * 2)
        # Attempt 4: after 4 seconds (2 * 2)
        # Attempt 5: after 8 seconds (4 * 2)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    # Attempt to execute function
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # Log failure
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}",
                        extra={
                            'function': func.__name__,
                            'attempt': attempt,
                            'max_attempts': max_attempts,
                            'exception_type': type(e).__name__,
                            'will_retry': attempt < max_attempts
                        }
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt)

                    # Don't sleep after last attempt
                    if attempt < max_attempts:
                        logger.info(
                            f"Retrying {func.__name__} in {current_delay:.2f} seconds...",
                            extra={'delay_seconds': current_delay}
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff

            # All attempts exhausted
            logger.error(
                f"All {max_attempts} attempts failed for {func.__name__}",
                extra={
                    'function': func.__name__,
                    'exception_type': type(last_exception).__name__,
                    'exception_message': str(last_exception)
                }
            )

            # Re-raise the last exception
            raise last_exception

        return wrapper
    return decorator


# =============================================================================
# MT5-Specific Error Handler
# =============================================================================

def handle_mt5_errors(
    retry_count: int = 3,
    retry_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    fallback_return: Any = None,
    exceptions: Tuple[Type[Exception], ...] = None,
    log_errors: bool = True
):
    """
    Decorator for handling MT5 API errors with automatic retry

    Designed specifically for MT5 API calls. Retries on connection errors,
    timeouts, and rate limits. Returns fallback value if all retries fail.

    Args:
        retry_count: Number of retry attempts (default: 3)
        retry_delay: Initial delay between retries (default: 1.0s)
        backoff_multiplier: Exponential backoff multiplier (default: 2.0)
        fallback_return: Value to return if all retries fail (default: None)
        exceptions: Tuple of exceptions to catch (default: retriable errors)
        log_errors: Whether to log errors (default: True)

    Returns:
        Decorated function with MT5 error handling

    Example:
        @handle_mt5_errors(retry_count=3, fallback_return=[])
        def get_open_positions(symbol: str):
            positions = mt5.positions_get(symbol=symbol)
            if positions is None:
                raise ConnectionError("Failed to get positions")
            return list(positions)

        # If MT5 call fails after 3 retries, returns [] instead of crashing
    """
    # Default to retriable errors if not specified
    if exceptions is None:
        exceptions = (ConnectionError, OrderTimeoutError, RateLimitError)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = retry_delay
            last_error = None

            for attempt in range(1, retry_count + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_error = e

                    # Check if error is retriable
                    if not is_retriable_error(e) and attempt == 1:
                        # Non-retriable error on first attempt - fail fast
                        if log_errors:
                            logger.error(
                                f"Non-retriable error in {func.__name__}: {e}",
                                extra={'function': func.__name__},
                                exc_info=True
                            )
                        return fallback_return

                    if log_errors:
                        logger.warning(
                            f"MT5 error in {func.__name__} (attempt {attempt}/{retry_count}): {e}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt,
                                'error_type': type(e).__name__
                            }
                        )

                    # Retry if not last attempt
                    if attempt < retry_count:
                        logger.info(f"Retrying in {current_delay:.2f}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff_multiplier
                    else:
                        # Last attempt failed
                        if log_errors:
                            logger.error(
                                f"All {retry_count} attempts failed for {func.__name__}",
                                extra={
                                    'function': func.__name__,
                                    'final_error': str(last_error)
                                },
                                exc_info=True
                            )
                        return fallback_return

            return fallback_return

        return wrapper
    return decorator


# =============================================================================
# Context Manager for Error Handling
# =============================================================================

class ErrorHandler:
    """
    Context manager for graceful error handling with fallback

    Catches exceptions within context and provides fallback mechanism
    without crashing the program. Useful for non-critical operations.

    Usage:
        with ErrorHandler(fallback_value=[], log_errors=True):
            positions = get_open_positions(symbol)
            # If error occurs, positions = []

        # Program continues regardless of error
    """

    def __init__(
        self,
        fallback_value: Any = None,
        log_errors: bool = True,
        suppress_errors: bool = True,
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        Initialize error handler context

        Args:
            fallback_value: Value to use if error occurs
            log_errors: Whether to log exceptions
            suppress_errors: Whether to suppress exceptions (default: True)
            on_error: Optional callback for error handling
        """
        self.fallback_value = fallback_value
        self.log_errors = log_errors
        self.suppress_errors = suppress_errors
        self.on_error = on_error
        self.result = None
        self.error = None

    def __enter__(self):
        """Enter context"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context and handle any exceptions

        Returns:
            True to suppress exception, False to propagate
        """
        if exc_type is not None:
            self.error = exc_val
            self.result = self.fallback_value

            if self.log_errors:
                logger.error(
                    f"Error in context: {exc_val}",
                    extra={'exception_type': exc_type.__name__},
                    exc_info=True
                )

            if self.on_error:
                self.on_error(exc_val)

            return self.suppress_errors

        return False


# =============================================================================
# Rate Limiter
# =============================================================================

class RateLimiter:
    """
    Simple rate limiter to prevent API throttling

    Tracks API calls and enforces minimum delay between calls.
    Useful for preventing rate limit errors from external APIs.

    Usage:
        rate_limiter = RateLimiter(calls_per_second=5)

        for symbol in symbols:
            rate_limiter.wait_if_needed()
            data = api.get_data(symbol)
    """

    def __init__(self, calls_per_second: float = 10.0):
        """
        Initialize rate limiter

        Args:
            calls_per_second: Maximum calls per second (default: 10)
        """
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0

    def wait_if_needed(self):
        """Wait if necessary to maintain rate limit"""
        now = time.time()
        elapsed = now - self.last_call_time

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)

        self.last_call_time = time.time()


# =============================================================================
# Timeout Decorator
# =============================================================================

def timeout(seconds: float = 30.0, fallback_return: Any = None):
    """
    Decorator to enforce timeout on function execution

    Note: Uses signal module (Unix only) or threading fallback

    Args:
        seconds: Timeout in seconds
        fallback_return: Value to return on timeout

    Returns:
        Decorated function with timeout enforcement

    Example:
        @timeout(seconds=10.0, fallback_return=None)
        def slow_operation():
            # Operation that might take too long
            return expensive_computation()
    """
    import platform
    import threading

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use signal on Unix systems
            if platform.system() != 'Windows':
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Function {func.__name__} timed out after {seconds}s")

                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(seconds))

                try:
                    result = func(*args, **kwargs)
                    signal.alarm(0)
                    return result
                except TimeoutError as e:
                    logger.error(f"Timeout in {func.__name__}: {e}")
                    return fallback_return
                finally:
                    signal.signal(signal.SIGALRM, old_handler)

            # Use threading on Windows
            else:
                result = [fallback_return]
                exception = [None]

                def target():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e

                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout=seconds)

                if thread.is_alive():
                    logger.error(f"Timeout in {func.__name__} after {seconds}s")
                    return fallback_return

                if exception[0]:
                    raise exception[0]

                return result[0]

        return wrapper
    return decorator


# =============================================================================
# Helper Functions
# =============================================================================

def safe_execute(
    func: Callable,
    *args,
    fallback_return: Any = None,
    log_errors: bool = True,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling

    Args:
        func: Function to execute
        *args: Positional arguments for function
        fallback_return: Value to return on error
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for function

    Returns:
        Function result or fallback_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(
                f"Error executing {func.__name__}: {e}",
                extra={'function': func.__name__},
                exc_info=True
            )
        return fallback_return


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example 1: Retry decorator
    @retry_on_failure(max_attempts=3, delay=1.0, backoff=2.0)
    def flaky_operation(fail_count: int = 2):
        """Simulates operation that fails first N times"""
        if not hasattr(flaky_operation, 'attempts'):
            flaky_operation.attempts = 0

        flaky_operation.attempts += 1
        print(f"Attempt {flaky_operation.attempts}")

        if flaky_operation.attempts <= fail_count:
            raise ConnectionError("Connection failed (simulated)")

        return "Success!"

    print("Testing retry decorator:")
    result = flaky_operation(fail_count=2)
    print(f"Result: {result}\n")

    # Example 2: MT5 error handler
    @handle_mt5_errors(retry_count=2, fallback_return=None)
    def get_fake_tick(symbol: str):
        """Simulates MT5 API call"""
        raise ConnectionError("MT5 not responding")

    print("Testing MT5 error handler:")
    tick = get_fake_tick("EURUSD")
    print(f"Tick: {tick}\n")

    # Example 3: Error context manager
    print("Testing error context manager:")
    with ErrorHandler(fallback_value=[]) as handler:
        raise ValueError("Something went wrong")

    print(f"Result after error: {handler.result}")
    print(f"Error caught: {handler.error}")
