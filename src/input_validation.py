"""Input validation utilities for security."""
import re
from typing import Tuple


# Security constants
MAX_TEXT_LENGTH = 10000  # Maximum characters for text input
MAX_APP_IDENTIFIER_LENGTH = 255  # Maximum length for application identifier
MIN_COORDINATE = -10000  # Minimum coordinate value
MAX_COORDINATE = 100000  # Maximum coordinate value
MIN_DIMENSION = 1  # Minimum screen dimension
MAX_DIMENSION = 16384  # Maximum screen dimension (8K resolution)
MIN_DELAY_MS = 0  # Minimum delay
MAX_DELAY_MS = 10000  # Maximum delay (10 seconds)
MAX_DRAG_STEPS = 1000  # Maximum steps for drag operation

# Safe charset for application identifiers
SAFE_APP_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.()]+$')


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_text(text: str) -> str:
    """Validate text input for key sending.

    Args:
        text: The text to validate

    Returns:
        Validated text

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(text, str):
        raise ValidationError(f"Text must be a string, got {type(text)}")

    if len(text) > MAX_TEXT_LENGTH:
        raise ValidationError(
            f"Text length {len(text)} exceeds maximum {MAX_TEXT_LENGTH}"
        )

    # Strip control characters except common ones (tab, newline, return)
    allowed_controls = {'\t', '\n', '\r', '\b'}
    cleaned = ''.join(
        char for char in text
        if char in allowed_controls or not (ord(char) < 32 or ord(char) == 127)
    )

    return cleaned


def validate_coordinates(
    x: int,
    y: int,
    source_width: int,
    source_height: int
) -> Tuple[int, int, int, int]:
    """Validate coordinate inputs.

    Args:
        x: X coordinate
        y: Y coordinate
        source_width: Source screen width
        source_height: Source screen height

    Returns:
        Tuple of validated (x, y, source_width, source_height)

    Raises:
        ValidationError: If validation fails
    """
    # Validate types
    if not all(isinstance(val, int) for val in [x, y, source_width, source_height]):
        raise ValidationError("All coordinate values must be integers")

    # Validate coordinate bounds
    if not (MIN_COORDINATE <= x <= MAX_COORDINATE):
        raise ValidationError(
            f"X coordinate {x} outside valid range [{MIN_COORDINATE}, {MAX_COORDINATE}]"
        )

    if not (MIN_COORDINATE <= y <= MAX_COORDINATE):
        raise ValidationError(
            f"Y coordinate {y} outside valid range [{MIN_COORDINATE}, {MAX_COORDINATE}]"
        )

    # Validate dimensions
    if not (MIN_DIMENSION <= source_width <= MAX_DIMENSION):
        raise ValidationError(
            f"Source width {source_width} outside valid range [{MIN_DIMENSION}, {MAX_DIMENSION}]"
        )

    if not (MIN_DIMENSION <= source_height <= MAX_DIMENSION):
        raise ValidationError(
            f"Source height {source_height} outside valid range [{MIN_DIMENSION}, {MAX_DIMENSION}]"
        )

    return x, y, source_width, source_height


def validate_application_identifier(identifier: str) -> str:
    """Validate application identifier.

    Args:
        identifier: Application name, path, or bundle ID

    Returns:
        Validated identifier

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(identifier, str):
        raise ValidationError(f"Identifier must be a string, got {type(identifier)}")

    if not identifier:
        raise ValidationError("Identifier cannot be empty")

    if len(identifier) > MAX_APP_IDENTIFIER_LENGTH:
        raise ValidationError(
            f"Identifier length {len(identifier)} exceeds maximum {MAX_APP_IDENTIFIER_LENGTH}"
        )

    # Check for safe characters only (prevent command injection)
    if not SAFE_APP_IDENTIFIER_PATTERN.match(identifier):
        raise ValidationError(
            f"Identifier contains unsafe characters. Only alphanumeric, space, hyphen, "
            f"underscore, period, and parentheses are allowed: {identifier}"
        )

    return identifier.strip()


def validate_button(button: int) -> int:
    """Validate mouse button number.

    Args:
        button: Mouse button number

    Returns:
        Validated button number

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(button, int):
        raise ValidationError(f"Button must be an integer, got {type(button)}")

    if button not in [1, 2, 3]:
        raise ValidationError(f"Button must be 1 (left), 2 (middle), or 3 (right), got {button}")

    return button


def validate_delay(delay_ms: int) -> int:
    """Validate delay value.

    Args:
        delay_ms: Delay in milliseconds

    Returns:
        Validated delay

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(delay_ms, int):
        raise ValidationError(f"Delay must be an integer, got {type(delay_ms)}")

    if not (MIN_DELAY_MS <= delay_ms <= MAX_DELAY_MS):
        raise ValidationError(
            f"Delay {delay_ms}ms outside valid range [{MIN_DELAY_MS}, {MAX_DELAY_MS}]"
        )

    return delay_ms


def validate_drag_steps(steps: int) -> int:
    """Validate drag operation steps.

    Args:
        steps: Number of steps

    Returns:
        Validated steps

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(steps, int):
        raise ValidationError(f"Steps must be an integer, got {type(steps)}")

    if not (1 <= steps <= MAX_DRAG_STEPS):
        raise ValidationError(
            f"Steps {steps} outside valid range [1, {MAX_DRAG_STEPS}]"
        )

    return steps


def validate_scroll_direction(direction: str) -> str:
    """Validate scroll direction.

    Args:
        direction: Scroll direction

    Returns:
        Validated direction

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(direction, str):
        raise ValidationError(f"Direction must be a string, got {type(direction)}")

    direction = direction.lower().strip()
    if direction not in ['up', 'down']:
        raise ValidationError(f"Direction must be 'up' or 'down', got '{direction}'")

    return direction
