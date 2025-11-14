"""
Semantic action handlers for native macOS UI control.

These handlers use the Accessibility API and MLX vision for semantic
UI interactions (find elements by name, role, visual description)
instead of pixel coordinates.
"""

import logging
from typing import Any, Dict, List
import json

import mcp.types as types
from control_router import create_router
from accessibility_client import check_accessibility_available

# Configure logging
logger = logging.getLogger('semantic_handlers')
logger.setLevel(logging.DEBUG)


def handle_macos_find_element(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Find UI elements by name, role, or properties.

    Args:
        arguments: Dict with:
            - name: Element name/title (optional)
            - role: Element role like "AXButton", "AXTextField" (optional)
            - app_name: Limit search to specific application (optional)

    Returns:
        List of found elements with their properties
    """
    name = arguments.get("name")
    role = arguments.get("role")
    app_name = arguments.get("app_name")

    if not check_accessibility_available():
        return [types.TextContent(
            type="text",
            text="Accessibility API not available. This feature requires macOS with PyObjC installed."
        )]

    try:
        router = create_router()

        # Get PID if app_name specified
        pid = None
        if app_name and router.accessibility_client:
            pid = router.accessibility_client.get_application_by_name(app_name)
            if not pid:
                return [types.TextContent(
                    type="text",
                    text=f"Application not found: {app_name}"
                )]

        # Find elements
        elements = router.find_elements(role=role, title=name)

        if not elements:
            return [types.TextContent(
                type="text",
                text=f"No elements found matching: name={name}, role={role}"
            )]

        # Get info for each element
        results = []
        for i, element in enumerate(elements[:10]):  # Limit to 10 results
            info = router.accessibility_client.get_element_info(element)
            results.append({
                "index": i,
                "role": info.get("AXRole"),
                "title": info.get("AXTitle"),
                "description": info.get("AXDescription"),
                "position": str(info.get("AXPosition")),
                "size": str(info.get("AXSize")),
                "enabled": info.get("AXEnabled"),
            })

        return [types.TextContent(
            type="text",
            text=f"Found {len(elements)} element(s):\n\n" + json.dumps(results, indent=2)
        )]

    except Exception as e:
        logger.error(f"Error finding elements: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_macos_click_element(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Click a UI element by its name/title (semantic click).

    Args:
        arguments: Dict with:
            - name: Element name/title (required)
            - role: Element role filter like "AXButton" (optional)
            - app_name: Limit to specific application (optional)

    Returns:
        Success/failure message
    """
    name = arguments.get("name")
    role = arguments.get("role")
    app_name = arguments.get("app_name")

    if not name:
        raise ValueError("Element name is required")

    if not check_accessibility_available():
        return [types.TextContent(
            type="text",
            text="Accessibility API not available. Use remote_macos_mouse_click for coordinate-based clicking."
        )]

    try:
        router = create_router()

        # Get PID if app_name specified
        pid = None
        if app_name and router.accessibility_client:
            pid = router.accessibility_client.get_application_by_name(app_name)
            if not pid:
                return [types.TextContent(
                    type="text",
                    text=f"Application not found: {app_name}"
                )]

        # Click element
        success = router.click_element_by_name(name, role=role)

        if success:
            return [types.TextContent(
                type="text",
                text=f"Successfully clicked element: {name}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to click element: {name}. Element may not exist or may not be clickable."
            )]

    except Exception as e:
        logger.error(f"Error clicking element: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_macos_type_text_semantic(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Type text into the currently focused text field.

    Args:
        arguments: Dict with:
            - text: Text to type (required)

    Returns:
        Success/failure message
    """
    text = arguments.get("text")

    if not text:
        raise ValueError("Text is required")

    if not check_accessibility_available():
        return [types.TextContent(
            type="text",
            text="Accessibility API not available. Use remote_macos_send_keys instead."
        )]

    try:
        router = create_router()
        success = router.type_text(text)

        if success:
            return [types.TextContent(
                type="text",
                text=f"Successfully typed text: '{text}'"
            )]
        else:
            return [types.TextContent(
                type="text",
                text="Failed to type text. Ensure a text field is focused."
            )]

    except Exception as e:
        logger.error(f"Error typing text: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_macos_get_focused_app(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Get information about the currently focused application.

    Returns:
        Application name and PID
    """
    if not check_accessibility_available():
        return [types.TextContent(
            type="text",
            text="Accessibility API not available."
        )]

    try:
        router = create_router()

        if not router.accessibility_client:
            return [types.TextContent(
                type="text",
                text="Accessibility client not available"
            )]

        app_info = router.accessibility_client.get_focused_application()

        if app_info:
            name, pid = app_info
            return [types.TextContent(
                type="text",
                text=f"Focused application:\n  Name: {name}\n  PID: {pid}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text="No focused application found"
            )]

    except Exception as e:
        logger.error(f"Error getting focused app: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_macos_launch_app_native(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Launch an application using native macOS APIs.

    Args:
        arguments: Dict with:
            - app_name: Application name or bundle ID (required)

    Returns:
        Success/failure message
    """
    app_name = arguments.get("app_name")

    if not app_name:
        raise ValueError("app_name is required")

    if not check_accessibility_available():
        return [types.TextContent(
            type="text",
            text="Accessibility API not available. Use remote_macos_open_application instead."
        )]

    try:
        router = create_router()
        success = router.launch_application(app_name)

        if success:
            return [types.TextContent(
                type="text",
                text=f"Successfully launched application: {app_name}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to launch application: {app_name}"
            )]

    except Exception as e:
        logger.error(f"Error launching app: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_macos_get_capabilities(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Get the capabilities of the current control method.

    Returns:
        Dictionary of available capabilities
    """
    try:
        router = create_router()
        capabilities = router.get_capabilities()

        cap_list = []
        for key, value in capabilities.items():
            status = "✓" if value else "✗"
            cap_list.append(f"  {status} {key}")

        return [types.TextContent(
            type="text",
            text=f"Control capabilities:\n" + "\n".join(cap_list) + "\n\n" +
                 f"Control method: {router.control_method.value}"
        )]

    except Exception as e:
        logger.error(f"Error getting capabilities: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
