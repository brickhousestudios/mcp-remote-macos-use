"""
System controls for macOS (clipboard, volume, brightness, power, etc.).

Provides high-level system control functions using native macOS APIs
and AppleScript where appropriate.
"""

import logging
import subprocess
from typing import Optional, Tuple, Dict, Any
import os

try:
    from AppKit import NSPasteboard, NSStringPboardType, NSPasteboardTypeString
    from Cocoa import NSURL, NSData
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False

# Configure logging
logger = logging.getLogger('system_controls')
logger.setLevel(logging.DEBUG)


class ClipboardManager:
    """
    Manage system clipboard operations.

    Supports reading and writing text, URLs, and file paths.
    """

    def __init__(self):
        """Initialize clipboard manager."""
        if not COCOA_AVAILABLE:
            raise ImportError("Cocoa framework not available. Install pyobjc-framework-Cocoa")

        self.pasteboard = NSPasteboard.generalPasteboard()
        logger.info("Initialized clipboard manager")

    def read_text(self) -> Optional[str]:
        """
        Read text from clipboard.

        Returns:
            Clipboard text or None
        """
        try:
            # Try modern API first
            text = self.pasteboard.stringForType_(NSPasteboardTypeString)

            # Fallback to older API
            if text is None:
                text = self.pasteboard.stringForType_(NSStringPboardType)

            return text
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")
            return None

    def write_text(self, text: str) -> bool:
        """
        Write text to clipboard.

        Args:
            text: Text to write

        Returns:
            bool: True if successful
        """
        try:
            self.pasteboard.clearContents()
            success = self.pasteboard.setString_forType_(text, NSPasteboardTypeString)

            if not success:
                # Try older API
                success = self.pasteboard.setString_forType_(text, NSStringPboardType)

            return success
        except Exception as e:
            logger.error(f"Error writing clipboard: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear the clipboard.

        Returns:
            bool: True if successful
        """
        try:
            self.pasteboard.clearContents()
            return True
        except Exception as e:
            logger.error(f"Error clearing clipboard: {e}")
            return False

    def get_contents_info(self) -> Dict[str, Any]:
        """
        Get information about clipboard contents.

        Returns:
            Dictionary with clipboard info
        """
        try:
            types = self.pasteboard.types()
            return {
                "has_content": len(types) > 0,
                "types": [str(t) for t in types] if types else [],
                "text_available": NSPasteboardTypeString in types or NSStringPboardType in types,
            }
        except Exception as e:
            logger.error(f"Error getting clipboard info: {e}")
            return {"error": str(e)}


class SystemController:
    """
    Control system-level functions (volume, brightness, power, etc.).
    """

    def __init__(self):
        """Initialize system controller."""
        logger.info("Initialized system controller")

    def set_volume(self, level: int) -> Tuple[bool, Optional[str]]:
        """
        Set system volume.

        Args:
            level: Volume level (0-100)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Clamp to valid range
            level = max(0, min(100, level))

            # Use osascript for cross-version compatibility
            result = subprocess.run(
                ['osascript', '-e', f'set volume output volume {level}'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"Set volume to {level}")
                return True, None
            else:
                error = result.stderr.strip()
                logger.error(f"Failed to set volume: {error}")
                return False, error

        except Exception as e:
            error = f"Error setting volume: {str(e)}"
            logger.error(error)
            return False, error

    def get_volume(self) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Get current system volume.

        Returns:
            Tuple of (success, volume_level, error_message)
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', 'get volume settings'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse: "output volume:75, input volume:50, ..."
                output = result.stdout.strip()
                for part in output.split(','):
                    if 'output volume' in part:
                        volume = int(part.split(':')[1].strip())
                        return True, volume, None

                return False, None, "Could not parse volume"
            else:
                return False, None, result.stderr.strip()

        except Exception as e:
            return False, None, str(e)

    def mute(self) -> Tuple[bool, Optional[str]]:
        """
        Mute system volume.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', 'set volume output muted true'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info("Muted volume")
                return True, None
            else:
                return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def unmute(self) -> Tuple[bool, Optional[str]]:
        """
        Unmute system volume.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', 'set volume output muted false'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info("Unmuted volume")
                return True, None
            else:
                return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def set_brightness(self, level: float) -> Tuple[bool, Optional[str]]:
        """
        Set display brightness.

        Args:
            level: Brightness level (0.0-1.0)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Clamp to valid range
            level = max(0.0, min(1.0, level))

            # Use brightness command if available
            result = subprocess.run(
                ['brightness', str(level)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"Set brightness to {level}")
                return True, None
            else:
                # Try alternative method using CoreGraphics
                try:
                    import Quartz
                    # This requires special permissions
                    # Would need to implement via IOKit
                    return False, "Brightness control requires additional setup"
                except:
                    return False, "Brightness control not available"

        except FileNotFoundError:
            return False, "brightness command not found. Install with: brew install brightness"
        except Exception as e:
            return False, str(e)

    def lock_screen(self) -> Tuple[bool, Optional[str]]:
        """
        Lock the screen.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Use pmset to lock screen
            result = subprocess.run(
                ['/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession', '-suspend'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info("Locked screen")
                return True, None
            else:
                # Alternative method
                result = subprocess.run(
                    ['osascript', '-e', 'tell application "System Events" to keystroke "q" using {command down, control down}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0, result.stderr.strip() if result.returncode != 0 else None

        except Exception as e:
            return False, str(e)

    def sleep(self) -> Tuple[bool, Optional[str]]:
        """
        Put computer to sleep.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            result = subprocess.run(
                ['pmset', 'sleepnow'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info("Put computer to sleep")
                return True, None
            else:
                return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def restart(self, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Restart the computer.

        Args:
            force: Force restart without saving

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if force:
                cmd = ['osascript', '-e', 'tell app "System Events" to restart']
            else:
                cmd = ['osascript', '-e', 'tell application "System Events" to restart']

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.warning("Computer restart initiated")
                return True, None
            else:
                return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def shutdown(self, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Shutdown the computer.

        Args:
            force: Force shutdown without saving

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if force:
                cmd = ['osascript', '-e', 'tell app "System Events" to shut down']
            else:
                cmd = ['osascript', '-e', 'tell application "System Events" to shut down']

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.warning("Computer shutdown initiated")
                return True, None
            else:
                return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def logout(self) -> Tuple[bool, Optional[str]]:
        """
        Log out current user.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to log out'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info("User logout initiated")
                return True, None
            else:
                return False, result.stderr.strip()

        except Exception as e:
            return False, str(e)

    def take_screenshot(
        self,
        filepath: Optional[str] = None,
        capture_type: str = "screen"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Take a screenshot.

        Args:
            filepath: Where to save (default: ~/Desktop/Screenshot.png)
            capture_type: "screen", "window", or "selection"

        Returns:
            Tuple of (success, filepath, error_message)
        """
        try:
            if filepath is None:
                filepath = os.path.expanduser("~/Desktop/Screenshot.png")

            # Use screencapture command
            cmd = ['screencapture']

            if capture_type == "window":
                cmd.append('-w')  # Capture window
            elif capture_type == "selection":
                cmd.append('-s')  # Interactive selection
            # else: full screen (default)

            cmd.append(filepath)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # Longer timeout for interactive selection
            )

            if result.returncode == 0 and os.path.exists(filepath):
                logger.info(f"Screenshot saved to {filepath}")
                return True, filepath, None
            else:
                return False, None, result.stderr.strip() or "Screenshot failed"

        except Exception as e:
            return False, None, str(e)

    def get_battery_info(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Get battery information (for laptops).

        Returns:
            Tuple of (success, battery_info, error_message)
        """
        try:
            result = subprocess.run(
                ['pmset', '-g', 'batt'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                output = result.stdout
                info = {"raw": output}

                # Parse output
                for line in output.split('\n'):
                    if '%' in line:
                        # Extract percentage
                        try:
                            percent = int(line.split('%')[0].split()[-1])
                            info['percentage'] = percent
                        except:
                            pass

                        # Check if charging
                        info['charging'] = 'AC Power' in line or 'charging' in line.lower()

                return True, info, None
            else:
                return False, None, result.stderr.strip()

        except Exception as e:
            return False, None, str(e)


# Convenience functions

def get_clipboard_text() -> Optional[str]:
    """
    Get text from clipboard (convenience function).

    Returns:
        Clipboard text or None
    """
    if not COCOA_AVAILABLE:
        return None

    try:
        manager = ClipboardManager()
        return manager.read_text()
    except Exception as e:
        logger.error(f"Error getting clipboard: {e}")
        return None


def set_clipboard_text(text: str) -> bool:
    """
    Set clipboard text (convenience function).

    Args:
        text: Text to set

    Returns:
        bool: True if successful
    """
    if not COCOA_AVAILABLE:
        return False

    try:
        manager = ClipboardManager()
        return manager.write_text(text)
    except Exception as e:
        logger.error(f"Error setting clipboard: {e}")
        return False


def check_cocoa_available() -> bool:
    """
    Check if Cocoa framework is available.

    Returns:
        bool: True if available
    """
    return COCOA_AVAILABLE
