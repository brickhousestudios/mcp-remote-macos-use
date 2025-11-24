"""
Element extraction and bounding box detection for macOS UI.

Extract complete UI hierarchies with properties, positions, and bounding boxes.
Enables screen scraping, automated form detection, and visual element mapping.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
import json

try:
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        AXUIElementCopyAttributeNames,
        kAXErrorSuccess,
    )
    from Cocoa import NSWorkspace
    ACCESSIBILITY_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_AVAILABLE = False

# Configure logging
logger = logging.getLogger('element_extractor')
logger.setLevel(logging.DEBUG)


class ElementExtractor:
    """
    Extract UI elements with full hierarchy, properties, and bounding boxes.

    Features:
    - Complete UI tree extraction
    - Element properties (role, title, value, etc.)
    - Bounding boxes (position, size)
    - Hierarchy and relationships
    - Filtering by type, properties
    - Export to JSON
    """

    def __init__(self):
        """Initialize element extractor."""
        if not ACCESSIBILITY_AVAILABLE:
            raise ImportError("Accessibility API not available")

        self.system_wide = AXUIElementCreateSystemWide()
        logger.info("Initialized element extractor")

    def _get_attribute_value(self, element, attribute: str) -> Optional[Any]:
        """Get attribute value from element."""
        try:
            error, value = AXUIElementCopyAttributeValue(element, attribute, None)
            if error == kAXErrorSuccess:
                return value
            return None
        except Exception as e:
            logger.debug(f"Error getting attribute {attribute}: {e}")
            return None

    def _get_all_attributes(self, element) -> Dict[str, Any]:
        """
        Get all available attributes from an element.

        Returns:
            Dictionary of all attributes
        """
        attributes = {}

        try:
            error, attr_names = AXUIElementCopyAttributeNames(element, None)
            if error != kAXErrorSuccess or not attr_names:
                return attributes

            for attr_name in attr_names:
                value = self._get_attribute_value(element, attr_name)
                if value is not None:
                    # Convert to serializable format
                    attributes[str(attr_name)] = self._serialize_value(value)

        except Exception as e:
            logger.debug(f"Error getting attributes: {e}")

        return attributes

    def _serialize_value(self, value: Any) -> Any:
        """
        Convert value to JSON-serializable format.

        Args:
            value: Value to serialize

        Returns:
            Serializable value
        """
        # Handle common types
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif hasattr(value, '__dict__'):
            # Try to extract useful info from objects
            if hasattr(value, 'x') and hasattr(value, 'y'):
                # CGPoint-like object
                return {"x": float(value.x), "y": float(value.y)}
            elif hasattr(value, 'width') and hasattr(value, 'height'):
                # CGSize-like object
                return {"width": float(value.width), "height": float(value.height)}
            elif hasattr(value, 'origin') and hasattr(value, 'size'):
                # CGRect-like object
                return {
                    "x": float(value.origin.x),
                    "y": float(value.origin.y),
                    "width": float(value.size.width),
                    "height": float(value.size.height)
                }

        # Default: convert to string
        return str(value)

    def extract_element_info(self, element) -> Dict[str, Any]:
        """
        Extract comprehensive information about a single element.

        Args:
            element: AXUIElement

        Returns:
            Dictionary with element info including bounding box
        """
        info = {}

        # Get essential attributes
        essential = [
            "AXRole",
            "AXRoleDescription",
            "AXTitle",
            "AXValue",
            "AXDescription",
            "AXHelp",
            "AXEnabled",
            "AXFocused",
            "AXPosition",
            "AXSize",
            "AXFrame",
            "AXIdentifier",
            "AXPlaceholderValue",
        ]

        for attr in essential:
            value = self._get_attribute_value(element, attr)
            if value is not None:
                info[attr] = self._serialize_value(value)

        # Calculate bounding box if position and size available
        if "AXPosition" in info and "AXSize" in info:
            pos = info["AXPosition"]
            size = info["AXSize"]
            if isinstance(pos, dict) and isinstance(size, dict):
                info["BoundingBox"] = {
                    "x": pos.get("x", 0),
                    "y": pos.get("y", 0),
                    "width": size.get("width", 0),
                    "height": size.get("height", 0)
                }

        return info

    def extract_element_tree(
        self,
        element=None,
        max_depth: int = 10,
        current_depth: int = 0,
        include_properties: bool = True,
        role_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract complete UI element tree with hierarchy.

        Args:
            element: Root element (default: system-wide)
            max_depth: Maximum depth to traverse
            current_depth: Current depth (internal)
            include_properties: Include all properties (vs just basic info)
            role_filter: Only include elements with these roles

        Returns:
            Nested dictionary representing UI tree
        """
        if element is None:
            element = self.system_wide

        if current_depth >= max_depth:
            return {}

        # Extract element info
        if include_properties:
            node = self.extract_element_info(element)
        else:
            # Just basic info
            node = {
                "AXRole": self._serialize_value(self._get_attribute_value(element, "AXRole")),
                "AXTitle": self._serialize_value(self._get_attribute_value(element, "AXTitle")),
            }

        # Filter by role if specified
        if role_filter and node.get("AXRole") not in role_filter:
            return None

        # Get children
        children = self._get_attribute_value(element, "AXChildren")
        if children:
            node["children"] = []
            for child in children:
                child_node = self.extract_element_tree(
                    child,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    include_properties=include_properties,
                    role_filter=role_filter
                )
                if child_node:  # Only add if not filtered out
                    node["children"].append(child_node)

            # Remove empty children list
            if not node["children"]:
                del node["children"]

        return node

    def extract_all_elements_flat(
        self,
        element=None,
        max_depth: int = 10,
        role_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all elements as a flat list (not nested).

        Args:
            element: Root element (default: system-wide)
            max_depth: Maximum depth to traverse
            role_filter: Only include elements with these roles

        Returns:
            List of element dictionaries
        """
        elements = []

        def traverse(elem, depth=0):
            if depth >= max_depth:
                return

            # Extract element info
            info = self.extract_element_info(elem)

            # Filter by role
            if role_filter is None or info.get("AXRole") in role_filter:
                # Add depth info
                info["depth"] = depth
                elements.append(info)

            # Traverse children
            children = self._get_attribute_value(elem, "AXChildren")
            if children:
                for child in children:
                    traverse(child, depth + 1)

        traverse(element or self.system_wide)
        return elements

    def extract_by_role(
        self,
        role: str,
        pid: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all elements of a specific role.

        Args:
            role: Element role (e.g., "AXButton", "AXTextField")
            pid: Limit to specific application PID

        Returns:
            List of matching elements
        """
        root = AXUIElementCreateApplication(pid) if pid else self.system_wide
        return self.extract_all_elements_flat(root, role_filter=[role])

    def extract_screen_structure(
        self,
        app_name: Optional[str] = None,
        include_all_properties: bool = False
    ) -> Dict[str, Any]:
        """
        Extract complete screen structure as JSON.

        Args:
            app_name: Limit to specific application
            include_all_properties: Include all properties (verbose)

        Returns:
            Screen structure dictionary
        """
        if app_name:
            # Get app PID
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()

            pid = None
            for app in running_apps:
                if app.localizedName().lower() == app_name.lower():
                    pid = app.processIdentifier()
                    break

            if not pid:
                return {"error": f"Application not found: {app_name}"}

            root = AXUIElementCreateApplication(pid)
        else:
            root = self.system_wide

        # Extract tree
        tree = self.extract_element_tree(
            root,
            max_depth=15,
            include_properties=include_all_properties
        )

        # Add metadata
        result = {
            "app_name": app_name,
            "element_tree": tree,
            "extraction_type": "complete" if include_all_properties else "basic"
        }

        return result

    def extract_form_fields(
        self,
        pid: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all form fields (text fields, checkboxes, radio buttons).

        Args:
            pid: Limit to specific application PID

        Returns:
            List of form fields
        """
        form_roles = [
            "AXTextField",
            "AXTextArea",
            "AXCheckBox",
            "AXRadioButton",
            "AXComboBox",
            "AXPopUpButton",
            "AXSlider",
        ]

        root = AXUIElementCreateApplication(pid) if pid else self.system_wide
        return self.extract_all_elements_flat(root, role_filter=form_roles)

    def extract_clickable_elements(
        self,
        pid: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all clickable elements (buttons, links, menu items).

        Args:
            pid: Limit to specific application PID

        Returns:
            List of clickable elements
        """
        clickable_roles = [
            "AXButton",
            "AXLink",
            "AXMenuItem",
            "AXCheckBox",
            "AXRadioButton",
        ]

        root = AXUIElementCreateApplication(pid) if pid else self.system_wide
        return self.extract_all_elements_flat(root, role_filter=clickable_roles)

    def extract_text_elements(
        self,
        pid: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all text elements (labels, static text).

        Args:
            pid: Limit to specific application PID

        Returns:
            List of text elements
        """
        text_roles = [
            "AXStaticText",
            "AXTextField",
            "AXTextArea",
        ]

        root = AXUIElementCreateApplication(pid) if pid else self.system_wide
        elements = self.extract_all_elements_flat(root, role_filter=text_roles)

        # Filter to only include elements with actual text
        return [e for e in elements if e.get("AXValue") or e.get("AXTitle")]

    def get_bounding_boxes(
        self,
        pid: Optional[int] = None,
        role_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get bounding boxes for all elements.

        Args:
            pid: Limit to specific application PID
            role_filter: Only include specific roles

        Returns:
            List of elements with bounding box info
        """
        root = AXUIElementCreateApplication(pid) if pid else self.system_wide
        elements = self.extract_all_elements_flat(root, role_filter=role_filter)

        # Filter to only include elements with bounding boxes
        return [e for e in elements if "BoundingBox" in e]


def extract_screen_to_json(
    app_name: Optional[str] = None,
    include_all: bool = False
) -> str:
    """
    Extract screen structure and return as JSON string.

    Args:
        app_name: Limit to specific application
        include_all: Include all properties

    Returns:
        JSON string
    """
    if not ACCESSIBILITY_AVAILABLE:
        return json.dumps({"error": "Accessibility API not available"})

    try:
        extractor = ElementExtractor()
        structure = extractor.extract_screen_structure(app_name, include_all)
        return json.dumps(structure, indent=2)
    except Exception as e:
        logger.error(f"Error extracting screen: {e}")
        return json.dumps({"error": str(e)})


def get_all_bounding_boxes(app_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get bounding boxes for all UI elements.

    Args:
        app_name: Limit to specific application

    Returns:
        List of bounding boxes
    """
    if not ACCESSIBILITY_AVAILABLE:
        return []

    try:
        extractor = ElementExtractor()

        # Get app PID if specified
        pid = None
        if app_name:
            from Cocoa import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()

            for app in running_apps:
                if app.localizedName().lower() == app_name.lower():
                    pid = app.processIdentifier()
                    break

        return extractor.get_bounding_boxes(pid)
    except Exception as e:
        logger.error(f"Error getting bounding boxes: {e}")
        return []
