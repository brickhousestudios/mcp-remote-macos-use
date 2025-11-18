"""Secure logging utilities to prevent credential leakage."""
import logging
import re
from typing import Any


class SecureLogFilter(logging.Filter):
    """Filter to strip sensitive information from log messages."""

    # Patterns that might contain sensitive data
    SENSITIVE_PATTERNS = [
        (re.compile(r'password[=:\s]+[^\s,}\]]+', re.IGNORECASE), 'password=***'),
        (re.compile(r'passwd[=:\s]+[^\s,}\]]+', re.IGNORECASE), 'passwd=***'),
        (re.compile(r'pwd[=:\s]+[^\s,}\]]+', re.IGNORECASE), 'pwd=***'),
        (re.compile(r'secret[=:\s]+[^\s,}\]]+', re.IGNORECASE), 'secret=***'),
        (re.compile(r'token[=:\s]+[^\s,}\]]+', re.IGNORECASE), 'token=***'),
        (re.compile(r'api[_-]?key[=:\s]+[^\s,}\]]+', re.IGNORECASE), 'api_key=***'),
        (re.compile(r'auth[=:\s]+[^\s,}\]]+', re.IGNORECASE), 'auth=***'),
        # VNC URLs with embedded credentials
        (re.compile(r'vnc://[^:]+:[^@]+@', re.IGNORECASE), 'vnc://***:***@'),
        # Environment variable patterns
        (re.compile(r"MACOS_PASSWORD['\"]?\s*[=:]\s*['\"]?[^'\"\s,}]+", re.IGNORECASE), "MACOS_PASSWORD='***'"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and sanitize log record.

        Args:
            record: The log record to filter

        Returns:
            True (always pass the record, but sanitize it first)
        """
        if record.msg:
            message = str(record.msg)
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                message = pattern.sub(replacement, message)
            record.msg = message

        # Sanitize args if present
        if record.args:
            sanitized_args = []
            for arg in record.args if isinstance(record.args, tuple) else [record.args]:
                if isinstance(arg, str):
                    sanitized = arg
                    for pattern, replacement in self.SENSITIVE_PATTERNS:
                        sanitized = pattern.sub(replacement, sanitized)
                    sanitized_args.append(sanitized)
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args) if isinstance(record.args, tuple) else sanitized_args[0]

        return True


def setup_secure_logging(name: str, level: str = 'INFO') -> logging.Logger:
    """Set up a logger with secure filtering.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Add secure filter to prevent credential leakage
    secure_filter = SecureLogFilter()

    # Apply filter to all handlers
    for handler in logger.handlers:
        handler.addFilter(secure_filter)

    # If no handlers exist, add a default one with the filter
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(numeric_level)
        handler.addFilter(secure_filter)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
