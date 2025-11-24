"""
Advanced action handlers for AppleScript, clipboard, system controls, and batch operations.
"""

import logging
from typing import Any, Dict, List
import json
import time

import mcp.types as types

# Import our advanced modules
try:
    from applescript_client import AppleScriptClient, check_applescript_available
    APPLESCRIPT_AVAILABLE = True
except ImportError:
    APPLESCRIPT_AVAILABLE = False

try:
    from system_controls import (
        ClipboardManager,
        SystemController,
        check_cocoa_available
    )
    SYSTEM_CONTROLS_AVAILABLE = check_cocoa_available()
except ImportError:
    SYSTEM_CONTROLS_AVAILABLE = False

# Import element extraction
try:
    from element_extractor import ElementExtractor
    ELEMENT_EXTRACTION_AVAILABLE = True
except ImportError:
    ELEMENT_EXTRACTION_AVAILABLE = False

# Import smart waiting
try:
    from smart_waiting import SmartWaiter, WaitResult
    SMART_WAITING_AVAILABLE = True
except ImportError:
    SMART_WAITING_AVAILABLE = False

# Import visual debugging
try:
    from visual_debugging import VisualDebugger
    VISUAL_DEBUGGING_AVAILABLE = True
except ImportError:
    VISUAL_DEBUGGING_AVAILABLE = False

# Import window manager
try:
    from window_manager import WindowManager, check_window_manager_available
    WINDOW_MANAGER_AVAILABLE = check_window_manager_available()
except ImportError:
    WINDOW_MANAGER_AVAILABLE = False

# Import advanced interactions
try:
    from advanced_interactions import AdvancedInteractions, GestureType, check_advanced_interactions_available
    ADVANCED_INTERACTIONS_AVAILABLE = check_advanced_interactions_available()
except ImportError:
    ADVANCED_INTERACTIONS_AVAILABLE = False

# Import for batch operations
from action_handlers import (
    handle_remote_macos_mouse_click,
    handle_remote_macos_send_keys,
    handle_remote_macos_mouse_move,
)

try:
    from semantic_handlers import (
        handle_macos_click_element,
        handle_macos_type_text_semantic,
    )
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

# Configure logging
logger = logging.getLogger('advanced_handlers')
logger.setLevel(logging.DEBUG)


# AppleScript Handlers

def handle_execute_applescript(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Execute an AppleScript.

    Args:
        arguments: Dict with:
            - script: AppleScript code to execute
            - timeout: Optional timeout in seconds (default: 30)

    Returns:
        Execution result
    """
    if not APPLESCRIPT_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="AppleScript not available. Requires macOS."
        )]

    script = arguments.get("script")
    timeout = arguments.get("timeout", 30)

    if not script:
        raise ValueError("script is required")

    try:
        client = AppleScriptClient()
        success, output, error = client.execute_script(script, timeout)

        if success:
            return [types.TextContent(
                type="text",
                text=f"Script executed successfully.\n\nOutput:\n{output or '(no output)'}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Script execution failed.\n\nError:\n{error}"
            )]

    except Exception as e:
        logger.error(f"Error executing AppleScript: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_applescript_tell_app(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Send a command to a specific application via AppleScript.

    Args:
        arguments: Dict with:
            - app_name: Application name
            - command: AppleScript command(s)
            - timeout: Optional timeout (default: 30)

    Returns:
        Execution result
    """
    if not APPLESCRIPT_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="AppleScript not available. Requires macOS."
        )]

    app_name = arguments.get("app_name")
    command = arguments.get("command")
    timeout = arguments.get("timeout", 30)

    if not app_name or not command:
        raise ValueError("app_name and command are required")

    try:
        client = AppleScriptClient()
        success, output, error = client.tell_app(app_name, command, timeout)

        if success:
            return [types.TextContent(
                type="text",
                text=f"Command sent to {app_name} successfully.\n\nOutput:\n{output or '(no output)'}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Command failed.\n\nError:\n{error}"
            )]

    except Exception as e:
        logger.error(f"Error sending command: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Clipboard Handlers

def handle_read_clipboard(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Read text from clipboard.

    Returns:
        Clipboard contents
    """
    if not SYSTEM_CONTROLS_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Clipboard operations not available. Requires macOS with PyObjC."
        )]

    try:
        manager = ClipboardManager()
        text = manager.read_text()

        if text is not None:
            return [types.TextContent(
                type="text",
                text=f"Clipboard contents:\n\n{text}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text="Clipboard is empty or contains non-text data"
            )]

    except Exception as e:
        logger.error(f"Error reading clipboard: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_write_clipboard(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Write text to clipboard.

    Args:
        arguments: Dict with:
            - text: Text to write to clipboard

    Returns:
        Success message
    """
    if not SYSTEM_CONTROLS_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Clipboard operations not available. Requires macOS with PyObjC."
        )]

    text = arguments.get("text")

    if text is None:
        raise ValueError("text is required")

    try:
        manager = ClipboardManager()
        success = manager.write_text(str(text))

        if success:
            return [types.TextContent(
                type="text",
                text=f"Successfully wrote to clipboard:\n{text}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text="Failed to write to clipboard"
            )]

    except Exception as e:
        logger.error(f"Error writing clipboard: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# System Control Handlers

def handle_set_volume(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Set system volume.

    Args:
        arguments: Dict with:
            - level: Volume level (0-100)

    Returns:
        Success message
    """
    level = arguments.get("level")

    if level is None:
        raise ValueError("level is required")

    try:
        controller = SystemController()
        success, error = controller.set_volume(int(level))

        if success:
            return [types.TextContent(
                type="text",
                text=f"Volume set to {level}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to set volume: {error}"
            )]

    except Exception as e:
        logger.error(f"Error setting volume: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_get_volume(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Get current system volume."""
    try:
        controller = SystemController()
        success, volume, error = controller.get_volume()

        if success:
            return [types.TextContent(
                type="text",
                text=f"Current volume: {volume}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to get volume: {error}"
            )]

    except Exception as e:
        logger.error(f"Error getting volume: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_system_action(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Perform a system action (lock, sleep, etc.).

    Args:
        arguments: Dict with:
            - action: Action to perform (lock/sleep/logout/mute/unmute)

    Returns:
        Success message
    """
    action = arguments.get("action")

    if not action:
        raise ValueError("action is required")

    try:
        controller = SystemController()

        if action == "lock":
            success, error = controller.lock_screen()
            msg = "Screen locked"
        elif action == "sleep":
            success, error = controller.sleep()
            msg = "Computer sleep initiated"
        elif action == "logout":
            success, error = controller.logout()
            msg = "User logout initiated"
        elif action == "mute":
            success, error = controller.mute()
            msg = "Volume muted"
        elif action == "unmute":
            success, error = controller.unmute()
            msg = "Volume unmuted"
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown action: {action}. Valid: lock, sleep, logout, mute, unmute"
            )]

        if success:
            return [types.TextContent(type="text", text=msg)]
        else:
            return [types.TextContent(type="text", text=f"Failed: {error}")]

    except Exception as e:
        logger.error(f"Error performing system action: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Batch Operations Handler

def handle_batch_operations(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Execute multiple operations in sequence.

    Args:
        arguments: Dict with:
            - operations: List of operation dicts, each with:
                - tool: Tool name
                - arguments: Tool arguments
                - delay_ms: Optional delay after this operation (default: 100)

    Returns:
        Results from all operations
    """
    operations = arguments.get("operations", [])

    if not operations:
        raise ValueError("operations list is required")

    results = []
    total_start = time.time()

    for i, op in enumerate(operations):
        tool = op.get("tool")
        op_args = op.get("arguments", {})
        delay_ms = op.get("delay_ms", 100)

        if not tool:
            results.append(f"Operation {i+1}: ERROR - no tool specified")
            continue

        op_start = time.time()

        try:
            # Route to appropriate handler
            if tool == "remote_macos_mouse_click":
                result = handle_remote_macos_mouse_click(op_args)
            elif tool == "remote_macos_send_keys":
                result = handle_remote_macos_send_keys(op_args)
            elif tool == "remote_macos_mouse_move":
                result = handle_remote_macos_mouse_move(op_args)
            elif tool == "macos_click_element" and SEMANTIC_AVAILABLE:
                result = handle_macos_click_element(op_args)
            elif tool == "macos_type_text_native" and SEMANTIC_AVAILABLE:
                result = handle_macos_type_text_semantic(op_args)
            else:
                result = [types.TextContent(type="text", text=f"Unknown or unavailable tool: {tool}")]

            # Extract result text
            result_text = result[0].text if result and hasattr(result[0], 'text') else str(result)

            op_time = round((time.time() - op_start) * 1000, 2)
            results.append(f"Operation {i+1} ({tool}): OK ({op_time}ms)\n  {result_text[:100]}...")

            # Delay before next operation
            if delay_ms > 0 and i < len(operations) - 1:
                time.sleep(delay_ms / 1000.0)

        except Exception as e:
            logger.error(f"Error in batch operation {i+1}: {e}", exc_info=True)
            results.append(f"Operation {i+1} ({tool}): ERROR - {str(e)}")

    total_time = round((time.time() - total_start) * 1000, 2)

    summary = f"Batch Operations Complete\n"
    summary += f"Total: {len(operations)} operations in {total_time}ms\n"
    summary += f"Average: {round(total_time / len(operations), 2)}ms per operation\n\n"
    summary += "Results:\n" + "\n".join(results)

    return [types.TextContent(type="text", text=summary)]


# Element Extraction Handlers

def handle_extract_screen_structure(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Extract complete UI structure/tree from screen.

    Args:
        arguments: Dict with:
            - app_name: Optional app name to limit extraction
            - include_all_properties: Include all properties (default: False)
            - format: Output format "json" or "summary" (default: "json")

    Returns:
        Screen structure
    """
    if not ELEMENT_EXTRACTION_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Element extraction not available. Requires macOS with Accessibility API."
        )]

    app_name = arguments.get("app_name")
    include_all = arguments.get("include_all_properties", False)
    output_format = arguments.get("format", "json")

    try:
        extractor = ElementExtractor()
        structure = extractor.extract_screen_structure(app_name, include_all)

        if output_format == "json":
            return [types.TextContent(
                type="text",
                text=json.dumps(structure, indent=2)
            )]
        else:
            # Summary format
            def count_elements(node, count=0):
                count += 1
                if "children" in node:
                    for child in node["children"]:
                        count = count_elements(child, count)
                return count

            total = count_elements(structure.get("element_tree", {}))
            summary = f"Screen Structure for {app_name or 'all apps'}:\n"
            summary += f"Total elements: {total}\n"
            summary += f"Include all properties: {include_all}\n\n"
            summary += f"JSON output:\n{json.dumps(structure, indent=2)[:1000]}..."

            return [types.TextContent(type="text", text=summary)]

    except Exception as e:
        logger.error(f"Error extracting screen structure: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_extract_all_elements(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Extract all UI elements as a flat list.

    Args:
        arguments: Dict with:
            - app_name: Optional app name
            - role_filter: Optional list of roles to include
            - max_depth: Maximum depth to traverse (default: 10)

    Returns:
        List of all elements
    """
    if not ELEMENT_EXTRACTION_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Element extraction not available. Requires macOS with Accessibility API."
        )]

    app_name = arguments.get("app_name")
    role_filter = arguments.get("role_filter")
    max_depth = arguments.get("max_depth", 10)

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

            if not pid:
                return [types.TextContent(type="text", text=f"App not found: {app_name}")]

        from ApplicationServices import AXUIElementCreateApplication, AXUIElementCreateSystemWide
        root = AXUIElementCreateApplication(pid) if pid else AXUIElementCreateSystemWide()

        elements = extractor.extract_all_elements_flat(root, max_depth, role_filter)

        return [types.TextContent(
            type="text",
            text=f"Found {len(elements)} elements\n\n{json.dumps(elements[:50], indent=2)}"
        )]

    except Exception as e:
        logger.error(f"Error extracting elements: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_get_bounding_boxes(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Get bounding boxes for all UI elements.

    Args:
        arguments: Dict with:
            - app_name: Optional app name
            - role_filter: Optional list of roles

    Returns:
        List of elements with bounding boxes
    """
    if not ELEMENT_EXTRACTION_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Element extraction not available. Requires macOS with Accessibility API."
        )]

    app_name = arguments.get("app_name")
    role_filter = arguments.get("role_filter")

    try:
        extractor = ElementExtractor()

        # Get app PID
        pid = None
        if app_name:
            from Cocoa import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()

            for app in running_apps:
                if app.localizedName().lower() == app_name.lower():
                    pid = app.processIdentifier()
                    break

        boxes = extractor.get_bounding_boxes(pid, role_filter)

        return [types.TextContent(
            type="text",
            text=f"Found {len(boxes)} elements with bounding boxes\n\n{json.dumps(boxes, indent=2)}"
        )]

    except Exception as e:
        logger.error(f"Error getting bounding boxes: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_extract_form_fields(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Extract all form fields from screen.

    Args:
        arguments: Dict with:
            - app_name: Optional app name

    Returns:
        List of form fields
    """
    if not ELEMENT_EXTRACTION_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Element extraction not available. Requires macOS with Accessibility API."
        )]

    app_name = arguments.get("app_name")

    try:
        extractor = ElementExtractor()

        pid = None
        if app_name:
            from Cocoa import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()

            for app in running_apps:
                if app.localizedName().lower() == app_name.lower():
                    pid = app.processIdentifier()
                    break

        fields = extractor.extract_form_fields(pid)

        return [types.TextContent(
            type="text",
            text=f"Found {len(fields)} form fields\n\n{json.dumps(fields, indent=2)}"
        )]

    except Exception as e:
        logger.error(f"Error extracting form fields: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_extract_clickable_elements(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Extract all clickable elements (buttons, links, etc.).

    Args:
        arguments: Dict with:
            - app_name: Optional app name

    Returns:
        List of clickable elements
    """
    if not ELEMENT_EXTRACTION_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Element extraction not available. Requires macOS with Accessibility API."
        )]

    app_name = arguments.get("app_name")

    try:
        extractor = ElementExtractor()

        pid = None
        if app_name:
            from Cocoa import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()

            for app in running_apps:
                if app.localizedName().lower() == app_name.lower():
                    pid = app.processIdentifier()
                    break

        elements = extractor.extract_clickable_elements(pid)

        return [types.TextContent(
            type="text",
            text=f"Found {len(elements)} clickable elements\n\n{json.dumps(elements, indent=2)}"
        )]

    except Exception as e:
        logger.error(f"Error extracting clickable elements: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_extract_text_content(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Extract all text content from screen.

    Args:
        arguments: Dict with:
            - app_name: Optional app name

    Returns:
        All text content
    """
    if not ELEMENT_EXTRACTION_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Element extraction not available. Requires macOS with Accessibility API."
        )]

    app_name = arguments.get("app_name")

    try:
        extractor = ElementExtractor()

        pid = None
        if app_name:
            from Cocoa import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()

            for app in running_apps:
                if app.localizedName().lower() == app_name.lower():
                    pid = app.processIdentifier()
                    break

        text_elements = extractor.extract_text_elements(pid)

        # Compile all text
        all_text = []
        for elem in text_elements:
            text = elem.get("AXValue") or elem.get("AXTitle") or ""
            if text:
                all_text.append(text)

        return [types.TextContent(
            type="text",
            text=f"Extracted {len(all_text)} text elements:\n\n" + "\n".join(all_text)
        )]

    except Exception as e:
        logger.error(f"Error extracting text content: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Smart Waiting Handlers

def handle_wait_for_element(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Wait for UI element to appear.

    Args:
        arguments: Dict with:
            - name: Optional element name/title
            - role: Optional element role (e.g., "AXButton")
            - app_name: Optional app name to limit search
            - timeout: Optional timeout in seconds (default: 10.0)
            - poll_interval: Optional polling interval (default: 0.5)
            - min_count: Optional minimum element count (default: 1)

    Returns:
        Wait result with found elements
    """
    if not SMART_WAITING_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Smart waiting not available. Requires macOS with Accessibility API."
        )]

    name = arguments.get("name")
    role = arguments.get("role")
    app_name = arguments.get("app_name")
    timeout = arguments.get("timeout", 10.0)
    poll_interval = arguments.get("poll_interval", 0.5)
    min_count = arguments.get("min_count", 1)

    try:
        waiter = SmartWaiter()
        result, elements, error = waiter.wait_for_element(
            name=name,
            role=role,
            app_name=app_name,
            timeout=timeout,
            poll_interval=poll_interval,
            min_count=min_count
        )

        if result == WaitResult.SUCCESS:
            return [types.TextContent(
                type="text",
                text=f"✓ Found {len(elements)} element(s) matching criteria\n\n" +
                     f"Search: name={name}, role={role}, app={app_name}\n" +
                     f"Elements are ready for interaction."
            )]
        elif result == WaitResult.TIMEOUT:
            return [types.TextContent(
                type="text",
                text=f"✗ Timeout waiting for element\n\nError: {error}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"✗ Error waiting for element\n\nError: {error}"
            )]

    except Exception as e:
        logger.error(f"Error in wait_for_element: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_wait_for_element_property(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Wait for element property to reach expected value.

    Args:
        arguments: Dict with:
            - name: Optional element name
            - role: Optional element role
            - app_name: Optional app name
            - property_name: Property to check (e.g., "AXValue", "AXEnabled")
            - expected_value: Expected value (None = any non-None value)
            - timeout: Optional timeout (default: 10.0)
            - poll_interval: Optional polling interval (default: 0.5)

    Returns:
        Wait result with property value
    """
    if not SMART_WAITING_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Smart waiting not available. Requires macOS with Accessibility API."
        )]

    name = arguments.get("name")
    role = arguments.get("role")
    app_name = arguments.get("app_name")
    property_name = arguments.get("property_name", "AXValue")
    expected_value = arguments.get("expected_value")
    timeout = arguments.get("timeout", 10.0)
    poll_interval = arguments.get("poll_interval", 0.5)

    try:
        waiter = SmartWaiter()
        result, actual_value, error = waiter.wait_for_element_property(
            name=name,
            role=role,
            app_name=app_name,
            property_name=property_name,
            expected_value=expected_value,
            timeout=timeout,
            poll_interval=poll_interval
        )

        if result == WaitResult.SUCCESS:
            return [types.TextContent(
                type="text",
                text=f"✓ Property condition met\n\n" +
                     f"Element: name={name}, role={role}\n" +
                     f"Property: {property_name}={actual_value}"
            )]
        elif result == WaitResult.TIMEOUT:
            return [types.TextContent(
                type="text",
                text=f"✗ Timeout waiting for property\n\nError: {error}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"✗ Error waiting for property\n\nError: {error}"
            )]

    except Exception as e:
        logger.error(f"Error in wait_for_element_property: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Visual Debugging Handlers

def handle_capture_annotated_screenshot(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Capture screenshot and annotate with element bounding boxes.

    Args:
        arguments: Dict with:
            - app_name: Optional app name to limit elements
            - role_filter: Optional list of roles to show
            - output_path: Optional output path (default: temp file)
            - show_labels: Optional show element labels (default: True)
            - show_roles: Optional show element roles (default: False)

    Returns:
        Path to annotated screenshot
    """
    if not VISUAL_DEBUGGING_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Visual debugging not available. Requires macOS with PIL/Pillow installed."
        )]

    app_name = arguments.get("app_name")
    role_filter = arguments.get("role_filter")
    output_path = arguments.get("output_path")
    show_labels = arguments.get("show_labels", True)
    show_roles = arguments.get("show_roles", False)

    try:
        debugger = VisualDebugger()
        success, path, error = debugger.capture_and_annotate(
            app_name=app_name,
            role_filter=role_filter,
            output_path=output_path,
            show_labels=show_labels,
            show_roles=show_roles
        )

        if success:
            return [types.TextContent(
                type="text",
                text=f"✓ Annotated screenshot saved\n\nPath: {path}\n\n" +
                     f"Screenshot shows all UI elements with colored bounding boxes.\n" +
                     f"Colors indicate element types (red=buttons, green=text fields, etc.)"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"✗ Failed to capture annotated screenshot\n\nError: {error}"
            )]

    except Exception as e:
        logger.error(f"Error capturing annotated screenshot: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_highlight_element(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Capture screenshot and highlight specific element.

    Args:
        arguments: Dict with:
            - element_name: Element name to highlight (required)
            - role: Optional element role
            - app_name: Optional app name
            - output_path: Optional output path

    Returns:
        Path to highlighted screenshot
    """
    if not VISUAL_DEBUGGING_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Visual debugging not available. Requires macOS with PIL/Pillow installed."
        )]

    element_name = arguments.get("element_name")
    role = arguments.get("role")
    app_name = arguments.get("app_name")
    output_path = arguments.get("output_path")

    if not element_name:
        raise ValueError("element_name is required")

    try:
        from visual_debugging import highlight_element_on_screen

        success, path, error = highlight_element_on_screen(
            element_name=element_name,
            role=role,
            app_name=app_name
        )

        if success:
            return [types.TextContent(
                type="text",
                text=f"✓ Element highlighted on screenshot\n\nPath: {path}\n\n" +
                     f"Highlighted element: {element_name}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"✗ Failed to highlight element\n\nError: {error}"
            )]

    except Exception as e:
        logger.error(f"Error highlighting element: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_visualize_element_tree(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Create text visualization of UI element tree.

    Args:
        arguments: Dict with:
            - app_name: Optional app name
            - max_depth: Optional max tree depth (default: 5)
            - output_path: Optional output path

    Returns:
        Path to element tree visualization
    """
    if not VISUAL_DEBUGGING_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Visual debugging not available. Requires macOS with Accessibility API."
        )]

    app_name = arguments.get("app_name")
    max_depth = arguments.get("max_depth", 5)
    output_path = arguments.get("output_path")

    try:
        debugger = VisualDebugger()
        success, path, error = debugger.visualize_element_tree(
            app_name=app_name,
            max_depth=max_depth,
            output_path=output_path
        )

        if success:
            # Also read and return the content
            with open(path, 'r') as f:
                content = f.read()

            return [types.TextContent(
                type="text",
                text=f"✓ Element tree visualization saved\n\nPath: {path}\n\n" +
                     f"Preview:\n{content[:2000]}..." if len(content) > 2000 else content
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"✗ Failed to visualize element tree\n\nError: {error}"
            )]

    except Exception as e:
        logger.error(f"Error visualizing element tree: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Window Management Handlers

def handle_list_windows(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    List all windows or windows for specific app.

    Args:
        arguments: Dict with:
            - app_name: Optional app name to filter

    Returns:
        List of windows with details
    """
    if not WINDOW_MANAGER_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Window management not available. Requires macOS with Accessibility permissions."
        )]

    app_name = arguments.get("app_name")

    try:
        manager = WindowManager()
        windows = manager.list_all_windows(app_name)

        if not windows:
            return [types.TextContent(
                type="text",
                text=f"No windows found" + (f" for app: {app_name}" if app_name else "")
            )]

        # Format window list
        window_list = []
        for w in windows:
            window_list.append(
                f"• {w.get('app_name', 'Unknown')} - {w.get('title', 'Untitled')}\n"
                f"  Position: ({w.get('x', 0)}, {w.get('y', 0)})\n"
                f"  Size: {w.get('width', 0)}x{w.get('height', 0)}\n"
                f"  Minimized: {w.get('minimized', False)}"
            )

        return [types.TextContent(
            type="text",
            text=f"Found {len(windows)} window(s):\n\n" + "\n\n".join(window_list)
        )]

    except Exception as e:
        logger.error(f"Error listing windows: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_resize_window(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Resize a window.

    Args:
        arguments: Dict with:
            - window_title: Window title (required)
            - width: New width in pixels (required)
            - height: New height in pixels (required)
            - app_name: Optional app name filter

    Returns:
        Success/failure message
    """
    if not WINDOW_MANAGER_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Window management not available. Requires macOS with Accessibility permissions."
        )]

    window_title = arguments.get("window_title")
    width = arguments.get("width")
    height = arguments.get("height")
    app_name = arguments.get("app_name")

    if not window_title:
        raise ValueError("window_title is required")
    if width is None or height is None:
        raise ValueError("width and height are required")

    try:
        manager = WindowManager()
        window, pid, error = manager.get_window_by_title(window_title, app_name)

        if not window:
            return [types.TextContent(type="text", text=f"✗ {error}")]

        success, error = manager.resize_window(window, width, height)

        if success:
            return [types.TextContent(
                type="text",
                text=f"✓ Resized window '{window_title}' to {width}x{height}"
            )]
        else:
            return [types.TextContent(type="text", text=f"✗ {error}")]

    except Exception as e:
        logger.error(f"Error resizing window: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_move_window(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Move a window to new position.

    Args:
        arguments: Dict with:
            - window_title: Window title (required)
            - x: New x coordinate (required)
            - y: New y coordinate (required)
            - app_name: Optional app name filter

    Returns:
        Success/failure message
    """
    if not WINDOW_MANAGER_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Window management not available. Requires macOS with Accessibility permissions."
        )]

    window_title = arguments.get("window_title")
    x = arguments.get("x")
    y = arguments.get("y")
    app_name = arguments.get("app_name")

    if not window_title:
        raise ValueError("window_title is required")
    if x is None or y is None:
        raise ValueError("x and y coordinates are required")

    try:
        manager = WindowManager()
        window, pid, error = manager.get_window_by_title(window_title, app_name)

        if not window:
            return [types.TextContent(type="text", text=f"✗ {error}")]

        success, error = manager.move_window(window, x, y)

        if success:
            return [types.TextContent(
                type="text",
                text=f"✓ Moved window '{window_title}' to ({x}, {y})"
            )]
        else:
            return [types.TextContent(type="text", text=f"✗ {error}")]

    except Exception as e:
        logger.error(f"Error moving window: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_window_action(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Perform action on window (minimize, maximize, fullscreen, close).

    Args:
        arguments: Dict with:
            - window_title: Window title (required)
            - action: Action to perform (required) - "minimize", "maximize", "fullscreen", "close", "restore"
            - app_name: Optional app name filter

    Returns:
        Success/failure message
    """
    if not WINDOW_MANAGER_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Window management not available. Requires macOS with Accessibility permissions."
        )]

    window_title = arguments.get("window_title")
    action = arguments.get("action")
    app_name = arguments.get("app_name")

    if not window_title:
        raise ValueError("window_title is required")
    if not action:
        raise ValueError("action is required")

    try:
        manager = WindowManager()
        window, pid, error = manager.get_window_by_title(window_title, app_name)

        if not window:
            return [types.TextContent(type="text", text=f"✗ {error}")]

        # Perform action
        if action == "minimize":
            success, error = manager.minimize_window(window)
        elif action == "maximize":
            success, error = manager.maximize_window(window)
        elif action == "fullscreen":
            success, error = manager.fullscreen_window(window)
        elif action == "close":
            success, error = manager.close_window(window)
        elif action == "restore":
            success, error = manager.restore_window(window)
        else:
            return [types.TextContent(
                type="text",
                text=f"✗ Unknown action: {action}. Use: minimize, maximize, fullscreen, close, restore"
            )]

        if success:
            return [types.TextContent(
                type="text",
                text=f"✓ Performed '{action}' on window '{window_title}'"
            )]
        else:
            return [types.TextContent(type="text", text=f"✗ {error}")]

    except Exception as e:
        logger.error(f"Error performing window action: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_switch_to_window(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Switch to a specific window.

    Args:
        arguments: Dict with:
            - app_name: Application name (required)
            - window_title: Optional window title to switch to specific window

    Returns:
        Success/failure message
    """
    if not WINDOW_MANAGER_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Window management not available. Requires macOS with Accessibility permissions."
        )]

    app_name = arguments.get("app_name")
    window_title = arguments.get("window_title")

    if not app_name:
        raise ValueError("app_name is required")

    try:
        manager = WindowManager()
        success, error = manager.switch_to_window(app_name, window_title)

        if success:
            msg = f"✓ Switched to {app_name}"
            if window_title:
                msg += f" - '{window_title}'"
            return [types.TextContent(type="text", text=msg)]
        else:
            return [types.TextContent(type="text", text=f"✗ {error}")]

    except Exception as e:
        logger.error(f"Error switching to window: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Advanced Interaction Handlers

def handle_right_click(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Perform right-click at coordinates.

    Args:
        arguments: Dict with:
            - x: X coordinate (required)
            - y: Y coordinate (required)
            - menu_item: Optional menu item to click after right-click

    Returns:
        Success/failure message
    """
    if not ADVANCED_INTERACTIONS_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Advanced interactions not available. Requires macOS with Quartz framework."
        )]

    x = arguments.get("x")
    y = arguments.get("y")
    menu_item = arguments.get("menu_item")

    if x is None or y is None:
        raise ValueError("x and y coordinates are required")

    try:
        interactions = AdvancedInteractions()

        if menu_item:
            success, error = interactions.context_menu_click(x, y, menu_item)
            if success:
                return [types.TextContent(
                    type="text",
                    text=f"✓ Right-clicked at ({x}, {y}) and selected '{menu_item}'"
                )]
        else:
            success, error = interactions.right_click(x, y)
            if success:
                return [types.TextContent(
                    type="text",
                    text=f"✓ Right-clicked at ({x}, {y})"
                )]

        return [types.TextContent(type="text", text=f"✗ {error}")]

    except Exception as e:
        logger.error(f"Error performing right-click: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_select_text(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Select text by dragging or using select all.

    Args:
        arguments: Dict with:
            - start_x: Optional start X coordinate for drag selection
            - start_y: Optional start Y coordinate for drag selection
            - end_x: Optional end X coordinate for drag selection
            - end_y: Optional end Y coordinate for drag selection
            - select_all: Optional boolean to select all text (Cmd+A)

    Returns:
        Success/failure message
    """
    if not ADVANCED_INTERACTIONS_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Advanced interactions not available. Requires macOS with Quartz framework."
        )]

    start_x = arguments.get("start_x")
    start_y = arguments.get("start_y")
    end_x = arguments.get("end_x")
    end_y = arguments.get("end_y")
    select_all = arguments.get("select_all", False)

    try:
        interactions = AdvancedInteractions()

        if select_all:
            success, error = interactions.select_all_text()
            if success:
                return [types.TextContent(
                    type="text",
                    text="✓ Selected all text (Cmd+A)"
                )]
        elif start_x is not None and start_y is not None and end_x is not None and end_y is not None:
            success, error = interactions.select_text(start_x, start_y, end_x, end_y)
            if success:
                return [types.TextContent(
                    type="text",
                    text=f"✓ Selected text from ({start_x}, {start_y}) to ({end_x}, {end_y})"
                )]
        else:
            return [types.TextContent(
                type="text",
                text="✗ Either provide coordinates (start_x, start_y, end_x, end_y) or set select_all=true"
            )]

        return [types.TextContent(type="text", text=f"✗ {error}")]

    except Exception as e:
        logger.error(f"Error selecting text: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_copy_cut_selection(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Copy or cut selected text to clipboard.

    Args:
        arguments: Dict with:
            - action: "copy" or "cut" (required)

    Returns:
        Success/failure message and clipboard content
    """
    if not ADVANCED_INTERACTIONS_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Advanced interactions not available. Requires macOS with Quartz framework."
        )]

    action = arguments.get("action", "copy")

    try:
        interactions = AdvancedInteractions()

        if action == "copy":
            success, error = interactions.copy_selection()
        elif action == "cut":
            success, error = interactions.cut_selection()
        else:
            return [types.TextContent(
                type="text",
                text=f"✗ Unknown action: {action}. Use 'copy' or 'cut'"
            )]

        if success:
            # Get clipboard content to confirm
            try:
                from system_controls import ClipboardManager
                clipboard = ClipboardManager()
                content = clipboard.read_text()
                return [types.TextContent(
                    type="text",
                    text=f"✓ {action.capitalize()}d to clipboard\n\nClipboard content:\n{content[:500]}" +
                         ("..." if len(content) > 500 else "")
                )]
            except:
                return [types.TextContent(
                    type="text",
                    text=f"✓ {action.capitalize()}d to clipboard"
                )]
        else:
            return [types.TextContent(type="text", text=f"✗ {error}")]

    except Exception as e:
        logger.error(f"Error copying/cutting: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


def handle_gesture(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Simulate multi-finger gesture.

    Args:
        arguments: Dict with:
            - gesture_type: Gesture type (required) - "pinch_in", "pinch_out", "swipe_left", "swipe_right", "swipe_up", "swipe_down"
            - center_x: Center X coordinate (required)
            - center_y: Center Y coordinate (required)
            - magnitude: Optional gesture magnitude in pixels (default: 100)

    Returns:
        Success/failure message
    """
    if not ADVANCED_INTERACTIONS_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Advanced interactions not available. Requires macOS with Quartz framework."
        )]

    gesture_type_str = arguments.get("gesture_type")
    center_x = arguments.get("center_x")
    center_y = arguments.get("center_y")
    magnitude = arguments.get("magnitude", 100.0)

    if not gesture_type_str:
        raise ValueError("gesture_type is required")
    if center_x is None or center_y is None:
        raise ValueError("center_x and center_y are required")

    try:
        # Parse gesture type
        gesture_type = GestureType(gesture_type_str)

        interactions = AdvancedInteractions()
        success, error = interactions.simulate_gesture(gesture_type, center_x, center_y, magnitude)

        if success:
            return [types.TextContent(
                type="text",
                text=f"✓ Simulated {gesture_type_str} gesture at ({center_x}, {center_y})"
            )]
        else:
            return [types.TextContent(type="text", text=f"✗ {error}")]

    except ValueError:
        return [types.TextContent(
            type="text",
            text=f"✗ Invalid gesture_type: {gesture_type_str}\n" +
                 "Valid types: pinch_in, pinch_out, swipe_left, swipe_right, swipe_up, swipe_down"
        )]
    except Exception as e:
        logger.error(f"Error simulating gesture: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
