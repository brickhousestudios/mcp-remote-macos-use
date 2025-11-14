"""
VNC Connection Manager with connection pooling and caching.

This module provides a connection manager that reuses VNC connections
to improve performance and reduce connection overhead.
"""

import logging
import time
import threading
from typing import Optional, Tuple, Callable, Any
from contextlib import contextmanager
from vnc_client import VNCClient

# Configure logging
logger = logging.getLogger('vnc_connection_manager')
logger.setLevel(logging.DEBUG)


class VNCConnectionManager:
    """
    Manages VNC connections with pooling and caching for improved performance.

    Features:
    - Connection reuse across operations
    - Automatic connection validation
    - Configurable connection timeout
    - Thread-safe operations
    """

    def __init__(
        self,
        host: str,
        port: int = 5900,
        password: Optional[str] = None,
        username: Optional[str] = None,
        encryption: str = "prefer_on",
        connection_timeout: float = 300.0,  # 5 minutes default
        max_idle_time: float = 60.0  # 1 minute default
    ):
        """
        Initialize the VNC connection manager.

        Args:
            host: VNC server hostname or IP
            port: VNC server port
            password: VNC password
            username: VNC username (optional)
            encryption: Encryption preference
            connection_timeout: Max time to keep connection alive (seconds)
            max_idle_time: Max idle time before closing connection (seconds)
        """
        self.host = host
        self.port = port
        self.password = password
        self.username = username
        self.encryption = encryption
        self.connection_timeout = connection_timeout
        self.max_idle_time = max_idle_time

        self._connection: Optional[VNCClient] = None
        self._last_used: float = 0
        self._created_at: float = 0
        self._lock = threading.RLock()

        logger.info(f"Initialized VNC connection manager for {host}:{port}")
        logger.debug(f"Connection timeout: {connection_timeout}s, Max idle: {max_idle_time}s")

    def _is_connection_valid(self) -> bool:
        """
        Check if the current connection is still valid and not expired.

        Returns:
            bool: True if connection is valid and can be reused
        """
        if self._connection is None or self._connection.socket is None:
            return False

        now = time.time()

        # Check if connection has exceeded max lifetime
        if now - self._created_at > self.connection_timeout:
            logger.debug("Connection expired (exceeded max lifetime)")
            return False

        # Check if connection has been idle too long
        if now - self._last_used > self.max_idle_time:
            logger.debug("Connection expired (exceeded max idle time)")
            return False

        # TODO: Could add a ping/health check here
        return True

    def _create_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Create a new VNC connection.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        logger.info(f"Creating new VNC connection to {self.host}:{self.port}")

        # Close any existing connection first
        self._close_connection()

        # Create new connection
        self._connection = VNCClient(
            host=self.host,
            port=self.port,
            password=self.password,
            username=self.username,
            encryption=self.encryption
        )

        success, error_message = self._connection.connect()

        if success:
            self._created_at = time.time()
            self._last_used = time.time()
            logger.info("VNC connection established successfully")
        else:
            logger.error(f"Failed to create VNC connection: {error_message}")
            self._connection = None

        return success, error_message

    def _close_connection(self):
        """Close the current VNC connection if it exists."""
        if self._connection is not None:
            try:
                self._connection.close()
                logger.debug("Closed VNC connection")
            except Exception as e:
                logger.warning(f"Error closing VNC connection: {e}")
            finally:
                self._connection = None

    @contextmanager
    def get_connection(self):
        """
        Get a VNC connection from the pool (context manager).

        Yields:
            VNCClient: A valid VNC connection

        Raises:
            ConnectionError: If unable to establish connection

        Example:
            with manager.get_connection() as vnc:
                vnc.send_mouse_click(100, 100)
        """
        with self._lock:
            # Check if we can reuse existing connection
            if self._is_connection_valid():
                logger.debug("Reusing existing VNC connection")
                self._last_used = time.time()
                try:
                    yield self._connection
                    return
                except Exception as e:
                    logger.warning(f"Error using cached connection: {e}")
                    # Fall through to create new connection

            # Create new connection
            success, error_message = self._create_connection()
            if not success:
                raise ConnectionError(f"Failed to connect to VNC server: {error_message}")

            try:
                yield self._connection
            except Exception as e:
                # If there's an error during use, close the connection
                logger.error(f"Error during VNC operation: {e}")
                self._close_connection()
                raise

    def execute_operation(self, operation: Callable[[VNCClient], Any]) -> Any:
        """
        Execute an operation with a VNC connection from the pool.

        Args:
            operation: Callable that takes a VNCClient and returns a result

        Returns:
            The result of the operation

        Example:
            result = manager.execute_operation(
                lambda vnc: vnc.send_mouse_click(100, 100)
            )
        """
        with self.get_connection() as vnc:
            return operation(vnc)

    def close(self):
        """Close the connection manager and clean up resources."""
        with self._lock:
            self._close_connection()
            logger.info("VNC connection manager closed")

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support for context manager protocol."""
        self.close()
        return False


class GlobalVNCConnectionPool:
    """
    Global singleton pool for managing VNC connections across the application.

    This ensures that we only have one connection per host/port combination,
    reducing overhead and improving performance.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._managers: dict[Tuple[str, int], VNCConnectionManager] = {}
        self._managers_lock = threading.RLock()
        self._initialized = True

        logger.info("Initialized global VNC connection pool")

    def get_manager(
        self,
        host: str,
        port: int = 5900,
        password: Optional[str] = None,
        username: Optional[str] = None,
        encryption: str = "prefer_on",
        connection_timeout: float = 300.0,
        max_idle_time: float = 60.0
    ) -> VNCConnectionManager:
        """
        Get or create a connection manager for the specified host/port.

        Args:
            host: VNC server hostname or IP
            port: VNC server port
            password: VNC password
            username: VNC username (optional)
            encryption: Encryption preference
            connection_timeout: Max time to keep connection alive (seconds)
            max_idle_time: Max idle time before closing connection (seconds)

        Returns:
            VNCConnectionManager: Connection manager for the host/port
        """
        key = (host, port)

        with self._managers_lock:
            if key not in self._managers:
                logger.info(f"Creating new connection manager for {host}:{port}")
                self._managers[key] = VNCConnectionManager(
                    host=host,
                    port=port,
                    password=password,
                    username=username,
                    encryption=encryption,
                    connection_timeout=connection_timeout,
                    max_idle_time=max_idle_time
                )

            return self._managers[key]

    def close_all(self):
        """Close all connection managers in the pool."""
        with self._managers_lock:
            for manager in self._managers.values():
                try:
                    manager.close()
                except Exception as e:
                    logger.warning(f"Error closing manager: {e}")

            self._managers.clear()
            logger.info("Closed all VNC connection managers")


# Global connection pool instance
_global_pool = GlobalVNCConnectionPool()


def get_vnc_manager(
    host: str,
    port: int = 5900,
    password: Optional[str] = None,
    username: Optional[str] = None,
    encryption: str = "prefer_on",
    connection_timeout: float = 300.0,
    max_idle_time: float = 60.0
) -> VNCConnectionManager:
    """
    Get a VNC connection manager from the global pool.

    This is the recommended way to get a connection manager in most cases.

    Args:
        host: VNC server hostname or IP
        port: VNC server port
        password: VNC password
        username: VNC username (optional)
        encryption: Encryption preference
        connection_timeout: Max time to keep connection alive (seconds)
        max_idle_time: Max idle time before closing connection (seconds)

    Returns:
        VNCConnectionManager: Connection manager for the host/port
    """
    return _global_pool.get_manager(
        host=host,
        port=port,
        password=password,
        username=username,
        encryption=encryption,
        connection_timeout=connection_timeout,
        max_idle_time=max_idle_time
    )
