# MCP Server Setup Guide

This guide will help you configure the MCP Remote macOS Control server with Claude Desktop.

## 🚀 Quick Setup (Local macOS Control)

### Step 1: Install Dependencies

```bash
cd /path/to/mcp-remote-macos-use
pip install -e .
```

### Step 2: Grant Accessibility Permissions

**IMPORTANT:** The MCP server needs Accessibility permissions to control your Mac.

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **+** button
3. Add your **Terminal** or **Python** app
4. Enable the toggle

### Step 3: Create Environment File (Optional for VNC)

For **local control**, you don't need VNC. Skip this step.

For **remote control via VNC**:
```bash
cp .env.example .env
# Edit .env with your VNC settings
nano .env
```

### Step 4: Configure Claude Desktop

#### Option A: Using uvx (Recommended)

Add this to your Claude Desktop config file:

**macOS/Linux:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "macos-control": {
      "command": "uvx",
      "args": [
        "mcp-remote-macos-use"
      ],
      "env": {
        "MACOS_HOST": "localhost"
      }
    }
  }
}
```

#### Option B: Using Python Directly

```json
{
  "mcpServers": {
    "macos-control": {
      "command": "python",
      "args": [
        "-m",
        "mcp_remote_macos_use.server"
      ],
      "cwd": "/absolute/path/to/mcp-remote-macos-use",
      "env": {
        "MACOS_HOST": "localhost",
        "PYTHONPATH": "/absolute/path/to/mcp-remote-macos-use/src"
      }
    }
  }
}
```

#### Option C: Using uv run

```json
{
  "mcpServers": {
    "macos-control": {
      "command": "uv",
      "args": [
        "run",
        "mcp-remote-macos-use"
      ],
      "cwd": "/absolute/path/to/mcp-remote-macos-use"
    }
  }
}
```

### Step 5: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Look for the 🔌 icon in the bottom right - it should show "macos-control" is connected

## ✅ Test It Works

Once connected, try these commands in Claude Desktop:

### Test 1: Take Screenshot
```
Take a screenshot of my Mac screen
```

### Test 2: Open Safari
```
Open Safari on my Mac
```

### Test 3: List Windows
```
List all open windows on my Mac
```

### Test 4: Navigate to Website
```
Go to looperman.com on my Mac
```

### Test 5: Element Detection
```
Find all buttons on the screen
```

## 🎯 Available Tools (42 Total)

### VNC Control (8 tools)
- `remote_macos_get_screen` - Take screenshot
- `remote_macos_mouse_click` - Click at coordinates
- `remote_macos_mouse_double_click` - Double-click
- `remote_macos_mouse_move` - Move mouse
- `remote_macos_mouse_scroll` - Scroll
- `remote_macos_mouse_drag_n_drop` - Drag and drop
- `remote_macos_send_keys` - Type text/special keys
- `remote_macos_open_application` - Open apps

### Semantic UI Control (6 tools)
- `macos_find_element` - Find UI elements by name/role
- `macos_click_element` - Click elements semantically
- `macos_type_text_native` - Type into focused element
- `macos_get_focused_app` - Get focused app
- `macos_launch_app_native` - Launch app
- `macos_get_capabilities` - Get available capabilities

### AppleScript & System (8 tools)
- `execute_applescript` - Run AppleScript
- `applescript_tell_app` - Control apps via AppleScript
- `read_clipboard` - Read clipboard content
- `write_clipboard` - Write to clipboard
- `set_volume` - Set system volume
- `get_volume` - Get system volume
- `system_action` - Lock/sleep/logout
- `batch_operations` - Run multiple operations

### Element Extraction (6 tools)
- `extract_screen_structure` - Get full UI hierarchy
- `extract_all_elements` - Get all elements flat
- `get_bounding_boxes` - Get element positions
- `extract_form_fields` - Find all form fields
- `extract_clickable_elements` - Find all clickable items
- `extract_text_content` - Extract all text

### Smart Waiting (2 tools)
- `wait_for_element` - Wait for element to appear
- `wait_for_element_property` - Wait for property change

### Visual Debugging (3 tools)
- `capture_annotated_screenshot` - Screenshot with boxes
- `highlight_element` - Highlight specific element
- `visualize_element_tree` - ASCII UI tree

### Window Management (5 tools)
- `list_windows` - List all windows
- `resize_window` - Resize window
- `move_window` - Move window
- `window_action` - Minimize/maximize/close
- `switch_to_window` - Switch to window

### Advanced Interactions (4 tools)
- `right_click` - Right-click menu
- `select_text` - Select text
- `copy_cut_selection` - Copy/cut
- `gesture` - Multi-finger gestures

## 🔧 Troubleshooting

### Issue: "Server not connected"
- Check Claude Desktop config syntax (valid JSON)
- Verify absolute paths in config
- Check Accessibility permissions
- Restart Claude Desktop

### Issue: "Permission denied"
- Grant Accessibility permissions (Step 2)
- May need to add Python executable specifically

### Issue: "Module not found"
- Make sure you installed: `pip install -e .`
- Check PYTHONPATH in config

### Issue: "Tools not appearing"
- Restart Claude Desktop
- Check MCP server logs
- Verify config file location

## 📝 Example Workflows

### Workflow 1: Open Website
```
1. Open Safari
2. Navigate to github.com
3. Take a screenshot
```

### Workflow 2: Window Management
```
1. List all windows
2. Resize Safari to 1200x800
3. Move it to top-left corner
```

### Workflow 3: Text Automation
```
1. Open TextEdit
2. Type "Hello World"
3. Select all text
4. Copy to clipboard
```

### Workflow 4: UI Analysis
```
1. Take annotated screenshot showing all elements
2. Extract all clickable buttons
3. List all text on screen
```

## 🎬 Advanced: Remote Control via VNC

If you want to control a **remote Mac** (not the local one):

1. Enable **Screen Sharing** on target Mac:
   - System Settings → Sharing → Screen Sharing

2. Configure `.env`:
   ```
   MACOS_HOST=192.168.1.100  # Target Mac IP
   MACOS_PORT=5900
   MACOS_VNC_PASSWORD=your_password
   ```

3. Update Claude Desktop config to load .env:
   ```json
   {
     "mcpServers": {
       "macos-control": {
         "command": "python",
         "args": ["-m", "mcp_remote_macos_use.server"],
         "cwd": "/path/to/mcp-remote-macos-use",
         "env": {
           "MACOS_HOST": "192.168.1.100",
           "MACOS_PORT": "5900",
           "MACOS_VNC_PASSWORD": "your_password"
         }
       }
     }
   }
   ```

## 🎯 Pro Tips

1. **Use semantic tools when possible** - They're faster and more reliable than coordinate-based clicking

2. **Wait for elements** - Use `wait_for_element` instead of fixed delays

3. **Debug with visual tools** - Use `capture_annotated_screenshot` to see what's on screen

4. **Batch operations** - Group multiple actions for better performance

5. **Window management** - Organize your workspace before automation

## 📚 Additional Resources

- [README.md](README.md) - Project overview
- [NATIVE_MACOS_CONTROL.md](NATIVE_MACOS_CONTROL.md) - Native API details
- [PERFORMANCE_IMPROVEMENTS.md](PERFORMANCE_IMPROVEMENTS.md) - Performance tips

## 🆘 Need Help?

Open an issue on GitHub with:
- Claude Desktop config (remove sensitive data)
- Error messages
- What you're trying to do
- macOS version
