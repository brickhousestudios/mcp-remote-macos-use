"""
Intelligent Control Router for macOS automation.

Automatically selects the best control method:
- Accessibility API (native) for local control
- VNC for remote control
- MLX vision for visual tasks

Provides a unified interface regardless of the underlying method.
"""

import logging
import os
import socket
from typing import Optional, Tuple, Dict, Any, List
from enum import Enum

# Import our modules
from accessibility_client import (
    AccessibilityClient,
    check_accessibility_available,
    check_accessibility_enabled
)
from vnc_connection_manager import get_vnc_manager
from mlx_vision import (
    MLXVisionEngine,
    check_mlx_available,
    create_vision_engine
)

# Configure logging
logger = logging.getLogger('control_router')
logger.setLevel(logging.DEBUG)


class ControlMethod(Enum):
    """Available control methods."""
    ACCESSIBILITY = "accessibility"  # Native macOS Accessibility API
    VNC = "vnc"                      # VNC for remote control
    HYBRID = "hybrid"                # Combination of methods


class ControlRouter:
    """
    Intelligent router that selects the best control method.

    Decision tree:
    1. Check if target is localhost → Use Accessibility API
    2. Check if remote host → Use VNC
    3. Use MLX vision to augment either method when needed
    """

    def __init__(
        self,
        host: str,
        port: int = 5900,
        password: Optional[str] = None,
        username: Optional[str] = None,
        encryption: str = "prefer_on",
        prefer_native: bool = True
    ):
        """
        Initialize the control router.

        Args:
            host: Target host (can be localhost, 127.0.0.1, or remote)
            port: VNC port (for remote)
            password: VNC password (for remote)
            username: VNC username (for remote)
            encryption: VNC encryption preference
            prefer_native: Prefer Accessibility API when available
        """
        self.host = host
        self.port = port
        self.password = password
        self.username = username
        self.encryption = encryption
        self.prefer_native = prefer_native

        # Determine control method
        self.control_method = self._determine_control_method()

        # Initialize clients
        self.accessibility_client: Optional[AccessibilityClient] = None
        self.vnc_manager = None
        self.vision_engine: Optional[MLXVisionEngine] = None

        # Initialize based on control method
        if self.control_method in [ControlMethod.ACCESSIBILITY, ControlMethod.HYBRID]:
            try:
                self.accessibility_client = AccessibilityClient()
                logger.info("Initialized Accessibility API client")
            except Exception as e:
                logger.warning(f"Failed to initialize Accessibility API: {e}")
                if self.control_method == ControlMethod.ACCESSIBILITY:
                    # Fall back to VNC
                    self.control_method = ControlMethod.VNC

        if self.control_method in [ControlMethod.VNC, ControlMethod.HYBRID]:
            self.vnc_manager = get_vnc_manager(
                host=host,
                port=port,
                password=password,
                username=username,
                encryption=encryption
            )
            logger.info("Initialized VNC connection manager")

        # Initialize vision engine if available
        if check_mlx_available():
            try:
                self.vision_engine = create_vision_engine()
                logger.info("Initialized MLX vision engine")
            except Exception as e:
                logger.warning(f"Failed to initialize MLX vision: {e}")

        logger.info(f"Control router initialized with method: {self.control_method.value}")

    def _determine_control_method(self) -> ControlMethod:
        """
        Determine the best control method based on target host.

        Returns:
            ControlMethod: Recommended control method
        """
        # Check if target is localhost
        is_local = self._is_localhost(self.host)

        if is_local and self.prefer_native:
            # Check if Accessibility API is available
            if check_accessibility_available():
                if check_accessibility_enabled():
                    logger.info("Using Accessibility API (local + native)")
                    return ControlMethod.ACCESSIBILITY
                else:
                    logger.warning("Accessibility permissions not granted, falling back to VNC")
                    return ControlMethod.VNC
            else:
                logger.warning("Accessibility API not available, using VNC")
                return ControlMethod.VNC
        else:
            logger.info(f"Using VNC for remote host: {self.host}")
            return ControlMethod.VNC

    def _is_localhost(self, host: str) -> bool:
        """
        Check if a host is localhost.

        Args:
            host: Hostname or IP

        Returns:
            bool: True if localhost
        """
        if host in ['localhost', '127.0.0.1', '::1']:
            return True

        # Try resolving hostname
        try:
            hostname = socket.gethostname()
            host_ip = socket.gethostbyname(host)
            local_ip = socket.gethostbyname(hostname)

            return host_ip == local_ip or host_ip == '127.0.0.1'
        except:
            return False

    def click(self, x: int, y: int, button: int = 1) -> bool:
        """
        Click at coordinates or find and click element.

        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button (1=left, 2=middle, 3=right)

        Returns:
            bool: True if successful
        """
        if self.control_method == ControlMethod.ACCESSIBILITY:
            # TODO: Implement element finding at coordinates
            logger.warning("Coordinate-based click not yet implemented for Accessibility API")
            # Fall back to VNC if available
            if self.vnc_manager:
                with self.vnc_manager.get_connection() as vnc:
                    return vnc.send_mouse_click(x, y, button, False)
            return False

        elif self.control_method == ControlMethod.VNC:
            with self.vnc_manager.get_connection() as vnc:
                return vnc.send_mouse_click(x, y, button, False)

        return False

    def click_element_by_name(self, name: str, role: Optional[str] = None) -> bool:
        """
        Click an element by its name (semantic action).

        Args:
            name: Element name/title
            role: Optional role filter

        Returns:
            bool: True if successful
        """
        if self.accessibility_client:
            return self.accessibility_client.click_by_name(name, role=role)
        else:
            logger.error("Accessibility API not available for semantic actions")
            return False

    def type_text(self, text: str) -> bool:
        """
        Type text into focused element.

        Args:
            text: Text to type

        Returns:
            bool: True if successful
        """
        if self.control_method == ControlMethod.ACCESSIBILITY:
            return self.accessibility_client.type_text(text)

        elif self.control_method == ControlMethod.VNC:
            with self.vnc_manager.get_connection() as vnc:
                return vnc.send_text(text)

        return False

    def launch_application(self, app_name: str) -> bool:
        """
        Launch an application.

        Args:
            app_name: Application name

        Returns:
            bool: True if successful
        """
        if self.accessibility_client:
            # Use native launch
            return self.accessibility_client.launch_application(app_name)
        else:
            # Use VNC with Spotlight (legacy method)
            logger.info(f"Launching {app_name} via VNC/Spotlight")
            # Would call the existing VNC-based launch method
            return False

    def find_elements(
        self,
        role: Optional[str] = None,
        title: Optional[str] = None
    ) -> List[Any]:
        """
        Find UI elements matching criteria.

        Args:
            role: Element role
            title: Element title/name

        Returns:
            List of elements
        """
        if self.accessibility_client:
            return self.accessibility_client.find_elements(role=role, title=title)
        else:
            logger.warning("Element finding only available with Accessibility API")
            return []

    def get_screen_info(self) -> Dict[str, Any]:
        """
        Get information about the current screen/UI state.

        Returns:
            Dictionary with screen info
        """
        info = {
            "control_method": self.control_method.value,
            "host": self.host,
        }

        if self.accessibility_client:
            app_info = self.accessibility_client.get_focused_application()
            if app_info:
                info["focused_app"] = {
                    "name": app_info[0],
                    "pid": app_info[1]
                }

        return info

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get the capabilities of the current control method.

        Returns:
            Dictionary of capability flags
        """
        return {
            "accessibility_api": self.accessibility_client is not None,
            "vnc": self.vnc_manager is not None,
            "mlx_vision": self.vision_engine is not None,
            "semantic_actions": self.accessibility_client is not None,
            "coordinate_actions": True,  # Both methods support this
            "ocr": self.vision_engine is not None,
            "visual_grounding": self.vision_engine is not None,
        }


def create_router(
    host: Optional[str] = None,
    port: int = 5900,
    password: Optional[str] = None,
    username: Optional[str] = None,
    encryption: str = "prefer_on"
) -> ControlRouter:
    """
    Create a control router with automatic configuration.

    If host is not specified, defaults to localhost and uses Accessibility API.

    Args:
        host: Target host (defaults to localhost)
        port: VNC port
        password: VNC password
        username: VNC username
        encryption: VNC encryption preference

    Returns:
        ControlRouter instance
    """
    # Default to localhost if not specified
    if host is None:
        host = os.environ.get('MACOS_HOST', 'localhost')

    return ControlRouter(
        host=host,
        port=port,
        password=password,
        username=username,
        encryption=encryption
    )
