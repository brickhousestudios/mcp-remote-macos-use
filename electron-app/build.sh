#!/bin/bash
# Build script for MCP macOS Viewer Electron app

set -e

echo "🚀 Building MCP macOS Viewer"
echo "=============================="
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found. Run this from electron-app/ directory."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "✅ Dependencies installed"
    echo ""
fi

# Ask what to build
echo "What would you like to build?"
echo "1) Current platform only (fastest)"
echo "2) Linux (AppImage, deb, rpm)"
echo "3) macOS (dmg)"
echo "4) Windows (exe, portable)"
echo "5) All platforms"
echo "6) Pack (unpackaged build for testing)"
echo ""

read -p "Choose [1-6]: " choice

case $choice in
    1)
        echo "📦 Building for current platform..."
        npm run build
        ;;
    2)
        echo "🐧 Building for Linux..."
        npm run build:linux
        ;;
    3)
        echo "🍎 Building for macOS..."
        npm run build:mac
        ;;
    4)
        echo "🪟 Building for Windows..."
        npm run build:win
        ;;
    5)
        echo "🌍 Building for all platforms..."
        npm run build:all
        ;;
    6)
        echo "📦 Packing (unpackaged)..."
        npm run pack
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Build complete!"
echo ""
echo "📂 Output location: dist/"
echo ""

# List built files
if [ -d "dist" ]; then
    echo "Built files:"
    ls -lh dist/ | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
fi

echo ""
echo "🎉 Done! You can now distribute your application."
echo ""
echo "To test locally:"
echo "  npm start"
echo ""
