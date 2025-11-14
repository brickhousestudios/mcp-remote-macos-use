"""
macOS Accessibility API Client for native UI automation.

This module provides native macOS UI control using the Accessibility API,
enabling semantic UI interactions (find elements by name/role) instead of
pixel-based coordinates.

Requires: pyobjc-framework-ApplicationServices, pyobjc-framework-Cocoa
"""

import logging
import time
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

try:
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        AXUIElementCopyAttributeNames,
        AXUIElementGetAttributeValueCount,
        AXUIElementPerformAction,
        AXUIElementCopyActionNames,
        kAXErrorSuccess,
        kAXErrorInvalidUIElement,
        kAXErrorAttributeUnsupported,
        kAXErrorActionUnsupported,
        kAXErrorNotificationUnsupported,
        kAXErrorNotImplemented,
        kAXTrustedCheckOptionPrompt,
    )
    from Cocoa import (
        NSWorkspace,
        NSRunningApplication,
    )
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
    )
    ACCESSIBILITY_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_AVAILABLE = False

# Configure logging
logger = logging.getLogger('accessibility_client')
logger.setLevel(logging.DEBUG)


class ElementRole(Enum):
    """Common UI element roles."""
    BUTTON = "AXButton"
    TEXT_FIELD = "AXTextField"
    STATIC_TEXT = "AXStaticText"
    WINDOW = "AXWindow"
    APPLICATION = "AXApplication"
    MENU = "AXMenu"
    MENU_ITEM = "AXMenuItem"
    MENU_BAR = "AXMenuBar"
    CHECKBOX = "AXCheckBox"
    RADIO_BUTTON = "AXRadioButton"
    SCROLL_AREA = "AXScrollArea"
    TAB_GROUP = "AXTabGroup"
    TABLE = "AXTable"
    ROW = "AXRow"
    CELL = "AXCell"
    LINK = "AXLink"
    IMAGE = "AXImage"
    GROUP = "AXGroup"


class AccessibilityClient:
    """
    Native macOS Accessibility API client for semantic UI automation.

    Provides high-level UI control without requiring coordinates:
    - Find elements by name, role, or properties
    - Perform semantic actions (click button by name)
    - Query UI hierarchy and properties
    - Much faster than VNC for local control
    """

    def __init__(self):
        """Initialize the Accessibility client."""
        if not ACCESSIBILITY_AVAILABLE:
            raise ImportError(
                "Accessibility API not available. Install with: "
                "pip install pyobjc-framework-ApplicationServices pyobjc-framework-Cocoa"
            )

        self.system_wide = AXUIElementCreateSystemWide()
        logger.info("Initialized macOS Accessibility API client")

    @staticmethod
    def check_accessibility_permissions() -> bool:
        """
        Check if the application has Accessibility permissions.

        Returns:
            bool: True if permissions are granted
        """
        # This will prompt the user if permissions are not granted
        from ApplicationServices import AXIsProcessTrusted, AXIsProcessTrustedWithOptions
        from Cocoa import NSMutableDictionary

        # Check without prompt first
        if AXIsProcessTrusted():
            return True

        logger.warning("Accessibility permissions not granted")

        # Prompt for permissions
        options = NSMutableDictionary.dictionary()
        options[kAXTrustedCheckOptionPrompt] = True
        return AXIsProcessTrustedWithOptions(options)

    def _get_attribute_value(self, element, attribute: str) -> Optional[Any]:
        """
        Get an attribute value from a UI element.

        Args:
            element: AXUIElement
            attribute: Attribute name (e.g., "AXTitle", "AXRole")

        Returns:
            Attribute value or None if not available
        """
        try:
            error, value = AXUIElementCopyAttributeValue(element, attribute, None)
            if error == kAXErrorSuccess:
                return value
            return None
        except Exception as e:
            logger.debug(f"Error getting attribute {attribute}: {e}")
            return None

    def _perform_action(self, element, action: str) -> bool:
        """
        Perform an action on a UI element.

        Args:
            element: AXUIElement
            action: Action name (e.g., "AXPress", "AXShowMenu")

        Returns:
            bool: True if action succeeded
        """
        try:
            error = AXUIElementPerformAction(element, action)
            return error == kAXErrorSuccess
        except Exception as e:
            logger.error(f"Error performing action {action}: {e}")
            return False

    def get_focused_application(self) -> Optional[Tuple[str, int]]:
        """
        Get the currently focused application.

        Returns:
            Tuple of (app_name, pid) or None
        """
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()

        if active_app:
            return (
                active_app.localizedName(),
                active_app.processIdentifier()
            )
        return None

    def get_application_by_name(self, app_name: str) -> Optional[int]:
        """
        Find an application by name and return its PID.

        Args:
            app_name: Application name (e.g., "Safari", "TextEdit")

        Returns:
            Process ID or None if not found
        """
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()

        for app in running_apps:
            if app.localizedName().lower() == app_name.lower():
                return app.processIdentifier()

        return None

    def launch_application(self, app_name: str) -> bool:
        """
        Launch an application by name.

        Args:
            app_name: Application name or bundle identifier

        Returns:
            bool: True if launched successfully
        """
        workspace = NSWorkspace.sharedWorkspace()

        # Try launching by name
        success = workspace.launchApplication_(app_name)

        if success:
            logger.info(f"Launched application: {app_name}")
            return True

        logger.error(f"Failed to launch application: {app_name}")
        return False

    def activate_application(self, pid: int) -> bool:
        """
        Activate (bring to front) an application by PID.

        Args:
            pid: Process ID

        Returns:
            bool: True if activated successfully
        """
        app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
        if app:
            return app.activateWithOptions_(1 << 1)  # NSApplicationActivateIgnoringOtherApps
        return False

    def find_elements(
        self,
        role: Optional[str] = None,
        title: Optional[str] = None,
        pid: Optional[int] = None,
        recursive: bool = True,
        max_depth: int = 10
    ) -> List[Any]:
        """
        Find UI elements matching the criteria.

        Args:
            role: Element role (e.g., "AXButton", "AXTextField")
            title: Element title/name
            pid: Limit search to specific application
            recursive: Search recursively through UI hierarchy
            max_depth: Maximum recursion depth

        Returns:
            List of matching AXUIElements
        """
        results = []

        # Start from application or system-wide
        if pid:
            root = AXUIElementCreateApplication(pid)
        else:
            root = self.system_wide

        # Recursive search
        def search(element, depth=0):
            if depth > max_depth:
                return

            # Check if this element matches
            element_role = self._get_attribute_value(element, "AXRole")
            element_title = self._get_attribute_value(element, "AXTitle")

            matches = True
            if role and element_role != role:
                matches = False
            if title and (not element_title or title.lower() not in str(element_title).lower()):
                matches = False

            if matches:
                results.append(element)

            # Recurse into children
            if recursive:
                children = self._get_attribute_value(element, "AXChildren")
                if children:
                    for child in children:
                        search(child, depth + 1)

        search(root)
        return results

    def click_element(self, element) -> bool:
        """
        Click a UI element.

        Args:
            element: AXUIElement to click

        Returns:
            bool: True if click succeeded
        """
        return self._perform_action(element, "AXPress")

    def get_element_text(self, element) -> Optional[str]:
        """
        Get the text value of a UI element.

        Args:
            element: AXUIElement

        Returns:
            Text value or None
        """
        # Try different text attributes
        text = self._get_attribute_value(element, "AXValue")
        if text:
            return str(text)

        text = self._get_attribute_value(element, "AXTitle")
        if text:
            return str(text)

        return None

    def set_element_text(self, element, text: str) -> bool:
        """
        Set the text value of a UI element (e.g., text field).

        Args:
            element: AXUIElement
            text: Text to set

        Returns:
            bool: True if successful
        """
        try:
            from ApplicationServices import AXUIElementSetAttributeValue
            error = AXUIElementSetAttributeValue(element, "AXValue", text)
            return error == kAXErrorSuccess
        except Exception as e:
            logger.error(f"Error setting element text: {e}")
            return False

    def get_element_info(self, element) -> Dict[str, Any]:
        """
        Get comprehensive information about a UI element.

        Args:
            element: AXUIElement

        Returns:
            Dictionary with element properties
        """
        info = {}

        # Common attributes to check
        attributes = [
            "AXRole", "AXRoleDescription", "AXTitle", "AXValue",
            "AXDescription", "AXHelp", "AXEnabled", "AXFocused",
            "AXPosition", "AXSize", "AXFrame"
        ]

        for attr in attributes:
            value = self._get_attribute_value(element, attr)
            if value is not None:
                info[attr] = value

        # Get available actions
        try:
            error, actions = AXUIElementCopyActionNames(element, None)
            if error == kAXErrorSuccess and actions:
                info["AXActions"] = list(actions)
        except:
            pass

        return info

    def click_by_name(self, name: str, role: Optional[str] = None, pid: Optional[int] = None) -> bool:
        """
        Click a UI element by its name/title.

        Args:
            name: Element name/title to find
            role: Optional role filter (e.g., "AXButton")
            pid: Optional application PID

        Returns:
            bool: True if element was found and clicked
        """
        elements = self.find_elements(role=role, title=name, pid=pid)

        if not elements:
            logger.warning(f"No element found with name: {name}")
            return False

        # Click the first match
        return self.click_element(elements[0])

    def type_text(self, text: str, pid: Optional[int] = None) -> bool:
        """
        Type text into the currently focused text field.

        Args:
            text: Text to type
            pid: Optional application PID

        Returns:
            bool: True if successful
        """
        # Find focused text field
        if pid:
            root = AXUIElementCreateApplication(pid)
        else:
            root = self.system_wide

        focused = self._get_attribute_value(root, "AXFocusedUIElement")
        if not focused:
            logger.error("No focused element found")
            return False

        # Check if it's a text field
        role = self._get_attribute_value(focused, "AXRole")
        if role not in ["AXTextField", "AXTextArea"]:
            logger.warning(f"Focused element is not a text field: {role}")

        # Set the text
        return self.set_element_text(focused, text)


def check_accessibility_available() -> bool:
    """
    Check if Accessibility API is available on this system.

    Returns:
        bool: True if available
    """
    return ACCESSIBILITY_AVAILABLE


def check_accessibility_enabled() -> bool:
    """
    Check if Accessibility permissions are enabled for this process.

    Returns:
        bool: True if enabled
    """
    if not ACCESSIBILITY_AVAILABLE:
        return False

    return AccessibilityClient.check_accessibility_permissions()
