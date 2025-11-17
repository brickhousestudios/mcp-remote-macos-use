"""
Advanced interaction utilities for macOS.

Provides right-click/context menus, text selection, and multi-finger gestures.
"""

import logging
import time
from typing import Optional, Tuple, List
from enum import Enum

try:
    from vnc_client import VNCClient
    VNC_AVAILABLE = True
except ImportError:
    VNC_AVAILABLE = False

try:
    from ApplicationServices import (
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        AXUIElementSetAttributeValue,
        AXUIElementPerformAction,
        kAXErrorSuccess,
        kAXSelectedTextAttribute,
        kAXSelectedTextRangeAttribute,
        kAXValueAttribute,
        kAXFocusedUIElementAttribute,
    )
    from Quartz import (
        CGEventCreateMouseEvent,
        CGEventPost,
        CGEventCreateScrollWheelEvent,
        kCGEventMouseMoved,
        kCGEventLeftMouseDown,
        kCGEventLeftMouseUp,
        kCGEventRightMouseDown,
        kCGEventRightMouseUp,
        kCGEventScrollWheel,
        kCGMouseButtonLeft,
        kCGMouseButtonRight,
        kCGHIDEventTap,
        kCGScrollEventUnitPixel,
    )
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False

# Configure logging
logger = logging.getLogger('advanced_interactions')
logger.setLevel(logging.DEBUG)


class GestureType(Enum):
    """Multi-finger gesture types."""
    PINCH_IN = "pinch_in"      # Zoom out
    PINCH_OUT = "pinch_out"    # Zoom in
    ROTATE_LEFT = "rotate_left"
    ROTATE_RIGHT = "rotate_right"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"


class AdvancedInteractions:
    """
    Advanced interaction utilities for macOS.

    Features:
    - Right-click / context menus
    - Text selection and manipulation
    - Multi-finger gestures (pinch, zoom, rotate)
    - Advanced scrolling
    """

    def __init__(self):
        """Initialize advanced interactions."""
        if not QUARTZ_AVAILABLE:
            logger.warning("Quartz framework not available - limited functionality")

        logger.info("Initialized advanced interactions")

    def right_click(
        self,
        x: int,
        y: int,
        delay: float = 0.1
    ) -> Tuple[bool, Optional[str]]:
        """
        Perform right-click at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            delay: Delay between mouse down and up (seconds)

        Returns:
            Tuple of (success, error_message)
        """
        if not QUARTZ_AVAILABLE:
            return False, "Quartz framework not available"

        try:
            # Create right mouse down event
            mouse_down = CGEventCreateMouseEvent(
                None,
                kCGEventRightMouseDown,
                (x, y),
                kCGMouseButtonRight
            )

            # Create right mouse up event
            mouse_up = CGEventCreateMouseEvent(
                None,
                kCGEventRightMouseUp,
                (x, y),
                kCGMouseButtonRight
            )

            # Post events
            CGEventPost(kCGHIDEventTap, mouse_down)
            time.sleep(delay)
            CGEventPost(kCGHIDEventTap, mouse_up)

            logger.info(f"Right-clicked at ({x}, {y})")
            return True, None

        except Exception as e:
            error = f"Error performing right-click: {str(e)}"
            logger.error(error)
            return False, error

    def context_menu_click(
        self,
        x: int,
        y: int,
        menu_item: Optional[str] = None,
        delay: float = 0.5
    ) -> Tuple[bool, Optional[str]]:
        """
        Right-click and optionally select menu item.

        Args:
            x: X coordinate for right-click
            y: Y coordinate for right-click
            menu_item: Optional menu item name to click
            delay: Delay after right-click before selecting item

        Returns:
            Tuple of (success, error_message)
        """
        # Perform right-click
        success, error = self.right_click(x, y)
        if not success:
            return False, error

        # If menu item specified, try to click it using Accessibility API
        if menu_item:
            time.sleep(delay)

            try:
                from accessibility_client import AccessibilityClient
                client = AccessibilityClient()

                # Find menu item
                elements = client.find_elements(role="AXMenuItem", title=menu_item)

                if not elements:
                    return False, f"Menu item not found: {menu_item}"

                # Click the menu item
                success = client.click_element(elements[0])

                if success:
                    logger.info(f"Clicked menu item: {menu_item}")
                    return True, None
                else:
                    return False, f"Failed to click menu item: {menu_item}"

            except Exception as e:
                return False, f"Error clicking menu item: {str(e)}"

        return True, None

    def select_text(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Select text by dragging from start to end position.

        Args:
            start_x: Start X coordinate
            start_y: Start Y coordinate
            end_x: End X coordinate
            end_y: End Y coordinate

        Returns:
            Tuple of (success, error_message)
        """
        if not QUARTZ_AVAILABLE:
            return False, "Quartz framework not available"

        try:
            # Mouse down at start
            mouse_down = CGEventCreateMouseEvent(
                None,
                kCGEventLeftMouseDown,
                (start_x, start_y),
                kCGMouseButtonLeft
            )
            CGEventPost(kCGHIDEventTap, mouse_down)

            # Move to end position (dragging)
            time.sleep(0.05)
            mouse_drag = CGEventCreateMouseEvent(
                None,
                kCGEventMouseMoved,
                (end_x, end_y),
                kCGMouseButtonLeft
            )
            CGEventPost(kCGHIDEventTap, mouse_drag)

            # Mouse up at end
            time.sleep(0.05)
            mouse_up = CGEventCreateMouseEvent(
                None,
                kCGEventLeftMouseUp,
                (end_x, end_y),
                kCGMouseButtonLeft
            )
            CGEventPost(kCGHIDEventTap, mouse_up)

            logger.info(f"Selected text from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            return True, None

        except Exception as e:
            error = f"Error selecting text: {str(e)}"
            logger.error(error)
            return False, error

    def get_selected_text(
        self,
        app_name: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get currently selected text using Accessibility API.

        Args:
            app_name: Optional app name to get selection from

        Returns:
            Tuple of (selected_text, error_message)
        """
        try:
            from Cocoa import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()

            # Get focused app if not specified
            if not app_name:
                focused_app = workspace.frontmostApplication()
                pid = focused_app.processIdentifier()
            else:
                running_apps = workspace.runningApplications()
                pid = None
                for app in running_apps:
                    if app.localizedName().lower() == app_name.lower():
                        pid = app.processIdentifier()
                        break

                if not pid:
                    return None, f"App not found: {app_name}"

            # Get app element
            app_element = AXUIElementCreateApplication(pid)

            # Get focused element
            error_code, focused_element = AXUIElementCopyAttributeValue(
                app_element,
                kAXFocusedUIElementAttribute,
                None
            )

            if error_code != kAXErrorSuccess or not focused_element:
                return None, "No focused element found"

            # Get selected text
            error_code, selected_text = AXUIElementCopyAttributeValue(
                focused_element,
                kAXSelectedTextAttribute,
                None
            )

            if error_code != kAXErrorSuccess:
                return None, "No text selected or unable to get selection"

            return str(selected_text) if selected_text else "", None

        except Exception as e:
            return None, f"Error getting selected text: {str(e)}"

    def select_all_text(self, app_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Select all text in focused element (Cmd+A).

        Args:
            app_name: Optional app name

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Use keyboard shortcut
            import subprocess

            applescript = """
            tell application "System Events"
                keystroke "a" using command down
            end tell
            """

            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info("Selected all text")
                return True, None
            else:
                return False, result.stderr

        except Exception as e:
            return False, f"Error selecting all text: {str(e)}"

    def copy_selection(self) -> Tuple[bool, Optional[str]]:
        """
        Copy selected text to clipboard (Cmd+C).

        Returns:
            Tuple of (success, error_message)
        """
        try:
            import subprocess

            applescript = """
            tell application "System Events"
                keystroke "c" using command down
            end tell
            """

            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )

            time.sleep(0.2)  # Give clipboard time to update

            if result.returncode == 0:
                logger.info("Copied selection to clipboard")
                return True, None
            else:
                return False, result.stderr

        except Exception as e:
            return False, f"Error copying selection: {str(e)}"

    def cut_selection(self) -> Tuple[bool, Optional[str]]:
        """
        Cut selected text to clipboard (Cmd+X).

        Returns:
            Tuple of (success, error_message)
        """
        try:
            import subprocess

            applescript = """
            tell application "System Events"
                keystroke "x" using command down
            end tell
            """

            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )

            time.sleep(0.2)

            if result.returncode == 0:
                logger.info("Cut selection to clipboard")
                return True, None
            else:
                return False, result.stderr

        except Exception as e:
            return False, f"Error cutting selection: {str(e)}"

    def simulate_gesture(
        self,
        gesture_type: GestureType,
        center_x: int,
        center_y: int,
        magnitude: float = 100.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Simulate multi-finger gesture.

        Note: This uses scroll wheel events as a proxy for gestures.
        True multi-touch gestures require private APIs.

        Args:
            gesture_type: Type of gesture
            center_x: Center X coordinate
            center_y: Center Y coordinate
            magnitude: Gesture magnitude (pixel distance)

        Returns:
            Tuple of (success, error_message)
        """
        if not QUARTZ_AVAILABLE:
            return False, "Quartz framework not available"

        try:
            # Map gestures to scroll/zoom events
            if gesture_type == GestureType.PINCH_IN:
                # Zoom out - simulate Cmd + scroll down
                return self._simulate_zoom(center_x, center_y, -magnitude)

            elif gesture_type == GestureType.PINCH_OUT:
                # Zoom in - simulate Cmd + scroll up
                return self._simulate_zoom(center_x, center_y, magnitude)

            elif gesture_type == GestureType.ROTATE_LEFT:
                # Rotation gestures are difficult to simulate
                logger.warning("Rotate gestures not fully supported")
                return False, "Rotate gestures require custom implementation per app"

            elif gesture_type == GestureType.ROTATE_RIGHT:
                logger.warning("Rotate gestures not fully supported")
                return False, "Rotate gestures require custom implementation per app"

            elif gesture_type == GestureType.SWIPE_LEFT:
                return self._simulate_swipe(center_x, center_y, -magnitude, 0)

            elif gesture_type == GestureType.SWIPE_RIGHT:
                return self._simulate_swipe(center_x, center_y, magnitude, 0)

            elif gesture_type == GestureType.SWIPE_UP:
                return self._simulate_swipe(center_x, center_y, 0, -magnitude)

            elif gesture_type == GestureType.SWIPE_DOWN:
                return self._simulate_swipe(center_x, center_y, 0, magnitude)

            else:
                return False, f"Unknown gesture type: {gesture_type}"

        except Exception as e:
            error = f"Error simulating gesture: {str(e)}"
            logger.error(error)
            return False, error

    def _simulate_zoom(
        self,
        x: int,
        y: int,
        delta: float
    ) -> Tuple[bool, Optional[str]]:
        """Simulate zoom gesture using scroll events."""
        try:
            # Create scroll wheel event with magnification
            scroll_event = CGEventCreateScrollWheelEvent(
                None,
                kCGScrollEventUnitPixel,
                1,  # Number of wheels
                int(delta)
            )

            CGEventPost(kCGHIDEventTap, scroll_event)

            direction = "in" if delta > 0 else "out"
            logger.info(f"Simulated zoom {direction}")
            return True, None

        except Exception as e:
            return False, f"Error simulating zoom: {str(e)}"

    def _simulate_swipe(
        self,
        x: int,
        y: int,
        delta_x: float,
        delta_y: float
    ) -> Tuple[bool, Optional[str]]:
        """Simulate swipe gesture."""
        try:
            # Use horizontal/vertical scroll events
            if abs(delta_x) > abs(delta_y):
                # Horizontal swipe
                scroll_event = CGEventCreateScrollWheelEvent(
                    None,
                    kCGScrollEventUnitPixel,
                    2,  # Both horizontal and vertical
                    0,
                    int(delta_x)
                )
            else:
                # Vertical swipe
                scroll_event = CGEventCreateScrollWheelEvent(
                    None,
                    kCGScrollEventUnitPixel,
                    1,
                    int(delta_y)
                )

            CGEventPost(kCGHIDEventTap, scroll_event)

            logger.info(f"Simulated swipe: dx={delta_x}, dy={delta_y}")
            return True, None

        except Exception as e:
            return False, f"Error simulating swipe: {str(e)}"

    def smooth_scroll(
        self,
        x: int,
        y: int,
        delta_x: int,
        delta_y: int,
        steps: int = 10,
        duration: float = 0.5
    ) -> Tuple[bool, Optional[str]]:
        """
        Perform smooth scrolling with easing.

        Args:
            x: X coordinate
            y: Y coordinate
            delta_x: Total horizontal scroll distance
            delta_y: Total vertical scroll distance
            steps: Number of scroll steps
            duration: Total duration in seconds

        Returns:
            Tuple of (success, error_message)
        """
        if not QUARTZ_AVAILABLE:
            return False, "Quartz framework not available"

        try:
            step_delay = duration / steps
            step_x = delta_x / steps
            step_y = delta_y / steps

            for i in range(steps):
                scroll_event = CGEventCreateScrollWheelEvent(
                    None,
                    kCGScrollEventUnitPixel,
                    2,  # Both axes
                    int(step_y),
                    int(step_x)
                )

                CGEventPost(kCGHIDEventTap, scroll_event)
                time.sleep(step_delay)

            logger.info(f"Smooth scrolled: dx={delta_x}, dy={delta_y}")
            return True, None

        except Exception as e:
            error = f"Error performing smooth scroll: {str(e)}"
            logger.error(error)
            return False, error


# Convenience functions

def check_advanced_interactions_available() -> bool:
    """Check if advanced interactions are available."""
    return QUARTZ_AVAILABLE


def right_click_at(x: int, y: int) -> Tuple[bool, Optional[str]]:
    """Right-click at coordinates (convenience function)."""
    interactions = AdvancedInteractions()
    return interactions.right_click(x, y)


def select_all_and_copy() -> Tuple[bool, Optional[str]]:
    """Select all text and copy to clipboard (convenience function)."""
    interactions = AdvancedInteractions()

    # Select all
    success, error = interactions.select_all_text()
    if not success:
        return False, error

    time.sleep(0.1)

    # Copy
    return interactions.copy_selection()
