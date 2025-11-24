#!/bin/bash
# MCP Remote macOS Control - Setup Script

set -e

echo "🚀 MCP Remote macOS Control - Setup Script"
echo "=========================================="
echo ""

# Get the absolute path to the project
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  Warning: This is designed for macOS. Some features may not work on $OSTYPE"
    echo ""
fi

# Install dependencies
echo "📦 Installing dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv (recommended)..."
    uv pip install -e "$PROJECT_DIR"
elif command -v pip &> /dev/null; then
    echo "Using pip..."
    pip install -e "$PROJECT_DIR"
else
    echo "❌ Error: Neither uv nor pip found. Please install pip or uv first."
    exit 1
fi
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "📝 Creating .env file..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "✅ Created .env file (edit it if you need VNC settings)"
else
    echo "📝 .env file already exists"
fi
echo ""

# Detect Claude Desktop config location
CLAUDE_CONFIG=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CLAUDE_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    CLAUDE_CONFIG="$APPDATA/Claude/claude_desktop_config.json"
fi

echo "🔧 Claude Desktop Configuration"
echo "================================"
echo ""
echo "Add this to your Claude Desktop config:"
echo "Location: $CLAUDE_CONFIG"
echo ""
echo "{"
echo "  \"mcpServers\": {"
echo "    \"macos-control\": {"
echo "      \"command\": \"python\","
echo "      \"args\": ["
echo "        \"-m\","
echo "        \"mcp_remote_macos_use.server\""
echo "      ],"
echo "      \"cwd\": \"$PROJECT_DIR\","
echo "      \"env\": {"
echo "        \"MACOS_HOST\": \"localhost\","
echo "        \"PYTHONPATH\": \"$PROJECT_DIR/src\""
echo "      }"
echo "    }"
echo "  }"
echo "}"
echo ""

# Offer to create/update config
if [ -f "$CLAUDE_CONFIG" ]; then
    echo "📄 Found existing Claude Desktop config"
    read -p "Do you want to automatically add this configuration? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup existing config
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup"
        echo "✅ Backed up existing config to $CLAUDE_CONFIG.backup"

        # Use Python to merge JSON (safer than manual editing)
        python3 << EOF
import json
import sys

config_path = "$CLAUDE_CONFIG"
project_dir = "$PROJECT_DIR"

# Read existing config
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except:
    config = {}

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add our server
config['mcpServers']['macos-control'] = {
    'command': 'python',
    'args': ['-m', 'mcp_remote_macos_use.server'],
    'cwd': project_dir,
    'env': {
        'MACOS_HOST': 'localhost',
        'PYTHONPATH': f'{project_dir}/src'
    }
}

# Write back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Updated Claude Desktop config")
EOF
    else
        echo "⏭️  Skipped automatic configuration. Please add manually."
    fi
else
    echo "ℹ️  Claude Desktop config not found at $CLAUDE_CONFIG"
    echo "Please create it manually with the configuration above."
fi
echo ""

# Accessibility permissions reminder
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🔐 Important: Grant Accessibility Permissions"
    echo "=============================================="
    echo "1. Open System Settings → Privacy & Security → Accessibility"
    echo "2. Click the + button"
    echo "3. Add Terminal (or your Python executable)"
    echo "4. Enable the toggle"
    echo ""
    echo "Without this, many features won't work!"
    echo ""
fi

echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Restart Claude Desktop"
echo "2. Look for 🔌 icon to confirm connection"
echo "3. Try: 'Take a screenshot of my Mac screen'"
echo ""
echo "📚 Read MCP_SETUP.md for full documentation"
echo "🎯 Available tools: 42 total"
