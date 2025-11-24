"""
Visual debugging utilities for macOS UI automation.

Provides tools for visualizing UI elements, bounding boxes, and element hierarchies
to help debug automation scripts and understand screen structure.
"""

import logging
import os
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from element_extractor import ElementExtractor, get_all_bounding_boxes
    ELEMENT_EXTRACTOR_AVAILABLE = True
except ImportError:
    ELEMENT_EXTRACTOR_AVAILABLE = False

try:
    from system_controls import SystemController
    SYSTEM_CONTROLS_AVAILABLE = True
except ImportError:
    SYSTEM_CONTROLS_AVAILABLE = False

# Configure logging
logger = logging.getLogger('visual_debugging')
logger.setLevel(logging.DEBUG)


class VisualDebugger:
    """
    Visual debugging utilities for UI automation.

    Features:
    - Annotate screenshots with bounding boxes
    - Highlight specific elements
    - Label elements with names/roles
    - Color-code by element type
    - Export annotated images
    """

    # Color scheme for different element types
    ELEMENT_COLORS = {
        "AXButton": (255, 0, 0),           # Red
        "AXTextField": (0, 255, 0),        # Green
        "AXTextArea": (0, 200, 0),         # Dark green
        "AXStaticText": (128, 128, 128),   # Gray
        "AXLink": (0, 0, 255),             # Blue
        "AXMenuItem": (255, 128, 0),       # Orange
        "AXCheckBox": (255, 0, 255),       # Magenta
        "AXRadioButton": (255, 0, 128),    # Pink
        "AXWindow": (128, 0, 128),         # Purple
        "AXTable": (0, 128, 128),          # Teal
        "default": (255, 255, 0)           # Yellow
    }

    def __init__(self):
        """Initialize visual debugger."""
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow not available. Install with: pip install Pillow")

        self.element_extractor = None
        if ELEMENT_EXTRACTOR_AVAILABLE:
            try:
                self.element_extractor = ElementExtractor()
            except Exception as e:
                logger.warning(f"ElementExtractor not available: {e}")

        self.system_controller = None
        if SYSTEM_CONTROLS_AVAILABLE:
            try:
                self.system_controller = SystemController()
            except Exception as e:
                logger.warning(f"SystemController not available: {e}")

        logger.info("Initialized visual debugger")

    def annotate_screenshot(
        self,
        screenshot_path: str,
        bounding_boxes: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        show_labels: bool = True,
        show_roles: bool = False,
        box_thickness: int = 2,
        font_size: int = 12
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Annotate a screenshot with bounding boxes.

        Args:
            screenshot_path: Path to screenshot image
            bounding_boxes: List of elements with BoundingBox info
            output_path: Where to save annotated image (default: temp file)
            show_labels: Show element names as labels
            show_roles: Show element roles in labels
            box_thickness: Thickness of bounding box lines
            font_size: Font size for labels

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            # Load image
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)

            # Try to load font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()

            # Draw each bounding box
            for element in bounding_boxes:
                bbox = element.get("BoundingBox")
                if not bbox:
                    continue

                # Extract coordinates
                x = bbox.get("x", 0)
                y = bbox.get("y", 0)
                width = bbox.get("width", 0)
                height = bbox.get("height", 0)

                # Get color based on role
                role = element.get("AXRole", "default")
                color = self.ELEMENT_COLORS.get(role, self.ELEMENT_COLORS["default"])

                # Draw rectangle
                draw.rectangle(
                    [(x, y), (x + width, y + height)],
                    outline=color,
                    width=box_thickness
                )

                # Draw label if requested
                if show_labels:
                    label_parts = []

                    if show_roles and role != "default":
                        label_parts.append(role)

                    # Add title or value
                    title = element.get("AXTitle") or element.get("AXValue") or element.get("AXDescription")
                    if title:
                        # Truncate long titles
                        title_str = str(title)
                        if len(title_str) > 30:
                            title_str = title_str[:27] + "..."
                        label_parts.append(title_str)

                    if label_parts:
                        label = ": ".join(label_parts)

                        # Draw label background
                        bbox_coords = draw.textbbox((x, y - font_size - 4), label, font=font)
                        draw.rectangle(bbox_coords, fill=(0, 0, 0, 180))

                        # Draw label text
                        draw.text((x, y - font_size - 4), label, fill=color, font=font)

            # Save annotated image
            if output_path is None:
                # Generate temp file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(tempfile.gettempdir(), f"annotated_{timestamp}.png")

            img.save(output_path)
            logger.info(f"Saved annotated screenshot to {output_path}")

            return True, output_path, None

        except Exception as e:
            error = f"Error annotating screenshot: {str(e)}"
            logger.error(error)
            return False, None, error

    def capture_and_annotate(
        self,
        app_name: Optional[str] = None,
        role_filter: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        show_labels: bool = True,
        show_roles: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Capture screenshot and annotate it with element bounding boxes.

        Args:
            app_name: Limit to specific app (None = all)
            role_filter: Only show specific element roles
            output_path: Where to save (default: temp file)
            show_labels: Show element labels
            show_roles: Show element roles

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            # Take screenshot
            if not self.system_controller:
                return False, None, "SystemController not available"

            screenshot_path = os.path.join(tempfile.gettempdir(), "debug_screenshot.png")
            success, path, error = self.system_controller.take_screenshot(
                filepath=screenshot_path,
                capture_type="screen"
            )

            if not success:
                return False, None, f"Failed to take screenshot: {error}"

            # Get bounding boxes
            if not self.element_extractor:
                return False, None, "ElementExtractor not available"

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
                    return False, None, f"App not found: {app_name}"

            bounding_boxes = self.element_extractor.get_bounding_boxes(pid, role_filter)

            if not bounding_boxes:
                logger.warning("No bounding boxes found")
                return False, None, "No elements with bounding boxes found"

            # Annotate
            success, annotated_path, error = self.annotate_screenshot(
                screenshot_path=screenshot_path,
                bounding_boxes=bounding_boxes,
                output_path=output_path,
                show_labels=show_labels,
                show_roles=show_roles
            )

            # Clean up temp screenshot
            try:
                os.remove(screenshot_path)
            except:
                pass

            return success, annotated_path, error

        except Exception as e:
            error = f"Error in capture_and_annotate: {str(e)}"
            logger.error(error)
            return False, None, error

    def highlight_element(
        self,
        screenshot_path: str,
        element_name: str,
        role: Optional[str] = None,
        app_name: Optional[str] = None,
        output_path: Optional[str] = None,
        highlight_color: Tuple[int, int, int] = (255, 0, 0),
        box_thickness: int = 4
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Highlight a specific element on a screenshot.

        Args:
            screenshot_path: Path to screenshot
            element_name: Element name to highlight
            role: Element role (optional)
            app_name: Limit to app (optional)
            output_path: Where to save
            highlight_color: RGB color for highlight
            box_thickness: Thickness of highlight box

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            if not self.element_extractor:
                return False, None, "ElementExtractor not available"

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

            # Get all elements
            all_elements = self.element_extractor.extract_all_elements_flat(
                max_depth=15,
                role_filter=[role] if role else None
            )

            # Filter by name
            matching_elements = [
                e for e in all_elements
                if (e.get("AXTitle") == element_name or
                    e.get("AXValue") == element_name or
                    e.get("AXDescription") == element_name)
            ]

            if not matching_elements:
                return False, None, f"Element not found: {element_name}"

            # Load image
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)

            # Highlight matching elements
            for element in matching_elements:
                bbox = element.get("BoundingBox")
                if not bbox:
                    continue

                x = bbox.get("x", 0)
                y = bbox.get("y", 0)
                width = bbox.get("width", 0)
                height = bbox.get("height", 0)

                # Draw thick highlight box
                draw.rectangle(
                    [(x - 2, y - 2), (x + width + 2, y + height + 2)],
                    outline=highlight_color,
                    width=box_thickness
                )

            # Save
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(tempfile.gettempdir(), f"highlighted_{timestamp}.png")

            img.save(output_path)
            logger.info(f"Saved highlighted screenshot to {output_path}")

            return True, output_path, None

        except Exception as e:
            error = f"Error highlighting element: {str(e)}"
            logger.error(error)
            return False, None, error

    def visualize_element_tree(
        self,
        app_name: Optional[str] = None,
        max_depth: int = 5,
        output_path: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a text visualization of the UI element tree.

        Args:
            app_name: Limit to specific app
            max_depth: Maximum tree depth
            output_path: Where to save text file (default: temp)

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            if not self.element_extractor:
                return False, None, "ElementExtractor not available"

            # Extract tree
            structure = self.element_extractor.extract_screen_structure(
                app_name=app_name,
                include_all_properties=False
            )

            # Generate text representation
            lines = []
            lines.append(f"UI Element Tree for: {app_name or 'All Applications'}")
            lines.append("=" * 80)
            lines.append("")

            def format_tree(node: Dict[str, Any], depth: int = 0, prefix: str = ""):
                if depth > max_depth:
                    return

                # Format node info
                role = node.get("AXRole", "Unknown")
                title = node.get("AXTitle", "")

                line = f"{prefix}├─ {role}"
                if title:
                    line += f": {title}"

                lines.append(line)

                # Process children
                children = node.get("children", [])
                for i, child in enumerate(children):
                    is_last = (i == len(children) - 1)
                    child_prefix = prefix + ("   " if is_last else "│  ")
                    format_tree(child, depth + 1, child_prefix)

            # Format tree
            tree = structure.get("element_tree", {})
            if tree:
                format_tree(tree)
            else:
                lines.append("No element tree available")

            # Save to file
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(tempfile.gettempdir(), f"element_tree_{timestamp}.txt")

            with open(output_path, 'w') as f:
                f.write('\n'.join(lines))

            logger.info(f"Saved element tree to {output_path}")

            return True, output_path, None

        except Exception as e:
            error = f"Error visualizing element tree: {str(e)}"
            logger.error(error)
            return False, None, error


# Convenience functions

def capture_annotated_screenshot(
    app_name: Optional[str] = None,
    output_path: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Capture and annotate screenshot (convenience function).

    Args:
        app_name: Limit to app
        output_path: Where to save

    Returns:
        Tuple of (success, path, error)
    """
    if not PIL_AVAILABLE:
        return False, None, "PIL/Pillow not available"

    try:
        debugger = VisualDebugger()
        return debugger.capture_and_annotate(app_name, output_path=output_path)
    except Exception as e:
        return False, None, str(e)


def highlight_element_on_screen(
    element_name: str,
    role: Optional[str] = None,
    app_name: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Capture screen and highlight specific element (convenience function).

    Args:
        element_name: Element to highlight
        role: Element role
        app_name: Limit to app

    Returns:
        Tuple of (success, path, error)
    """
    if not PIL_AVAILABLE:
        return False, None, "PIL/Pillow not available"

    try:
        debugger = VisualDebugger()

        # Take screenshot first
        from system_controls import SystemController
        controller = SystemController()

        screenshot_path = os.path.join(tempfile.gettempdir(), "temp_screenshot.png")
        success, path, error = controller.take_screenshot(filepath=screenshot_path)

        if not success:
            return False, None, f"Screenshot failed: {error}"

        # Highlight element
        result = debugger.highlight_element(
            screenshot_path=screenshot_path,
            element_name=element_name,
            role=role,
            app_name=app_name
        )

        # Clean up temp screenshot
        try:
            os.remove(screenshot_path)
        except:
            pass

        return result

    except Exception as e:
        return False, None, str(e)
