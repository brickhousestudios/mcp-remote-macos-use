import logging
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
import base64
import socket
import time
import io
from PIL import Image
import asyncio
import pyDes
import json
import os
from base64 import b64encode
from datetime import datetime
import sys

# Import MCP server libraries
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Import LiveKit
from livekit import api
from .livekit_handler import LiveKitHandler

# Import VNC client functionality from the src directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vnc_client import VNCClient, capture_vnc_screen

# Import action handlers from the src directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from action_handlers import (
    handle_remote_macos_get_screen,
    handle_remote_macos_mouse_scroll,
    handle_remote_macos_send_keys,
    handle_remote_macos_mouse_move,
    handle_remote_macos_mouse_click,
    handle_remote_macos_mouse_double_click,
    handle_remote_macos_open_application,
    handle_remote_macos_mouse_drag_n_drop
)

# Import semantic action handlers (Accessibility API + MLX)
try:
    from semantic_handlers import (
        handle_macos_find_element,
        handle_macos_click_element,
        handle_macos_type_text_semantic,
        handle_macos_get_focused_app,
        handle_macos_launch_app_native,
        handle_macos_get_capabilities
    )
    SEMANTIC_HANDLERS_AVAILABLE = True
    logger.info("Semantic handlers (Accessibility API) loaded successfully")
except ImportError as e:
    SEMANTIC_HANDLERS_AVAILABLE = False
    logger.warning(f"Semantic handlers not available: {e}")

# Import advanced handlers (AppleScript, clipboard, system, batch, element extraction, smart waiting, visual debugging, window management, advanced interactions)
try:
    from advanced_handlers import (
        handle_execute_applescript,
        handle_applescript_tell_app,
        handle_read_clipboard,
        handle_write_clipboard,
        handle_set_volume,
        handle_get_volume,
        handle_system_action,
        handle_batch_operations,
        handle_extract_screen_structure,
        handle_extract_all_elements,
        handle_get_bounding_boxes,
        handle_extract_form_fields,
        handle_extract_clickable_elements,
        handle_extract_text_content,
        handle_wait_for_element,
        handle_wait_for_element_property,
        handle_capture_annotated_screenshot,
        handle_highlight_element,
        handle_visualize_element_tree,
        handle_list_windows,
        handle_resize_window,
        handle_move_window,
        handle_window_action,
        handle_switch_to_window,
        handle_right_click,
        handle_select_text,
        handle_copy_cut_selection,
        handle_gesture
    )
    ADVANCED_HANDLERS_AVAILABLE = True
    logger.info("Advanced handlers (AppleScript, clipboard, system, extraction, smart waiting, visual debugging, window management, advanced interactions) loaded successfully")
except ImportError as e:
    ADVANCED_HANDLERS_AVAILABLE = False
    logger.warning(f"Advanced handlers not available: {e}")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp_remote_macos_use')
logger.setLevel(logging.DEBUG)

# Load environment variables for VNC connection
MACOS_HOST = os.environ.get('MACOS_HOST', '')
MACOS_PORT = int(os.environ.get('MACOS_PORT', '5900'))
MACOS_USERNAME = os.environ.get('MACOS_USERNAME', '')
MACOS_PASSWORD = os.environ.get('MACOS_PASSWORD', '')
VNC_ENCRYPTION = os.environ.get('VNC_ENCRYPTION', 'prefer_on')

# LiveKit configuration
LIVEKIT_URL = os.environ.get('LIVEKIT_URL', '')
LIVEKIT_API_KEY = os.environ.get('LIVEKIT_API_KEY', '')
LIVEKIT_API_SECRET = os.environ.get('LIVEKIT_API_SECRET', '')

# Log environment variable status (without exposing actual values)
logger.info(f"MACOS_HOST from environment: {'Set' if MACOS_HOST else 'Not set'}")
logger.info(f"MACOS_PORT from environment: {MACOS_PORT}")
logger.info(f"MACOS_USERNAME from environment: {'Set' if MACOS_USERNAME else 'Not set'}")
logger.info(f"MACOS_PASSWORD from environment: {'Set' if MACOS_PASSWORD else 'Not set (Required)'}")
logger.info(f"VNC_ENCRYPTION from environment: {VNC_ENCRYPTION}")
logger.info(f"LIVEKIT_URL from environment: {'Set' if LIVEKIT_URL else 'Not set'}")
logger.info(f"LIVEKIT_API_KEY from environment: {'Set' if LIVEKIT_API_KEY else 'Not set'}")
logger.info(f"LIVEKIT_API_SECRET from environment: {'Set' if LIVEKIT_API_SECRET else 'Not set'}")

# Validate required environment variables
if not MACOS_HOST:
    logger.error("MACOS_HOST environment variable is required but not set")
    raise ValueError("MACOS_HOST environment variable is required but not set")

if not MACOS_PASSWORD:
    logger.error("MACOS_PASSWORD environment variable is required but not set")
    raise ValueError("MACOS_PASSWORD environment variable is required but not set")


async def main():
    """Run the Remote MacOS MCP server."""
    logger.info("Remote MacOS computer use server starting")

    # Initialize LiveKit handler if environment variables are set
    livekit_handler = None
    if all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        livekit_handler = LiveKitHandler()

        # Generate access token for the room
        token = api.AccessToken() \
            .with_identity("remote-macos-bot") \
            .with_name("Remote MacOS Bot") \
            .with_grants(api.VideoGrants(
                room_join=True,
                room="remote-macos-room",
            )).to_jwt()

        # Start LiveKit connection
        success = await livekit_handler.start("remote-macos-room", token)
        if success:
            logger.info("LiveKit connection established")
        else:
            logger.warning("Failed to establish LiveKit connection")
            livekit_handler = None

    # Validate required environment variables
    if not MACOS_HOST:
        logger.error("MACOS_HOST environment variable is required but not set")
        raise ValueError("MACOS_HOST environment variable is required but not set")

    if not MACOS_PASSWORD:
        logger.error("MACOS_PASSWORD environment variable is required but not set")
        raise ValueError("MACOS_PASSWORD environment variable is required but not set")

    server = Server("remote-macos-client")

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        return []

    @server.read_resource()
    async def handle_read_resource(uri: types.AnyUrl) -> str:
        return ""

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="remote_macos_get_screen",
                description="Connect to a remote MacOs machine and get a screenshot of the remote desktop. Uses environment variables for connection details.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
            ),
            types.Tool(
                name="remote_macos_mouse_scroll",
                description="Perform a mouse scroll at specified coordinates on a remote MacOs machine, with automatic coordinate scaling. Uses environment variables for connection details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X coordinate for mouse position (in source dimensions)"},
                        "y": {"type": "integer", "description": "Y coordinate for mouse position (in source dimensions)"},
                        "source_width": {"type": "integer", "description": "Width of the reference screen for coordinate scaling", "default": 1366},
                        "source_height": {"type": "integer", "description": "Height of the reference screen for coordinate scaling", "default": 768},
                        "direction": {
                            "type": "string",
                            "description": "Scroll direction",
                            "enum": ["up", "down"],
                            "default": "down"
                        }
                    },
                    "required": ["x", "y"]
                },
            ),
            types.Tool(
                name="remote_macos_send_keys",
                description="Send keyboard input to a remote MacOs machine. Uses environment variables for connection details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to send as keystrokes"},
                        "special_key": {"type": "string", "description": "Special key to send (e.g., 'enter', 'backspace', 'tab', 'escape', etc.)"},
                        "key_combination": {"type": "string", "description": "Key combination to send (e.g., 'ctrl+c', 'cmd+q', 'ctrl+alt+delete', etc.)"}
                    },
                    "required": []
                },
            ),
            types.Tool(
                name="remote_macos_mouse_move",
                description="Move the mouse cursor to specified coordinates on a remote MacOs machine, with automatic coordinate scaling. Uses environment variables for connection details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X coordinate for mouse position (in source dimensions)"},
                        "y": {"type": "integer", "description": "Y coordinate for mouse position (in source dimensions)"},
                        "source_width": {"type": "integer", "description": "Width of the reference screen for coordinate scaling", "default": 1366},
                        "source_height": {"type": "integer", "description": "Height of the reference screen for coordinate scaling", "default": 768}
                    },
                    "required": ["x", "y"]
                },
            ),
            types.Tool(
                name="remote_macos_mouse_click",
                description="Perform a mouse click at specified coordinates on a remote MacOs machine, with automatic coordinate scaling. Uses environment variables for connection details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X coordinate for mouse position (in source dimensions)"},
                        "y": {"type": "integer", "description": "Y coordinate for mouse position (in source dimensions)"},
                        "source_width": {"type": "integer", "description": "Width of the reference screen for coordinate scaling", "default": 1366},
                        "source_height": {"type": "integer", "description": "Height of the reference screen for coordinate scaling", "default": 768},
                        "button": {"type": "integer", "description": "Mouse button (1=left, 2=middle, 3=right)", "default": 1}
                    },
                    "required": ["x", "y"]
                },
            ),
            types.Tool(
                name="remote_macos_mouse_double_click",
                description="Perform a mouse double-click at specified coordinates on a remote MacOs machine, with automatic coordinate scaling. Uses environment variables for connection details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X coordinate for mouse position (in source dimensions)"},
                        "y": {"type": "integer", "description": "Y coordinate for mouse position (in source dimensions)"},
                        "source_width": {"type": "integer", "description": "Width of the reference screen for coordinate scaling", "default": 1366},
                        "source_height": {"type": "integer", "description": "Height of the reference screen for coordinate scaling", "default": 768},
                        "button": {"type": "integer", "description": "Mouse button (1=left, 2=middle, 3=right)", "default": 1}
                    },
                    "required": ["x", "y"]
                },
            ),
            types.Tool(
                name="remote_macos_open_application",
                description="Opens/activates an application and returns its PID for further interactions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "identifier": {
                            "type": "string",
                            "description": "REQUIRED. App name, path, or bundle ID."
                        }
                    },
                    "required": ["identifier"]
                },
            ),
            types.Tool(
                name="remote_macos_mouse_drag_n_drop",
                description="Perform a mouse drag operation from start point and drop to end point on a remote MacOs machine, with automatic coordinate scaling.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_x": {"type": "integer", "description": "Starting X coordinate (in source dimensions)"},
                        "start_y": {"type": "integer", "description": "Starting Y coordinate (in source dimensions)"},
                        "end_x": {"type": "integer", "description": "Ending X coordinate (in source dimensions)"},
                        "end_y": {"type": "integer", "description": "Ending Y coordinate (in source dimensions)"},
                        "source_width": {"type": "integer", "description": "Width of the reference screen for coordinate scaling", "default": 1366},
                        "source_height": {"type": "integer", "description": "Height of the reference screen for coordinate scaling", "default": 768},
                        "button": {"type": "integer", "description": "Mouse button (1=left, 2=middle, 3=right)", "default": 1},
                        "steps": {"type": "integer", "description": "Number of intermediate points for smooth dragging", "default": 10},
                        "delay_ms": {"type": "integer", "description": "Delay between steps in milliseconds", "default": 10}
                    },
                    "required": ["start_x", "start_y", "end_x", "end_y"]
                },
            ),
        ] + ([
            # Semantic UI control tools (Accessibility API + MLX Vision)
            # Only available on macOS with proper permissions
            types.Tool(
                name="macos_find_element",
                description="Find UI elements by name, role, or properties using native Accessibility API. Much faster than VNC for local control. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Element name/title to search for"},
                        "role": {"type": "string", "description": "Element role (e.g., 'AXButton', 'AXTextField', 'AXMenuItem')"},
                        "app_name": {"type": "string", "description": "Limit search to specific application"}
                    },
                    "required": []
                },
            ),
            types.Tool(
                name="macos_click_element",
                description="Click a UI element by its name/title (semantic click). No coordinates needed! Uses native Accessibility API. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Element name/title to click"},
                        "role": {"type": "string", "description": "Optional element role filter (e.g., 'AXButton')"},
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"}
                    },
                    "required": ["name"]
                },
            ),
            types.Tool(
                name="macos_type_text_native",
                description="Type text into the currently focused text field using native APIs. Faster and more reliable than VNC. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to type"}
                    },
                    "required": ["text"]
                },
            ),
            types.Tool(
                name="macos_get_focused_app",
                description="Get information about the currently focused application. Uses native APIs. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
            ),
            types.Tool(
                name="macos_launch_app_native",
                description="Launch an application using native macOS APIs (faster than VNC/Spotlight method). Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Application name or bundle ID"}
                    },
                    "required": ["app_name"]
                },
            ),
            types.Tool(
                name="macos_get_capabilities",
                description="Get the available control capabilities (Accessibility API, VNC, MLX Vision) and current control method being used.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
            ),
        ] if SEMANTIC_HANDLERS_AVAILABLE else []) + ([
            # Advanced automation tools (AppleScript, clipboard, system controls, batch)
            types.Tool(
                name="execute_applescript",
                description="Execute an AppleScript for advanced macOS automation. Enables complex tasks like app-specific automation, file operations, system integration. Requires macOS.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "AppleScript code to execute"},
                        "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)", "default": 30}
                    },
                    "required": ["script"]
                },
            ),
            types.Tool(
                name="applescript_tell_app",
                description="Send an AppleScript command to a specific application (e.g., 'tell Safari to open location...'). Easier than writing full AppleScript. Requires macOS.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Application name"},
                        "command": {"type": "string", "description": "AppleScript command(s) to send to the app"},
                        "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)", "default": 30}
                    },
                    "required": ["app_name", "command"]
                },
            ),
            types.Tool(
                name="read_clipboard",
                description="Read text from the system clipboard. Useful for getting copied text, URLs, etc. Requires macOS with PyObjC.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
            ),
            types.Tool(
                name="write_clipboard",
                description="Write text to the system clipboard. Useful for copying text for pasting elsewhere. Requires macOS with PyObjC.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to write to clipboard"}
                    },
                    "required": ["text"]
                },
            ),
            types.Tool(
                name="set_volume",
                description="Set the system volume level. Requires macOS.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "level": {"type": "integer", "description": "Volume level (0-100)", "minimum": 0, "maximum": 100}
                    },
                    "required": ["level"]
                },
            ),
            types.Tool(
                name="get_volume",
                description="Get the current system volume level. Requires macOS.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
            ),
            types.Tool(
                name="system_action",
                description="Perform system actions: lock screen, sleep, logout, mute/unmute. Requires macOS.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Action to perform",
                            "enum": ["lock", "sleep", "logout", "mute", "unmute"]
                        }
                    },
                    "required": ["action"]
                },
            ),
            types.Tool(
                name="batch_operations",
                description="Execute multiple operations in sequence efficiently. Useful for complex workflows. Supports all mouse/keyboard/semantic tools.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "operations": {
                            "type": "array",
                            "description": "List of operations to execute",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tool": {"type": "string", "description": "Tool name to execute"},
                                    "arguments": {"type": "object", "description": "Arguments for the tool"},
                                    "delay_ms": {"type": "integer", "description": "Delay after this operation (default: 100ms)", "default": 100}
                                },
                                "required": ["tool", "arguments"]
                            }
                        }
                    },
                    "required": ["operations"]
                },
            ),
            # Element extraction tools (screen scraping, bounding boxes)
            types.Tool(
                name="extract_screen_structure",
                description="Extract complete UI tree/structure from screen as JSON. Includes element hierarchy, properties, positions. Perfect for screen scraping and understanding UI layout. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"},
                        "include_all_properties": {"type": "boolean", "description": "Include all element properties (default: false)", "default": False},
                        "format": {"type": "string", "description": "Output format: 'json' or 'summary' (default: 'json')", "enum": ["json", "summary"], "default": "json"}
                    }
                },
            ),
            types.Tool(
                name="extract_all_elements",
                description="Extract all UI elements as a flat list (not nested tree). Useful for finding all elements of certain types. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"},
                        "role_filter": {"type": "array", "description": "Optional: only include these roles (e.g., ['AXButton', 'AXTextField'])", "items": {"type": "string"}},
                        "max_depth": {"type": "integer", "description": "Maximum depth to traverse (default: 10)", "default": 10}
                    }
                },
            ),
            types.Tool(
                name="get_bounding_boxes",
                description="Get bounding boxes (x, y, width, height) for all UI elements. Perfect for visual element detection and positioning. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"},
                        "role_filter": {"type": "array", "description": "Optional: only include these roles", "items": {"type": "string"}}
                    }
                },
            ),
            types.Tool(
                name="extract_form_fields",
                description="Extract all form fields (text fields, checkboxes, radio buttons, etc.). Perfect for automated form filling. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"}
                    }
                },
            ),
            types.Tool(
                name="extract_clickable_elements",
                description="Extract all clickable elements (buttons, links, menu items). Find all interactive elements on screen. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"}
                    }
                },
            ),
            types.Tool(
                name="extract_text_content",
                description="Extract all visible text content from screen. Perfect for screen reading and text extraction. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"}
                    }
                },
            ),
            types.Tool(
                name="wait_for_element",
                description="Wait for UI element to appear on screen. Returns when element is found or timeout is reached. Perfect for waiting for dynamic content, page loads, or UI state changes. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Optional: element name/title to search for"},
                        "role": {"type": "string", "description": "Optional: element role (e.g., 'AXButton', 'AXTextField')"},
                        "app_name": {"type": "string", "description": "Optional: limit search to specific application"},
                        "timeout": {"type": "number", "description": "Optional: timeout in seconds (default: 10.0)"},
                        "poll_interval": {"type": "number", "description": "Optional: polling interval in seconds (default: 0.5)"},
                        "min_count": {"type": "integer", "description": "Optional: minimum number of elements to find (default: 1)"}
                    }
                },
            ),
            types.Tool(
                name="wait_for_element_property",
                description="Wait for element property to reach expected value. Returns when property condition is met or timeout is reached. Perfect for waiting for text changes, state changes, or loading indicators. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Optional: element name/title"},
                        "role": {"type": "string", "description": "Optional: element role"},
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"},
                        "property_name": {"type": "string", "description": "Property to check (e.g., 'AXValue', 'AXEnabled') - default: 'AXValue'"},
                        "expected_value": {"type": "string", "description": "Expected value (omit for any non-None value)"},
                        "timeout": {"type": "number", "description": "Optional: timeout in seconds (default: 10.0)"},
                        "poll_interval": {"type": "number", "description": "Optional: polling interval in seconds (default: 0.5)"}
                    }
                },
            ),
            types.Tool(
                name="capture_annotated_screenshot",
                description="Capture screenshot and annotate with element bounding boxes. All UI elements are outlined with colored boxes and labeled. Perfect for debugging UI automation and visualizing screen structure. Requires macOS with Accessibility permissions and PIL/Pillow.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"},
                        "role_filter": {"type": "array", "items": {"type": "string"}, "description": "Optional: only show specific element roles"},
                        "output_path": {"type": "string", "description": "Optional: output file path (default: temp file)"},
                        "show_labels": {"type": "boolean", "description": "Optional: show element labels (default: true)"},
                        "show_roles": {"type": "boolean", "description": "Optional: show element roles in labels (default: false)"}
                    }
                },
            ),
            types.Tool(
                name="highlight_element",
                description="Capture screenshot and highlight specific element. The target element is outlined with a thick colored box. Perfect for debugging element location and verifying automation targets. Requires macOS with Accessibility permissions and PIL/Pillow.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "element_name": {"type": "string", "description": "REQUIRED: element name to highlight"},
                        "role": {"type": "string", "description": "Optional: element role filter"},
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"},
                        "output_path": {"type": "string", "description": "Optional: output file path (default: temp file)"}
                    },
                    "required": ["element_name"]
                },
            ),
            types.Tool(
                name="visualize_element_tree",
                description="Create text visualization of UI element hierarchy. Generates ASCII tree showing element structure, roles, and relationships. Perfect for understanding screen structure and planning automation. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: limit to specific application"},
                        "max_depth": {"type": "integer", "description": "Optional: maximum tree depth (default: 5)"},
                        "output_path": {"type": "string", "description": "Optional: output file path (default: temp file)"}
                    }
                },
            ),
            types.Tool(
                name="list_windows",
                description="List all windows or windows for specific application. Shows window title, position, size, and minimized state. Perfect for discovering available windows. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Optional: filter by application name"}
                    }
                },
            ),
            types.Tool(
                name="resize_window",
                description="Resize a window by title. Change window dimensions programmatically. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "window_title": {"type": "string", "description": "REQUIRED: window title"},
                        "width": {"type": "integer", "description": "REQUIRED: new width in pixels"},
                        "height": {"type": "integer", "description": "REQUIRED: new height in pixels"},
                        "app_name": {"type": "string", "description": "Optional: application name filter"}
                    },
                    "required": ["window_title", "width", "height"]
                },
            ),
            types.Tool(
                name="move_window",
                description="Move a window to new position. Change window location programmatically. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "window_title": {"type": "string", "description": "REQUIRED: window title"},
                        "x": {"type": "integer", "description": "REQUIRED: new x coordinate"},
                        "y": {"type": "integer", "description": "REQUIRED: new y coordinate"},
                        "app_name": {"type": "string", "description": "Optional: application name filter"}
                    },
                    "required": ["window_title", "x", "y"]
                },
            ),
            types.Tool(
                name="window_action",
                description="Perform action on window (minimize, maximize, fullscreen, close, restore). Control window state programmatically. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "window_title": {"type": "string", "description": "REQUIRED: window title"},
                        "action": {"type": "string", "enum": ["minimize", "maximize", "fullscreen", "close", "restore"], "description": "REQUIRED: action to perform"},
                        "app_name": {"type": "string", "description": "Optional: application name filter"}
                    },
                    "required": ["window_title", "action"]
                },
            ),
            types.Tool(
                name="switch_to_window",
                description="Switch to (activate) a specific window or application. Brings window to front and focuses it. Requires macOS with Accessibility permissions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "REQUIRED: application name"},
                        "window_title": {"type": "string", "description": "Optional: specific window title to focus"}
                    },
                    "required": ["app_name"]
                },
            ),
            types.Tool(
                name="right_click",
                description="Perform right-click at coordinates. Opens context menu. Optionally select menu item by name. Requires macOS with Quartz framework.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "REQUIRED: x coordinate"},
                        "y": {"type": "integer", "description": "REQUIRED: y coordinate"},
                        "menu_item": {"type": "string", "description": "Optional: menu item name to click"}
                    },
                    "required": ["x", "y"]
                },
            ),
            types.Tool(
                name="select_text",
                description="Select text by dragging or using select all (Cmd+A). Perfect for text manipulation. Requires macOS with Quartz framework.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_x": {"type": "integer", "description": "Start x coordinate for drag selection"},
                        "start_y": {"type": "integer", "description": "Start y coordinate for drag selection"},
                        "end_x": {"type": "integer", "description": "End x coordinate for drag selection"},
                        "end_y": {"type": "integer", "description": "End y coordinate for drag selection"},
                        "select_all": {"type": "boolean", "description": "Select all text (Cmd+A) instead of dragging"}
                    }
                },
            ),
            types.Tool(
                name="copy_cut_selection",
                description="Copy or cut selected text to clipboard (Cmd+C or Cmd+X). Returns clipboard content for verification. Requires macOS with Quartz framework.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["copy", "cut"], "description": "Action: 'copy' or 'cut' (default: 'copy')"}
                    }
                },
            ),
            types.Tool(
                name="gesture",
                description="Simulate multi-finger gestures (pinch, swipe, zoom). Perfect for map/image navigation. Note: Uses scroll events as proxy - limited support. Requires macOS with Quartz framework.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "gesture_type": {"type": "string", "enum": ["pinch_in", "pinch_out", "swipe_left", "swipe_right", "swipe_up", "swipe_down"], "description": "REQUIRED: gesture type"},
                        "center_x": {"type": "integer", "description": "REQUIRED: center x coordinate"},
                        "center_y": {"type": "integer", "description": "REQUIRED: center y coordinate"},
                        "magnitude": {"type": "number", "description": "Optional: gesture magnitude in pixels (default: 100)"}
                    },
                    "required": ["gesture_type", "center_x", "center_y"]
                },
            ),
        ] if ADVANCED_HANDLERS_AVAILABLE else [])

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""
        try:
            if not arguments:
                arguments = {}

            if name == "remote_macos_get_screen":
                return await handle_remote_macos_get_screen(arguments)

            elif name == "remote_macos_mouse_scroll":
                return handle_remote_macos_mouse_scroll(arguments)

            elif name == "remote_macos_send_keys":
                return handle_remote_macos_send_keys(arguments)

            elif name == "remote_macos_mouse_move":
                return handle_remote_macos_mouse_move(arguments)

            elif name == "remote_macos_mouse_click":
                return handle_remote_macos_mouse_click(arguments)

            elif name == "remote_macos_mouse_double_click":
                return handle_remote_macos_mouse_double_click(arguments)

            elif name == "remote_macos_open_application":
                return handle_remote_macos_open_application(arguments)

            elif name == "remote_macos_mouse_drag_n_drop":
                return handle_remote_macos_mouse_drag_n_drop(arguments)

            # Semantic UI control tools (Accessibility API)
            elif name == "macos_find_element" and SEMANTIC_HANDLERS_AVAILABLE:
                return handle_macos_find_element(arguments)

            elif name == "macos_click_element" and SEMANTIC_HANDLERS_AVAILABLE:
                return handle_macos_click_element(arguments)

            elif name == "macos_type_text_native" and SEMANTIC_HANDLERS_AVAILABLE:
                return handle_macos_type_text_semantic(arguments)

            elif name == "macos_get_focused_app" and SEMANTIC_HANDLERS_AVAILABLE:
                return handle_macos_get_focused_app(arguments)

            elif name == "macos_launch_app_native" and SEMANTIC_HANDLERS_AVAILABLE:
                return handle_macos_launch_app_native(arguments)

            elif name == "macos_get_capabilities" and SEMANTIC_HANDLERS_AVAILABLE:
                return handle_macos_get_capabilities(arguments)

            # Advanced automation tools (AppleScript, clipboard, system, batch)
            elif name == "execute_applescript" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_execute_applescript(arguments)

            elif name == "applescript_tell_app" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_applescript_tell_app(arguments)

            elif name == "read_clipboard" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_read_clipboard(arguments)

            elif name == "write_clipboard" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_write_clipboard(arguments)

            elif name == "set_volume" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_set_volume(arguments)

            elif name == "get_volume" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_get_volume(arguments)

            elif name == "system_action" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_system_action(arguments)

            elif name == "batch_operations" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_batch_operations(arguments)

            # Element extraction tools
            elif name == "extract_screen_structure" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_extract_screen_structure(arguments)

            elif name == "extract_all_elements" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_extract_all_elements(arguments)

            elif name == "get_bounding_boxes" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_get_bounding_boxes(arguments)

            elif name == "extract_form_fields" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_extract_form_fields(arguments)

            elif name == "extract_clickable_elements" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_extract_clickable_elements(arguments)

            elif name == "extract_text_content" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_extract_text_content(arguments)

            # Smart waiting tools
            elif name == "wait_for_element" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_wait_for_element(arguments)

            elif name == "wait_for_element_property" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_wait_for_element_property(arguments)

            # Visual debugging tools
            elif name == "capture_annotated_screenshot" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_capture_annotated_screenshot(arguments)

            elif name == "highlight_element" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_highlight_element(arguments)

            elif name == "visualize_element_tree" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_visualize_element_tree(arguments)

            # Window management tools
            elif name == "list_windows" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_list_windows(arguments)

            elif name == "resize_window" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_resize_window(arguments)

            elif name == "move_window" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_move_window(arguments)

            elif name == "window_action" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_window_action(arguments)

            elif name == "switch_to_window" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_switch_to_window(arguments)

            # Advanced interaction tools
            elif name == "right_click" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_right_click(arguments)

            elif name == "select_text" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_select_text(arguments)

            elif name == "copy_cut_selection" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_copy_cut_selection(arguments)

            elif name == "gesture" and ADVANCED_HANDLERS_AVAILABLE:
                return handle_gesture(arguments)

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error in handle_call_tool: {str(e)}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        try:
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="vnc-client",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        finally:
            if livekit_handler:
                await livekit_handler.stop()

if __name__ == "__main__":
    # Load environment variables from .env file if it exists
    load_dotenv()

    try:
        # Run the server
        asyncio.run(main())
    except ValueError as e:
        logger.error(f"Initialization failed: {str(e)}")
        print(f"ERROR: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"ERROR: Unexpected error occurred: {str(e)}")
        sys.exit(1)