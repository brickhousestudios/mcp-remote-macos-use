"""Rate limiting to prevent abuse and DoS attacks."""
import time
import os
from collections import defaultdict, deque
from typing import Dict, Deque
import threading


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """In-memory rate limiter using sliding window algorithm."""

    def __init__(self, max_calls: int, period_seconds: float):
        """Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in the period
            period_seconds: Time period in seconds
        """
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self._calls: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check_rate_limit(self, key: str) -> None:
        """Check if rate limit is exceeded for a key.

        Args:
            key: The identifier to rate limit (e.g., tool name)

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        with self._lock:
            now = time.time()
            calls = self._calls[key]

            # Remove calls outside the current window
            while calls and calls[0] < now - self.period_seconds:
                calls.popleft()

            # Check if limit exceeded
            if len(calls) >= self.max_calls:
                oldest_call = calls[0]
                reset_time = oldest_call + self.period_seconds
                wait_seconds = reset_time - now
                raise RateLimitExceeded(
                    f"Rate limit exceeded for '{key}'. "
                    f"Maximum {self.max_calls} calls per {self.period_seconds}s. "
                    f"Try again in {wait_seconds:.1f} seconds."
                )

            # Record this call
            calls.append(now)

    def reset(self, key: str = None) -> None:
        """Reset rate limit counters.

        Args:
            key: Optional key to reset. If None, reset all.
        """
        with self._lock:
            if key is None:
                self._calls.clear()
            elif key in self._calls:
                del self._calls[key]


# Global rate limiter instance
_global_rate_limiter = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance.

    Configuration is read from environment variables:
    - VNC_RATE_LIMIT_MAX: Maximum calls per period (default: 100)
    - VNC_RATE_LIMIT_PERIOD: Period in seconds (default: 60)

    Returns:
        Global RateLimiter instance
    """
    global _global_rate_limiter

    if _global_rate_limiter is None:
        with _rate_limiter_lock:
            # Double-check pattern
            if _global_rate_limiter is None:
                max_calls = int(os.environ.get('VNC_RATE_LIMIT_MAX', '100'))
                period_seconds = float(os.environ.get('VNC_RATE_LIMIT_PERIOD', '60'))

                _global_rate_limiter = RateLimiter(
                    max_calls=max_calls,
                    period_seconds=period_seconds
                )

    return _global_rate_limiter


def check_tool_rate_limit(tool_name: str) -> None:
    """Check rate limit for a tool invocation.

    Args:
        tool_name: Name of the tool being called

    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    limiter = get_rate_limiter()
    limiter.check_rate_limit(tool_name)
