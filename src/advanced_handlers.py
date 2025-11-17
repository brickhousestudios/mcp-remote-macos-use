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
