# CLAUDE.md - AI Assistant Development Guide

**Comprehensive guide for AI assistants working on MCP Remote macOS Use**

Last Updated: 2025-11-18

---

## 📚 Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Architecture & Design Patterns](#architecture--design-patterns)
4. [Development Workflows](#development-workflows)
5. [Code Conventions](#code-conventions)
6. [Testing Guidelines](#testing-guidelines)
7. [Git Workflow](#git-workflow)
8. [Common Tasks](#common-tasks)
9. [Documentation Standards](#documentation-standards)
10. [Troubleshooting](#troubleshooting)

---

## 📖 Project Overview

### What is MCP Remote macOS Use?

A Model Context Protocol (MCP) server that enables AI assistants to remotely control macOS systems via VNC and native Accessibility APIs. Provides 42+ tools for complete macOS automation.

### Key Components

1. **MCP Server** - Exposes 42 tools via MCP protocol
2. **VNC Client** - Remote desktop control via VNC
3. **Accessibility API** - Native macOS UI control (local only)
4. **Automation Tools** - Window management, text selection, gestures
5. **Docker Support** - Run macOS VMs in containers
6. **Electron App** - Standalone VNC viewer with beautiful UI

### Technology Stack

- **Python 3.10+** - Core server and automation
- **MCP Protocol** - Tool exposure to AI assistants
- **VNC/RFB** - Remote desktop protocol
- **PyObjC** - macOS native API bindings
- **QEMU/KVM** - macOS virtualization in Docker
- **Electron** - Desktop VNC viewer app
- **noVNC** - HTML5 VNC client

---

## 🏗️ Repository Structure

```
mcp-remote-macos-use/
├── src/                           # Python source code
│   ├── mcp_remote_macos_use/     # MCP server package
│   │   ├── server.py             # Main MCP server (42 tools registered)
│   │   ├── livekit_handler.py    # LiveKit integration
│   │   └── __init__.py
│   │
│   ├── vnc_client.py             # VNC/RFB client implementation
│   ├── vnc_connection_manager.py # Connection pooling (10-50x faster)
│   ├── action_handlers.py        # VNC-based tools (8 handlers)
│   │
│   ├── accessibility_client.py   # macOS Accessibility API
│   ├── semantic_handlers.py      # Semantic UI tools (6 handlers)
│   ├── control_router.py         # VNC/Accessibility routing logic
│   │
│   ├── applescript_client.py     # AppleScript execution
│   ├── system_controls.py        # Clipboard, volume, system actions
│   ├── element_extractor.py      # UI element extraction & bounding boxes
│   ├── advanced_handlers.py      # All advanced tools (24 handlers)
│   │
│   ├── smart_waiting.py          # Wait for elements, polling, retry
│   ├── visual_debugging.py       # Annotated screenshots, highlighting
│   ├── window_manager.py         # Window resize, move, minimize, etc.
│   ├── advanced_interactions.py  # Right-click, text selection, gestures
│   │
│   └── mlx_vision.py             # MLX vision (future ML features)
│
├── electron-app/                 # Standalone VNC viewer
│   ├── main.js                   # Electron main process
│   ├── preload.js                # IPC security bridge
│   ├── src/
│   │   ├── index.html            # UI
│   │   ├── renderer.js           # VNC connection logic
│   │   └── styles.css            # Modern gradient UI
│   └── package.json              # Build config
│
├── docker/                       # Docker utilities
│   ├── start-macos-vm.sh        # QEMU VM startup
│   └── docker-commands.sh        # Helper commands
│
├── tests/                        # Test suite
│   ├── test_server.py
│   ├── test_vnc_client.py
│   └── test_action_handlers.py
│
├── docs/                         # Documentation
│   ├── README.md                 # Main documentation
│   ├── MCP_SETUP.md             # MCP server setup
│   ├── DOCKER_SETUP.md          # Docker & VM guide
│   ├── NATIVE_MACOS_CONTROL.md  # Accessibility API guide
│   └── PERFORMANCE_IMPROVEMENTS.md
│
├── Dockerfile                    # Production server
├── Dockerfile.vm                 # macOS VM + server
├── docker-compose.yml           # 3 profiles: basic, vm, dev
├── pyproject.toml               # Python dependencies
├── setup_mcp.sh                 # Automated setup script
└── .env.example                 # Configuration template
```

### File Organization Principles

1. **Separation by Capability**
   - VNC tools → `action_handlers.py`
   - Accessibility tools → `semantic_handlers.py`
   - Advanced features → `advanced_handlers.py`

2. **Client Libraries**
   - Each automation method has a client: `vnc_client.py`, `accessibility_client.py`, etc.

3. **Single Registration Point**
   - All tools registered in `server.py`
   - Handlers imported and connected to tool calls

4. **Documentation Co-location**
   - Each major feature has a markdown doc
   - In-code docstrings for all public functions

---

## 🏛️ Architecture & Design Patterns

### 1. MCP Tool Architecture

```
Client (Claude Desktop)
    ↓ MCP Protocol
server.py (@server.list_tools, @server.call_tool)
    ↓ Route by tool name
Handler Functions (handle_*, returns list[TextContent])
    ↓ Call client libraries
Client Libraries (VNCClient, AccessibilityClient, etc.)
    ↓ Execute actions
Target macOS System
```

### 2. Connection Pooling Pattern

**File:** `vnc_connection_manager.py`

```python
# Before (2-5 seconds per operation):
vnc = VNCClient(host, port, password)
vnc.connect()
vnc.click(x, y)
vnc.close()

# After (0.1-0.5 seconds):
manager = GlobalVNCConnectionPool.get_instance()
with manager.get_connection() as vnc:
    vnc.click(x, y)
```

**Performance Gain:** 10-50x faster for subsequent operations

### 3. Control Router Pattern

**File:** `control_router.py`

Routes between VNC (remote) and Accessibility API (local):

```python
def _determine_control_method():
    if is_local and prefer_native and accessibility_available:
        return ControlMethod.ACCESSIBILITY  # 10-100x faster
    return ControlMethod.VNC
```

### 4. Handler Pattern

All MCP tools follow this pattern:

```python
def handle_tool_name(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Tool description.

    Args:
        arguments: Dict with:
            - param1: Description
            - param2: Description

    Returns:
        Success/error message
    """
    # 1. Validate availability
    if not FEATURE_AVAILABLE:
        return [types.TextContent(type="text", text="Feature not available")]

    # 2. Extract and validate arguments
    param1 = arguments.get("param1")
    if not param1:
        raise ValueError("param1 is required")

    # 3. Execute action
    try:
        client = FeatureClient()
        success, result, error = client.do_action(param1)

        # 4. Return formatted response
        if success:
            return [types.TextContent(type="text", text=f"✓ Success: {result}")]
        else:
            return [types.TextContent(type="text", text=f"✗ Error: {error}")]

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
```

### 5. Client Library Pattern

Each automation method has a client library:

```python
class FeatureClient:
    """Client for feature automation."""

    def __init__(self):
        """Initialize client with error handling."""
        if not FEATURE_AVAILABLE:
            raise ImportError("Feature not available")
        # Initialize resources

    def do_action(self, param: str) -> Tuple[bool, Any, Optional[str]]:
        """
        Perform action.

        Returns:
            Tuple of (success, result, error_message)
        """
        try:
            # Perform action
            result = self._internal_action(param)
            return True, result, None
        except Exception as e:
            return False, None, str(e)
```

### 6. Availability Checking

**Pattern:** Check feature availability at module level

```python
# At top of file
try:
    from Cocoa import NSWorkspace
    FEATURE_AVAILABLE = True
except ImportError:
    FEATURE_AVAILABLE = False

# In handler
if not FEATURE_AVAILABLE:
    return [types.TextContent(type="text", text="Feature requires macOS")]
```

---

## 🔄 Development Workflows

### Adding a New MCP Tool

**Step-by-step process:**

1. **Create Client Library** (if needed)

   File: `src/new_feature.py`
   ```python
   class NewFeatureClient:
       def __init__(self):
           # Initialize

       def do_action(self, param) -> Tuple[bool, Any, Optional[str]]:
           # Implementation
   ```

2. **Create Handler Function**

   File: `src/advanced_handlers.py` (or create new handler file)
   ```python
   def handle_new_feature(arguments: dict[str, Any]) -> list[types.TextContent]:
       # Implementation following handler pattern
   ```

3. **Register Tool in Server**

   File: `src/mcp_remote_macos_use/server.py`

   a. Import handler at top:
   ```python
   from advanced_handlers import (
       # ... existing imports
       handle_new_feature
   )
   ```

   b. Add tool definition in `@server.list_tools()`:
   ```python
   types.Tool(
       name="new_feature",
       description="Clear description of what it does",
       inputSchema={
           "type": "object",
           "properties": {
               "param1": {"type": "string", "description": "Description"}
           },
           "required": ["param1"]
       }
   )
   ```

   c. Add handler call in `@server.call_tool()`:
   ```python
   elif name == "new_feature" and FEATURE_AVAILABLE:
       return handle_new_feature(arguments)
   ```

4. **Test Compilation**
   ```bash
   python3 -m py_compile src/new_feature.py
   python3 -m py_compile src/advanced_handlers.py
   python3 -m py_compile src/mcp_remote_macos_use/server.py
   ```

5. **Update Documentation**
   - Add to relevant .md file
   - Update tool count in README.md

6. **Commit Changes**
   ```bash
   git add src/new_feature.py src/advanced_handlers.py src/mcp_remote_macos_use/server.py
   git commit -m "Add new_feature tool

   New Features:
   - Description of feature

   New MCP Tool:
   - new_feature - What it does

   Use Cases:
   - Example use case
   "
   ```

### Modifying Existing Code

**Guidelines:**

1. **Always read the file first**
   ```python
   # Use Read tool before Edit tool
   Read(file_path="/path/to/file.py")
   Edit(file_path="/path/to/file.py", old_string="...", new_string="...")
   ```

2. **Test compilation after changes**
   ```bash
   python3 -m py_compile modified_file.py
   ```

3. **Check for breaking changes**
   - Are function signatures changed?
   - Are imports still valid?
   - Are error messages clear?

4. **Update related documentation**

### Performance Optimization

**Checklist:**

- [ ] Use connection pooling for VNC (`vnc_connection_manager.py`)
- [ ] Prefer Accessibility API over VNC for local control (10-100x faster)
- [ ] Use smart waiting instead of `time.sleep()`
- [ ] Batch operations when possible
- [ ] Cache results that don't change frequently

---

## 📝 Code Conventions

### Python Style

1. **Imports**
   ```python
   # Standard library
   import os
   import logging
   from typing import Optional, Tuple, List, Dict, Any

   # Third party
   import mcp.types as types

   # Local
   from vnc_client import VNCClient
   ```

2. **Docstrings**
   ```python
   def function_name(param1: str, param2: int) -> Tuple[bool, Optional[str]]:
       """
       Brief description.

       Detailed description if needed.

       Args:
           param1: Description of param1
           param2: Description of param2

       Returns:
           Tuple of (success, error_message)

       Example:
           >>> function_name("test", 42)
           (True, None)
       """
   ```

3. **Error Handling**
   ```python
   try:
       # Action
       result = do_something()
       return True, result, None
   except SpecificException as e:
       logger.error(f"Specific error: {e}", exc_info=True)
       return False, None, str(e)
   except Exception as e:
       logger.error(f"Unexpected error: {e}", exc_info=True)
       return False, None, f"Unexpected error: {str(e)}"
   ```

4. **Logging**
   ```python
   logger = logging.getLogger('module_name')
   logger.setLevel(logging.DEBUG)

   # Use appropriate levels
   logger.debug("Detailed information")
   logger.info("General information")
   logger.warning("Warning message")
   logger.error("Error occurred", exc_info=True)
   ```

5. **Type Hints**
   - Always use type hints for function signatures
   - Use `Optional[T]` for nullable values
   - Use `Tuple[bool, Any, Optional[str]]` for (success, result, error) pattern

### Naming Conventions

- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Handler functions**: `handle_tool_name`
- **Client classes**: `FeatureNameClient`

### File Naming

- **Client libraries**: `feature_name.py` (e.g., `vnc_client.py`)
- **Handler collections**: `*_handlers.py` (e.g., `action_handlers.py`)
- **Utilities**: descriptive names (e.g., `connection_manager.py`)

---

## 🧪 Testing Guidelines

### Test File Organization

```
tests/
├── test_server.py          # MCP server tests
├── test_vnc_client.py      # VNC client tests
├── test_action_handlers.py # Handler tests
└── conftest.py             # Shared fixtures
```

### Writing Tests

```python
def test_feature():
    """Test description."""
    # Arrange
    client = FeatureClient()

    # Act
    success, result, error = client.do_action("param")

    # Assert
    assert success is True
    assert error is None
    assert result is not None
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_server.py

# Specific test
pytest tests/test_server.py::test_function_name

# With coverage
pytest --cov=src tests/
```

---

## 🌿 Git Workflow

### Branch Naming

- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- AI assistant sessions: `claude/session-name-sessionid`

### Commit Messages

**Format:**
```
Brief summary line (imperative mood)

Detailed description:
- What changed
- Why it changed
- Any breaking changes

New Features:
- Feature 1
- Feature 2

New Files:
- file1.py - Description
- file2.py - Description

Use Cases:
- Use case 1
- Use case 2
```

**Examples:**

Good:
```
Add window management and advanced interactions

Complete control over macOS windows and UI.

New Features:
- Window resize, move, minimize, maximize
- Right-click context menus
- Text selection and gestures

New MCP Tools (9 total):
- list_windows, resize_window, move_window
- window_action, switch_to_window
- right_click, select_text, copy_cut_selection
- gesture

All code tested and compiles successfully.
```

Bad:
```
Updated files
```

### Pre-commit Checklist

- [ ] All new files compile: `python3 -m py_compile file.py`
- [ ] Tests pass (if applicable)
- [ ] Documentation updated
- [ ] README.md tool count updated (if tools added)
- [ ] Commit message follows format
- [ ] No sensitive data in commit

---

## 📖 Documentation Standards

### Documentation Files

1. **README.md** - Project overview, quick start
2. **MCP_SETUP.md** - MCP server configuration
3. **DOCKER_SETUP.md** - Docker and VM setup
4. **NATIVE_MACOS_CONTROL.md** - Accessibility API details
5. **PERFORMANCE_IMPROVEMENTS.md** - Performance tips
6. **electron-app/README.md** - Electron app guide

### Adding Documentation

**When to update:**

- New feature added → Update relevant .md file
- New tool added → Update README.md tool count
- Architecture changed → Update this CLAUDE.md
- Setup process changed → Update MCP_SETUP.md or DOCKER_SETUP.md

**Documentation structure:**
```markdown
# Feature Name

Brief description.

## Quick Start

\`\`\`bash
# Quick example
\`\`\`

## Features

- Feature 1
- Feature 2

## Usage Examples

### Example 1
\`\`\`python
# Code example
\`\`\`

## Troubleshooting

### Issue 1
Solution...
```

---

## 🛠️ Common Tasks

### Task 1: Add a New VNC Action

1. Add method to `VNCClient` in `vnc_client.py`
2. Create handler in `action_handlers.py`
3. Register tool in `server.py`
4. Test: `python3 -m py_compile src/vnc_client.py src/action_handlers.py src/mcp_remote_macos_use/server.py`
5. Commit

### Task 2: Add Accessibility API Feature

1. Add method to `AccessibilityClient` in `accessibility_client.py`
2. Create handler in `semantic_handlers.py`
3. Register tool in `server.py`
4. Test compilation
5. Update NATIVE_MACOS_CONTROL.md
6. Commit

### Task 3: Add Advanced Feature

1. Create new client library: `src/feature_name.py`
2. Add handler to `advanced_handlers.py`
3. Import in `server.py`
4. Register tool in `server.py`
5. Test compilation
6. Create/update documentation
7. Commit

### Task 4: Performance Optimization

1. Identify bottleneck
2. Apply optimization:
   - Use connection pooling
   - Use Accessibility API instead of VNC
   - Add caching
   - Batch operations
3. Measure improvement
4. Document in PERFORMANCE_IMPROVEMENTS.md
5. Commit

### Task 5: Add Docker Feature

1. Modify `Dockerfile` or `Dockerfile.vm`
2. Update `docker-compose.yml` if needed
3. Test: `docker-compose build`
4. Update DOCKER_SETUP.md
5. Commit

### Task 6: Fix Bug

1. Reproduce bug
2. Identify root cause
3. Fix in appropriate file
4. Test fix
5. Add test case if possible
6. Commit with clear description

---

## 🔧 Troubleshooting

### Common Issues

#### "Module not found"

**Cause:** Import path incorrect or package not installed

**Solution:**
```bash
# Check if in correct directory
pwd  # Should be /path/to/mcp-remote-macos-use

# Check PYTHONPATH
echo $PYTHONPATH  # Should include src/

# Reinstall
pip install -e .
```

#### "Tool not appearing in MCP server"

**Checklist:**
- [ ] Handler function created
- [ ] Handler imported in `server.py`
- [ ] Tool defined in `@server.list_tools()`
- [ ] Handler called in `@server.call_tool()`
- [ ] Availability flag set correctly
- [ ] Server restarted

#### "Feature not available"

**Cause:** Platform-specific feature on wrong platform

**Solution:** Check availability flags:
```python
FEATURE_AVAILABLE = check_feature_available()

if not FEATURE_AVAILABLE:
    return [types.TextContent(type="text", text="Feature requires macOS")]
```

#### "Compilation errors"

**Process:**
1. Read error message carefully
2. Check import statements
3. Check function signatures match
4. Verify type hints are correct
5. Run: `python3 -m py_compile file.py`

### Debugging Tips

1. **Enable debug logging**
   ```python
   logger.setLevel(logging.DEBUG)
   ```

2. **Check tool registration**
   ```python
   # In server.py @server.list_tools()
   # Verify tool is in the list
   ```

3. **Test handler directly**
   ```python
   # In Python REPL
   from advanced_handlers import handle_tool_name
   result = handle_tool_name({"param": "value"})
   print(result)
   ```

4. **Check MCP server logs**
   ```bash
   # When running with Claude Desktop
   # Check Console.app on macOS
   # Or run server manually to see output
   ```

---

## 🎯 Key Principles for AI Assistants

### 1. Always Compile Before Committing

```bash
python3 -m py_compile modified_file.py
```

### 2. Follow the Handler Pattern

Every MCP tool follows the same pattern - don't deviate.

### 3. Use Connection Pooling

For VNC operations, always use `vnc_connection_manager.py`.

### 4. Prefer Native APIs

When local control is available, use Accessibility API over VNC (10-100x faster).

### 5. Document Everything

- Update docs when adding features
- Write clear docstrings
- Update README.md tool count

### 6. Test Incrementally

- Test after each change
- Don't batch multiple risky changes
- Verify compilation frequently

### 7. Maintain Backwards Compatibility

- Don't break existing function signatures
- Add new parameters as optional
- Deprecate gradually if needed

### 8. Security First

- Never commit secrets
- Use environment variables
- Enable context isolation in Electron
- Validate all user inputs

### 9. Clear Error Messages

Users should understand what went wrong and how to fix it.

### 10. Keep It Simple

Prefer simple, readable code over clever optimizations (unless performance-critical).

---

## 📊 Current State Summary

### MCP Tools: 42 Total

- **VNC Control:** 8 tools
- **Semantic UI:** 6 tools
- **AppleScript/System:** 8 tools
- **Element Extraction:** 6 tools
- **Smart Waiting:** 2 tools
- **Visual Debugging:** 3 tools
- **Window Management:** 5 tools
- **Advanced Interactions:** 4 tools

### Major Components

1. ✅ MCP Server - Running and tested
2. ✅ VNC Client - Connection pooling implemented
3. ✅ Accessibility API - Native macOS control
4. ✅ Docker Support - macOS VMs in containers
5. ✅ Electron App - Standalone VNC viewer
6. ✅ Smart Waiting - Element polling and retry
7. ✅ Visual Debugging - Annotated screenshots
8. ✅ Window Management - Full window control
9. ✅ Advanced Interactions - Right-click, gestures

### Performance Metrics

- **VNC Connection Pooling:** 10-50x faster
- **Accessibility API:** 10-100x faster than VNC
- **Smart Waiting:** Eliminates fixed delays
- **Connection Reuse:** 0.1-0.5s vs 2-5s

---

## 🚀 Future Enhancements

### Potential Additions

1. **OCR Integration** - Extract text from images
2. **Image Finding** - Wait for images on screen
3. **Menu Bar Control** - Click menu bar items
4. **Dock Management** - Add/remove Dock items
5. **Process Management** - Kill/launch with arguments
6. **File Operations** - Drag/drop, Finder automation
7. **Recording/Playback** - Action recording
8. **Display Management** - Brightness, resolution

### When Adding Features

- Follow existing patterns
- Update tool count
- Document thoroughly
- Test on real macOS
- Consider performance impact

---

## 📞 Getting Help

### Resources

- **Main README:** Project overview
- **MCP_SETUP.md:** Setup instructions
- **DOCKER_SETUP.md:** Docker guide
- **NATIVE_MACOS_CONTROL.md:** Accessibility API
- **This File:** Development guide

### Questions to Ask

Before implementing:
1. Does this follow existing patterns?
2. Have I read the relevant client library?
3. Is compilation successful?
4. Are imports correct?
5. Is documentation updated?

---

## ✅ Pre-Commit Checklist

- [ ] All modified files compile successfully
- [ ] Tests pass (if applicable)
- [ ] Documentation updated
- [ ] README.md tool count updated (if tools added)
- [ ] Commit message is descriptive
- [ ] No debug code left in
- [ ] No sensitive data in commit
- [ ] Imports are organized
- [ ] Type hints are present
- [ ] Error handling is comprehensive
- [ ] Logging statements are appropriate

---

**End of CLAUDE.md**

*This guide should be updated whenever major architectural changes are made or new patterns are established.*
