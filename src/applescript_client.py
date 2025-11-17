"""
AppleScript integration for advanced macOS automation.

Allows executing AppleScripts for complex tasks that would be difficult
with UI automation alone (file operations, app-specific automation, etc.).
"""

import logging
import subprocess
from typing import Optional, Dict, Any, List, Tuple
import json
import tempfile
import os

# Configure logging
logger = logging.getLogger('applescript_client')
logger.setLevel(logging.DEBUG)


class AppleScriptClient:
    """
    Execute AppleScripts for advanced macOS automation.

    Supports:
    - Direct script execution
    - Pre-defined script templates
    - Application-specific automation
    - File operations
    - System integration
    """

    def __init__(self):
        """Initialize AppleScript client."""
        self.check_availability()
        logger.info("Initialized AppleScript client")

    @staticmethod
    def check_availability() -> bool:
        """
        Check if osascript is available.

        Returns:
            bool: True if available
        """
        try:
            result = subprocess.run(
                ['which', 'osascript'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"AppleScript not available: {e}")
            return False

    def execute_script(
        self,
        script: str,
        timeout: int = 30
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Execute an AppleScript.

        Args:
            script: AppleScript code to execute
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, output, error)
        """
        try:
            # Execute using osascript
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                logger.debug(f"Script executed successfully")
                return True, result.stdout.strip(), None
            else:
                logger.error(f"Script execution failed: {result.stderr}")
                return False, None, result.stderr.strip()

        except subprocess.TimeoutExpired:
            error = f"Script execution timed out after {timeout}s"
            logger.error(error)
            return False, None, error
        except Exception as e:
            error = f"Script execution error: {str(e)}"
            logger.error(error)
            return False, None, error

    def execute_script_file(
        self,
        script_path: str,
        timeout: int = 30
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Execute an AppleScript file.

        Args:
            script_path: Path to .scpt or .applescript file
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, output, error)
        """
        try:
            result = subprocess.run(
                ['osascript', script_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return True, result.stdout.strip(), None
            else:
                return False, None, result.stderr.strip()

        except Exception as e:
            return False, None, str(e)

    # Pre-defined script templates

    def get_app_info(self, app_name: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Get information about an application.

        Args:
            app_name: Application name

        Returns:
            Tuple of (success, info_dict, error)
        """
        script = f'''
        tell application "System Events"
            if exists application process "{app_name}" then
                tell application process "{app_name}"
                    set appInfo to {{}}
                    set appInfo to appInfo & {{name:name, visible:visible, frontmost:frontmost}}
                    return appInfo
                end tell
            else
                return "not_running"
            end if
        end tell
        '''

        success, output, error = self.execute_script(script)

        if success and output != "not_running":
            # Parse the output (basic parsing)
            return True, {"raw": output}, None
        elif output == "not_running":
            return True, {"running": False}, None
        else:
            return False, None, error

    def tell_app(
        self,
        app_name: str,
        command: str,
        timeout: int = 30
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send a command to a specific application.

        Args:
            app_name: Application name
            command: AppleScript command(s) to send
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, output, error)
        """
        script = f'''
        tell application "{app_name}"
            {command}
        end tell
        '''

        return self.execute_script(script, timeout)

    def open_url(self, url: str, browser: str = "Safari") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Open a URL in a specific browser.

        Args:
            url: URL to open
            browser: Browser name (default: Safari)

        Returns:
            Tuple of (success, output, error)
        """
        script = f'''
        tell application "{browser}"
            activate
            open location "{url}"
        end tell
        '''

        return self.execute_script(script)

    def send_message(
        self,
        recipient: str,
        message: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send an iMessage.

        Args:
            recipient: Phone number or email
            message: Message text

        Returns:
            Tuple of (success, output, error)
        """
        # Escape quotes in message
        message = message.replace('"', '\\"')

        script = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            set targetBuddy to buddy "{recipient}" of targetService
            send "{message}" to targetBuddy
        end tell
        '''

        return self.execute_script(script)

    def get_finder_selection(self) -> Tuple[bool, Optional[List[str]], Optional[str]]:
        """
        Get the currently selected files in Finder.

        Returns:
            Tuple of (success, file_paths, error)
        """
        script = '''
        tell application "Finder"
            set selectedItems to selection as alias list
            set pathList to {}
            repeat with anItem in selectedItems
                set end of pathList to POSIX path of anItem
            end repeat
            return pathList
        end tell
        '''

        success, output, error = self.execute_script(script)

        if success and output:
            # Parse the output
            paths = output.split(', ')
            return True, paths, None
        else:
            return False, None, error

    def set_volume(self, level: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Set system volume.

        Args:
            level: Volume level (0-100)

        Returns:
            Tuple of (success, output, error)
        """
        level = max(0, min(100, level))  # Clamp to 0-100

        script = f'set volume output volume {level}'

        return self.execute_script(script)

    def get_volume(self) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Get system volume.

        Returns:
            Tuple of (success, volume_level, error)
        """
        script = 'get volume settings'

        success, output, error = self.execute_script(script)

        if success and output:
            # Parse output to extract volume
            # Output format: "output volume:75, input volume:50, ..."
            try:
                for part in output.split(','):
                    if 'output volume' in part:
                        volume = int(part.split(':')[1].strip())
                        return True, volume, None
            except:
                pass

        return False, None, error or "Failed to parse volume"

    def display_notification(
        self,
        message: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        sound: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Display a macOS notification.

        Args:
            message: Notification message
            title: Notification title (optional)
            subtitle: Notification subtitle (optional)
            sound: Sound name (optional, e.g., "Glass", "Hero")

        Returns:
            Tuple of (success, output, error)
        """
        script_parts = [f'display notification "{message}"']

        if title:
            script_parts.append(f'with title "{title}"')
        if subtitle:
            script_parts.append(f'subtitle "{subtitle}"')
        if sound:
            script_parts.append(f'sound name "{sound}"')

        script = ' '.join(script_parts)

        return self.execute_script(script)

    def display_dialog(
        self,
        message: str,
        title: Optional[str] = None,
        buttons: Optional[List[str]] = None,
        default_button: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Display a dialog box.

        Args:
            message: Dialog message
            title: Dialog title (optional)
            buttons: List of button labels (optional)
            default_button: Default button label (optional)

        Returns:
            Tuple of (success, button_clicked, error)
        """
        script_parts = [f'display dialog "{message}"']

        if title:
            script_parts.append(f'with title "{title}"')
        if buttons:
            buttons_str = ', '.join(f'"{btn}"' for btn in buttons)
            script_parts.append(f'buttons {{{buttons_str}}}')
        if default_button:
            script_parts.append(f'default button "{default_button}"')

        script = ' '.join(script_parts)

        success, output, error = self.execute_script(script)

        # Extract button clicked from output
        if success and output:
            # Output format: "button returned:OK"
            try:
                button = output.split(':')[1].strip()
                return True, button, None
            except:
                return True, output, None

        return False, None, error

    def speak_text(self, text: str, voice: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Use text-to-speech to speak text.

        Args:
            text: Text to speak
            voice: Voice name (optional, e.g., "Alex", "Samantha")

        Returns:
            Tuple of (success, output, error)
        """
        if voice:
            script = f'say "{text}" using "{voice}"'
        else:
            script = f'say "{text}"'

        return self.execute_script(script)

    def run_shell_command(
        self,
        command: str,
        as_admin: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Run a shell command via AppleScript.

        Args:
            command: Shell command to run
            as_admin: Run with administrator privileges

        Returns:
            Tuple of (success, output, error)
        """
        if as_admin:
            script = f'do shell script "{command}" with administrator privileges'
        else:
            script = f'do shell script "{command}"'

        return self.execute_script(script)


# Convenience functions

def execute_applescript(script: str, timeout: int = 30) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Execute an AppleScript (convenience function).

    Args:
        script: AppleScript code
        timeout: Timeout in seconds

    Returns:
        Tuple of (success, output, error)
    """
    client = AppleScriptClient()
    return client.execute_script(script, timeout)


def check_applescript_available() -> bool:
    """
    Check if AppleScript is available.

    Returns:
        bool: True if available
    """
    return AppleScriptClient.check_availability()
