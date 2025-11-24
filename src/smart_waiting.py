"""
Smart waiting and polling utilities for macOS UI automation.

Provides intelligent waiting for UI elements, conditions, and state changes
with automatic retrying and timeout handling.
"""

import logging
import time
from typing import Optional, Callable, Any, Tuple, Dict, List
from enum import Enum
import functools

try:
    from accessibility_client import AccessibilityClient, check_accessibility_available
    ACCESSIBILITY_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_AVAILABLE = False

# Configure logging
logger = logging.getLogger('smart_waiting')
logger.setLevel(logging.DEBUG)


class WaitResult(Enum):
    """Result of a wait operation."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"


class SmartWaiter:
    """
    Smart waiting utilities for UI automation.

    Features:
    - Wait for elements to appear
    - Wait for text changes
    - Poll until condition is met
    - Automatic retry with exponential backoff
    - Configurable timeouts and intervals
    """

    def __init__(self):
        """Initialize smart waiter."""
        if not ACCESSIBILITY_AVAILABLE:
            logger.warning("Accessibility API not available - limited functionality")

        self.accessibility_client = None
        if ACCESSIBILITY_AVAILABLE and check_accessibility_available():
            try:
                self.accessibility_client = AccessibilityClient()
            except Exception as e:
                logger.error(f"Failed to initialize accessibility client: {e}")

        logger.info("Initialized smart waiter")

    def wait_for_element(
        self,
        name: Optional[str] = None,
        role: Optional[str] = None,
        app_name: Optional[str] = None,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        min_count: int = 1
    ) -> Tuple[WaitResult, Optional[List[Any]], Optional[str]]:
        """
        Wait for UI element(s) to appear.

        Args:
            name: Element name/title to search for
            role: Element role (e.g., "AXButton")
            app_name: Limit search to specific app
            timeout: Maximum time to wait (seconds)
            poll_interval: Time between checks (seconds)
            min_count: Minimum number of elements to find

        Returns:
            Tuple of (result, elements, error_message)
        """
        if not self.accessibility_client:
            return WaitResult.ERROR, None, "Accessibility client not available"

        start_time = time.time()
        last_error = None

        logger.info(f"Waiting for element: name={name}, role={role}, app={app_name}, timeout={timeout}s")

        while time.time() - start_time < timeout:
            try:
                # Get PID if app_name specified
                pid = None
                if app_name:
                    pid = self.accessibility_client.get_app_pid(app_name)
                    if not pid:
                        last_error = f"App not found: {app_name}"
                        time.sleep(poll_interval)
                        continue

                # Search for elements
                elements = self.accessibility_client.find_elements(
                    role=role,
                    title=name,
                    pid=pid
                )

                if elements and len(elements) >= min_count:
                    elapsed = time.time() - start_time
                    logger.info(f"Found {len(elements)} element(s) after {elapsed:.2f}s")
                    return WaitResult.SUCCESS, elements, None

                # Not found yet, wait and retry
                time.sleep(poll_interval)

            except Exception as e:
                last_error = str(e)
                logger.debug(f"Error while waiting: {e}")
                time.sleep(poll_interval)

        # Timeout reached
        elapsed = time.time() - start_time
        error_msg = f"Timeout after {elapsed:.2f}s - element not found"
        if last_error:
            error_msg += f": {last_error}"

        logger.warning(error_msg)
        return WaitResult.TIMEOUT, None, error_msg

    def wait_for_element_property(
        self,
        name: Optional[str] = None,
        role: Optional[str] = None,
        app_name: Optional[str] = None,
        property_name: str = "AXValue",
        expected_value: Any = None,
        timeout: float = 10.0,
        poll_interval: float = 0.5
    ) -> Tuple[WaitResult, Optional[Any], Optional[str]]:
        """
        Wait for element property to reach expected value.

        Args:
            name: Element name/title
            role: Element role
            app_name: Limit to specific app
            property_name: Property to check (e.g., "AXValue", "AXEnabled")
            expected_value: Expected property value (None = any non-None value)
            timeout: Maximum time to wait
            poll_interval: Time between checks

        Returns:
            Tuple of (result, actual_value, error_message)
        """
        if not self.accessibility_client:
            return WaitResult.ERROR, None, "Accessibility client not available"

        start_time = time.time()
        last_error = None

        logger.info(f"Waiting for property {property_name}={expected_value} on element: name={name}, role={role}")

        while time.time() - start_time < timeout:
            try:
                # Find element
                result, elements, error = self.wait_for_element(
                    name=name,
                    role=role,
                    app_name=app_name,
                    timeout=poll_interval,  # Short timeout for inner wait
                    poll_interval=poll_interval / 2
                )

                if result != WaitResult.SUCCESS or not elements:
                    time.sleep(poll_interval)
                    continue

                # Check property on first element
                element = elements[0]
                actual_value = self.accessibility_client._get_attribute_value(element, property_name)

                # Check if value matches
                if expected_value is None:
                    # Any non-None value is acceptable
                    if actual_value is not None:
                        elapsed = time.time() - start_time
                        logger.info(f"Property {property_name}={actual_value} found after {elapsed:.2f}s")
                        return WaitResult.SUCCESS, actual_value, None
                else:
                    # Exact match required
                    if actual_value == expected_value:
                        elapsed = time.time() - start_time
                        logger.info(f"Property {property_name}={expected_value} found after {elapsed:.2f}s")
                        return WaitResult.SUCCESS, actual_value, None

                time.sleep(poll_interval)

            except Exception as e:
                last_error = str(e)
                logger.debug(f"Error while waiting: {e}")
                time.sleep(poll_interval)

        # Timeout
        elapsed = time.time() - start_time
        error_msg = f"Timeout after {elapsed:.2f}s - property condition not met"
        if last_error:
            error_msg += f": {last_error}"

        logger.warning(error_msg)
        return WaitResult.TIMEOUT, None, error_msg

    def poll_until(
        self,
        condition: Callable[[], bool],
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        error_message: str = "Condition not met"
    ) -> Tuple[WaitResult, Optional[str]]:
        """
        Poll until a condition function returns True.

        Args:
            condition: Function that returns True when condition is met
            timeout: Maximum time to wait
            poll_interval: Time between checks
            error_message: Custom error message on timeout

        Returns:
            Tuple of (result, error_message)
        """
        start_time = time.time()
        last_exception = None

        logger.info(f"Polling until condition met (timeout={timeout}s)")

        while time.time() - start_time < timeout:
            try:
                if condition():
                    elapsed = time.time() - start_time
                    logger.info(f"Condition met after {elapsed:.2f}s")
                    return WaitResult.SUCCESS, None
            except Exception as e:
                last_exception = e
                logger.debug(f"Exception in condition check: {e}")

            time.sleep(poll_interval)

        # Timeout
        elapsed = time.time() - start_time
        error_msg = f"Timeout after {elapsed:.2f}s - {error_message}"
        if last_exception:
            error_msg += f": {last_exception}"

        logger.warning(error_msg)
        return WaitResult.TIMEOUT, error_msg

    def wait_with_retry(
        self,
        operation: Callable[[], Tuple[bool, Any]],
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute operation with automatic retry and exponential backoff.

        Args:
            operation: Function that returns (success, result)
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            backoff_factor: Multiply delay by this factor after each retry
            max_delay: Maximum delay between retries

        Returns:
            Tuple of (success, result, error_message)
        """
        delay = initial_delay
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries + 1}")
                success, result = operation()

                if success:
                    if attempt > 0:
                        logger.info(f"Operation succeeded after {attempt + 1} attempt(s)")
                    return True, result, None

                # Operation returned False but didn't raise exception
                last_error = "Operation returned False"

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

            # Don't sleep after last attempt
            if attempt < max_retries:
                logger.debug(f"Retrying in {delay:.2f}s...")
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)

        # All retries exhausted
        error_msg = f"Failed after {max_retries + 1} attempt(s)"
        if last_error:
            error_msg += f": {last_error}"

        logger.error(error_msg)
        return False, None, error_msg


# Convenience functions

def wait_for_element(
    name: Optional[str] = None,
    role: Optional[str] = None,
    app_name: Optional[str] = None,
    timeout: float = 10.0,
    poll_interval: float = 0.5
) -> Tuple[WaitResult, Optional[List[Any]], Optional[str]]:
    """
    Wait for UI element to appear (convenience function).

    Args:
        name: Element name/title
        role: Element role
        app_name: Limit to app
        timeout: Maximum wait time
        poll_interval: Check interval

    Returns:
        Tuple of (result, elements, error)
    """
    waiter = SmartWaiter()
    return waiter.wait_for_element(name, role, app_name, timeout, poll_interval)


def poll_until(
    condition: Callable[[], bool],
    timeout: float = 10.0,
    poll_interval: float = 0.5
) -> Tuple[WaitResult, Optional[str]]:
    """
    Poll until condition is met (convenience function).

    Args:
        condition: Function returning True when met
        timeout: Maximum wait time
        poll_interval: Check interval

    Returns:
        Tuple of (result, error)
    """
    waiter = SmartWaiter()
    return waiter.poll_until(condition, timeout, poll_interval)


def retry_with_backoff(
    operation: Callable[[], Tuple[bool, Any]],
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> Tuple[bool, Any, Optional[str]]:
    """
    Retry operation with exponential backoff (convenience function).

    Args:
        operation: Function returning (success, result)
        max_retries: Max retry attempts
        initial_delay: Initial delay

    Returns:
        Tuple of (success, result, error)
    """
    waiter = SmartWaiter()
    return waiter.wait_with_retry(operation, max_retries, initial_delay)


# Decorator for automatic retry

def with_retry(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator to automatically retry a function with exponential backoff.

    Args:
        max_retries: Maximum retry attempts
        initial_delay: Initial delay between retries
        backoff_factor: Backoff multiplier

    Example:
        @with_retry(max_retries=3, initial_delay=1.0)
        def unstable_operation():
            # ... operation that might fail
            return result
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}")

                    if attempt < max_retries:
                        time.sleep(delay)
                        delay *= backoff_factor

            # All retries exhausted
            raise last_error

        return wrapper
    return decorator
