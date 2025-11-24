"""
Window management utilities for macOS.

Provides comprehensive window control including resize, move, minimize/maximize,
fullscreen, switching between windows, and closing windows.
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum

try:
    from Cocoa import (
        NSWorkspace,
        NSRunningApplication,
        NSApplicationActivationOptions,
        NSApplicationActivateIgnoringOtherApps,
        NSApplicationActivateAllWindows,
    )
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGWindowListExcludeDesktopElements,
        kCGNullWindowID,
        CGWindowListCreateDescriptionFromArray,
    )
    from ApplicationServices import (
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        AXUIElementSetAttributeValue,
        kAXErrorSuccess,
        kAXWindowsAttribute,
        kAXFocusedWindowAttribute,
        kAXPositionAttribute,
        kAXSizeAttribute,
        kAXMinimizedAttribute,
        kAXTitleAttribute,
        kAXCloseButtonAttribute,
        kAXZoomButtonAttribute,
        kAXMinimizeButtonAttribute,
        kAXFullscreenButtonAttribute,
    )
    from CoreGraphics import (
        CGPoint,
        CGSize,
    )
    WINDOW_MANAGER_AVAILABLE = True
except ImportError:
    WINDOW_MANAGER_AVAILABLE = False

# Configure logging
logger = logging.getLogger('window_manager')
logger.setLevel(logging.DEBUG)


class WindowAction(Enum):
    """Window actions."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    FULLSCREEN = "fullscreen"
    CLOSE = "close"
    RESTORE = "restore"


class WindowManager:
    """
    Window management for macOS applications.

    Features:
    - List all windows
    - Get window info (position, size, title)
    - Resize windows
    - Move windows
    - Minimize/maximize/fullscreen
    - Switch between windows
    - Close windows
    """

    def __init__(self):
        """Initialize window manager."""
        if not WINDOW_MANAGER_AVAILABLE:
            raise ImportError("Window management requires macOS with Cocoa/Quartz frameworks")

        self.workspace = NSWorkspace.sharedWorkspace()
        logger.info("Initialized window manager")

    def get_app_pid(self, app_name: str) -> Optional[int]:
        """
        Get PID for application by name.

        Args:
            app_name: Application name

        Returns:
            PID or None if not found
        """
        running_apps = self.workspace.runningApplications()
        for app in running_apps:
            if app.localizedName().lower() == app_name.lower():
                return app.processIdentifier()
        return None

    def get_app_windows(self, pid: int) -> List[Any]:
        """
        Get all windows for an application.

        Args:
            pid: Process ID

        Returns:
            List of AXUIElement window objects
        """
        try:
            app_element = AXUIElementCreateApplication(pid)

            # Get windows attribute
            error_code, windows = AXUIElementCopyAttributeValue(
                app_element,
                kAXWindowsAttribute,
                None
            )

            if error_code != kAXErrorSuccess or not windows:
                logger.warning(f"No windows found for PID {pid}")
                return []

            return list(windows)

        except Exception as e:
            logger.error(f"Error getting windows for PID {pid}: {e}")
            return []

    def get_focused_window(self, pid: int) -> Optional[Any]:
        """
        Get focused window for an application.

        Args:
            pid: Process ID

        Returns:
            AXUIElement window object or None
        """
        try:
            app_element = AXUIElementCreateApplication(pid)

            error_code, focused_window = AXUIElementCopyAttributeValue(
                app_element,
                kAXFocusedWindowAttribute,
                None
            )

            if error_code != kAXErrorSuccess:
                logger.debug(f"No focused window for PID {pid}")
                return None

            return focused_window

        except Exception as e:
            logger.error(f"Error getting focused window: {e}")
            return None

    def get_window_info(self, window) -> Dict[str, Any]:
        """
        Get window information.

        Args:
            window: AXUIElement window object

        Returns:
            Dictionary with window info
        """
        info = {}

        try:
            # Get title
            error_code, title = AXUIElementCopyAttributeValue(
                window,
                kAXTitleAttribute,
                None
            )
            if error_code == kAXErrorSuccess:
                info['title'] = str(title) if title else "Untitled"

            # Get position
            error_code, position = AXUIElementCopyAttributeValue(
                window,
                kAXPositionAttribute,
                None
            )
            if error_code == kAXErrorSuccess and position:
                info['x'] = int(position.x)
                info['y'] = int(position.y)

            # Get size
            error_code, size = AXUIElementCopyAttributeValue(
                window,
                kAXSizeAttribute,
                None
            )
            if error_code == kAXErrorSuccess and size:
                info['width'] = int(size.width)
                info['height'] = int(size.height)

            # Get minimized state
            error_code, minimized = AXUIElementCopyAttributeValue(
                window,
                kAXMinimizedAttribute,
                None
            )
            if error_code == kAXErrorSuccess:
                info['minimized'] = bool(minimized)

        except Exception as e:
            logger.error(f"Error getting window info: {e}")

        return info

    def resize_window(
        self,
        window,
        width: int,
        height: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Resize a window.

        Args:
            window: AXUIElement window object
            width: New width in pixels
            height: New height in pixels

        Returns:
            Tuple of (success, error_message)
        """
        try:
            new_size = CGSize(width, height)

            error_code = AXUIElementSetAttributeValue(
                window,
                kAXSizeAttribute,
                new_size
            )

            if error_code != kAXErrorSuccess:
                return False, f"Failed to resize window (error code: {error_code})"

            logger.info(f"Resized window to {width}x{height}")
            return True, None

        except Exception as e:
            error = f"Error resizing window: {str(e)}"
            logger.error(error)
            return False, error

    def move_window(
        self,
        window,
        x: int,
        y: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Move a window to new position.

        Args:
            window: AXUIElement window object
            x: New x coordinate
            y: New y coordinate

        Returns:
            Tuple of (success, error_message)
        """
        try:
            new_position = CGPoint(x, y)

            error_code = AXUIElementSetAttributeValue(
                window,
                kAXPositionAttribute,
                new_position
            )

            if error_code != kAXErrorSuccess:
                return False, f"Failed to move window (error code: {error_code})"

            logger.info(f"Moved window to ({x}, {y})")
            return True, None

        except Exception as e:
            error = f"Error moving window: {str(e)}"
            logger.error(error)
            return False, error

    def set_window_bounds(
        self,
        window,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Set window position and size in one operation.

        Args:
            window: AXUIElement window object
            x: X coordinate
            y: Y coordinate
            width: Width in pixels
            height: Height in pixels

        Returns:
            Tuple of (success, error_message)
        """
        # Move first
        success, error = self.move_window(window, x, y)
        if not success:
            return False, error

        # Then resize
        return self.resize_window(window, width, height)

    def minimize_window(self, window) -> Tuple[bool, Optional[str]]:
        """
        Minimize a window.

        Args:
            window: AXUIElement window object

        Returns:
            Tuple of (success, error_message)
        """
        try:
            error_code = AXUIElementSetAttributeValue(
                window,
                kAXMinimizedAttribute,
                True
            )

            if error_code != kAXErrorSuccess:
                return False, f"Failed to minimize window (error code: {error_code})"

            logger.info("Minimized window")
            return True, None

        except Exception as e:
            error = f"Error minimizing window: {str(e)}"
            logger.error(error)
            return False, error

    def restore_window(self, window) -> Tuple[bool, Optional[str]]:
        """
        Restore a minimized window.

        Args:
            window: AXUIElement window object

        Returns:
            Tuple of (success, error_message)
        """
        try:
            error_code = AXUIElementSetAttributeValue(
                window,
                kAXMinimizedAttribute,
                False
            )

            if error_code != kAXErrorSuccess:
                return False, f"Failed to restore window (error code: {error_code})"

            logger.info("Restored window")
            return True, None

        except Exception as e:
            error = f"Error restoring window: {str(e)}"
            logger.error(error)
            return False, error

    def click_window_button(
        self,
        window,
        button_attribute: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Click a window button (close, minimize, maximize, fullscreen).

        Args:
            window: AXUIElement window object
            button_attribute: Button attribute (e.g., kAXCloseButtonAttribute)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get the button element
            error_code, button = AXUIElementCopyAttributeValue(
                window,
                button_attribute,
                None
            )

            if error_code != kAXErrorSuccess or not button:
                return False, f"Button not found (error code: {error_code})"

            # Press the button
            from ApplicationServices import AXUIElementPerformAction, kAXPressAction

            error_code = AXUIElementPerformAction(button, kAXPressAction)

            if error_code != kAXErrorSuccess:
                return False, f"Failed to click button (error code: {error_code})"

            logger.info(f"Clicked window button: {button_attribute}")
            return True, None

        except Exception as e:
            error = f"Error clicking window button: {str(e)}"
            logger.error(error)
            return False, error

    def close_window(self, window) -> Tuple[bool, Optional[str]]:
        """Close a window."""
        return self.click_window_button(window, kAXCloseButtonAttribute)

    def maximize_window(self, window) -> Tuple[bool, Optional[str]]:
        """Maximize a window (zoom button)."""
        return self.click_window_button(window, kAXZoomButtonAttribute)

    def fullscreen_window(self, window) -> Tuple[bool, Optional[str]]:
        """Toggle fullscreen mode for a window."""
        return self.click_window_button(window, kAXFullscreenButtonAttribute)

    def switch_to_window(
        self,
        app_name: str,
        window_title: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Switch to a specific window by app name and optionally window title.

        Args:
            app_name: Application name
            window_title: Optional window title to match

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Find the app
            running_apps = self.workspace.runningApplications()
            target_app = None

            for app in running_apps:
                if app.localizedName().lower() == app_name.lower():
                    target_app = app
                    break

            if not target_app:
                return False, f"Application not found: {app_name}"

            # Activate the app
            success = target_app.activateWithOptions_(
                NSApplicationActivateAllWindows | NSApplicationActivateIgnoringOtherApps
            )

            if not success:
                return False, f"Failed to activate application: {app_name}"

            # If window title specified, find and focus that window
            if window_title:
                pid = target_app.processIdentifier()
                windows = self.get_app_windows(pid)

                for window in windows:
                    info = self.get_window_info(window)
                    if info.get('title', '').lower() == window_title.lower():
                        # Raise this specific window
                        from ApplicationServices import AXUIElementPerformAction, kAXRaiseAction
                        AXUIElementPerformAction(window, kAXRaiseAction)
                        logger.info(f"Switched to window: {window_title}")
                        return True, None

                return False, f"Window not found: {window_title}"

            logger.info(f"Switched to app: {app_name}")
            return True, None

        except Exception as e:
            error = f"Error switching to window: {str(e)}"
            logger.error(error)
            return False, error

    def list_all_windows(
        self,
        app_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all windows, optionally filtered by app name.

        Args:
            app_name: Optional app name to filter

        Returns:
            List of window info dictionaries
        """
        all_windows = []

        try:
            running_apps = self.workspace.runningApplications()

            for app in running_apps:
                # Filter by app name if specified
                if app_name and app.localizedName().lower() != app_name.lower():
                    continue

                pid = app.processIdentifier()
                app_name_str = app.localizedName()

                windows = self.get_app_windows(pid)

                for window in windows:
                    info = self.get_window_info(window)
                    info['app_name'] = app_name_str
                    info['pid'] = pid
                    all_windows.append(info)

            logger.info(f"Found {len(all_windows)} windows")
            return all_windows

        except Exception as e:
            logger.error(f"Error listing windows: {e}")
            return []

    def get_window_by_title(
        self,
        title: str,
        app_name: Optional[str] = None
    ) -> Tuple[Optional[Any], Optional[int], Optional[str]]:
        """
        Find window by title.

        Args:
            title: Window title to search for
            app_name: Optional app name to limit search

        Returns:
            Tuple of (window_element, pid, error_message)
        """
        try:
            running_apps = self.workspace.runningApplications()

            for app in running_apps:
                # Filter by app name if specified
                if app_name and app.localizedName().lower() != app_name.lower():
                    continue

                pid = app.processIdentifier()
                windows = self.get_app_windows(pid)

                for window in windows:
                    info = self.get_window_info(window)
                    if info.get('title', '').lower() == title.lower():
                        return window, pid, None

            return None, None, f"Window not found: {title}"

        except Exception as e:
            return None, None, f"Error finding window: {str(e)}"


# Convenience functions

def check_window_manager_available() -> bool:
    """Check if window manager is available."""
    return WINDOW_MANAGER_AVAILABLE


def resize_window_by_title(
    title: str,
    width: int,
    height: int,
    app_name: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Resize window by title (convenience function).

    Args:
        title: Window title
        width: New width
        height: New height
        app_name: Optional app name filter

    Returns:
        Tuple of (success, error_message)
    """
    try:
        manager = WindowManager()
        window, pid, error = manager.get_window_by_title(title, app_name)

        if not window:
            return False, error

        return manager.resize_window(window, width, height)

    except Exception as e:
        return False, str(e)


def move_window_by_title(
    title: str,
    x: int,
    y: int,
    app_name: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Move window by title (convenience function).

    Args:
        title: Window title
        x: New x coordinate
        y: New y coordinate
        app_name: Optional app name filter

    Returns:
        Tuple of (success, error_message)
    """
    try:
        manager = WindowManager()
        window, pid, error = manager.get_window_by_title(title, app_name)

        if not window:
            return False, error

        return manager.move_window(window, x, y)

    except Exception as e:
        return False, str(e)
