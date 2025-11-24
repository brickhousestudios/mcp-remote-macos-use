# MCP macOS Viewer - Standalone Electron App

🖥️ **All-in-one VNC viewer for macOS control** - No server needed!

A beautiful, standalone desktop application for viewing and controlling macOS systems via VNC, with optional MCP automation controls.

## ✨ Features

- 🚀 **Standalone VNC Viewer** - No external VNC client needed
- 🎨 **Beautiful Modern UI** - Clean, intuitive interface
- 🔒 **Secure** - Built-in websockify proxy for VNC
- 📱 **Cross-Platform** - Works on Linux, macOS, and Windows
- ⚡ **Fast** - Hardware-accelerated rendering
- 🎯 **Quick Presets** - Save and load connection presets
- 🔧 **Optional MCP Controls** - Enable advanced automation (experimental)

## 🚀 Quick Start

### Install

```bash
cd electron-app

# Install dependencies
npm install

# Run in development mode
npm start
```

### Build for Your Platform

```bash
# Build for Linux
npm run build:linux

# Build for macOS
npm run build:mac

# Build for Windows
npm run build:win

# Build for all platforms
npm run build:all
```

Output will be in `dist/` directory.

## 📦 Download Pre-built

Download the latest release for your platform:

- **Linux**: `.AppImage`, `.deb`, or `.rpm`
- **macOS**: `.dmg`
- **Windows**: `.exe` installer or portable `.exe`

## 🎯 Usage

### Connecting to Mac

1. **Enable Screen Sharing** on your Mac:
   - System Settings → Sharing → Screen Sharing

2. **Launch MCP macOS Viewer**

3. **Enter Connection Details**:
   - **Host**: `localhost` (for local VM) or `192.168.1.100` (your Mac's IP)
   - **Port**: `5900` (default VNC port)
   - **Password**: Your VNC password (optional)

4. **Click Connect**

### Quick Presets

Use the preset buttons for common configurations:
- **Local VM**: `localhost:5900`
- **Home Mac**: `192.168.1.100:5900`
- **Second Display**: `localhost:5901`

Edit these in the source to match your setup!

### View Only Mode

Check "View Only Mode" to prevent accidental mouse/keyboard input.

### Fullscreen Mode

Click "Fullscreen" button or use menu: **View → Toggle Fullscreen**

### Fit to Screen

Click "Fit to Screen" to scale the remote desktop to your window size.

## 🔧 Advanced: MCP Controls

Enable "MCP Controls" to access automation features (experimental):

- 📸 **Screenshot**: Capture remote screen
- 🪟 **List Windows**: Show all open windows
- 🔍 **Extract Elements**: Get UI element information

**Note**: Requires MCP server running on the Mac.

## ⌨️ Keyboard Shortcuts

- **Ctrl+N** / **Cmd+N**: New Connection
- **Ctrl+D** / **Cmd+D**: Disconnect
- **Ctrl+Q** / **Cmd+Q**: Quit
- **F11**: Toggle Fullscreen

### Special Key Combinations

Use the **Control** menu to send:
- **Ctrl+Alt+Del**
- **Cmd+Q** (Quit)
- **Cmd+Tab** (Switch apps)

## 🐳 Use with Docker macOS VM

Perfect companion for Docker macOS VMs!

```bash
# Start macOS VM in Docker (from parent directory)
cd ..
docker-compose --profile vm up -d

# Connect with the app
# Host: localhost
# Port: 5900
```

## 🛠️ Development

### Project Structure

```
electron-app/
├── main.js              # Electron main process
├── preload.js           # IPC bridge
├── package.json         # Dependencies & build config
├── src/
│   ├── index.html       # Main UI
│   ├── renderer.js      # UI logic & VNC connection
│   └── styles.css       # Styling
├── build/               # Build assets (icons)
└── dist/                # Built applications
```

### Dependencies

- **Electron**: Desktop app framework
- **noVNC**: HTML5 VNC client
- **websockify**: WebSocket-to-TCP proxy for VNC

### Running in Dev Mode

```bash
npm run dev
```

This opens DevTools automatically.

### Building

```bash
# Development build (faster, not packaged)
npm run pack

# Production builds
npm run build          # Current platform
npm run build:linux    # Linux only
npm run build:mac      # macOS only
npm run build:win      # Windows only
npm run build:all      # All platforms
```

### Adding Custom Icons

Place icons in `build/` directory:
- `icon.png` - Linux (512x512)
- `icon.icns` - macOS
- `icon.ico` - Windows

Use tools like [electron-icon-builder](https://www.npmjs.com/package/electron-icon-builder) to generate from PNG.

## 📊 Performance

- **Rendering**: Hardware-accelerated via Electron
- **FPS**: Real-time counter in toolbar
- **Latency**: ~10-50ms on local network
- **Bandwidth**: ~1-5 Mbps depending on screen changes

## 🔒 Security

- ✅ No external servers - all local processing
- ✅ VNC passwords supported
- ✅ View-only mode available
- ✅ Context isolation enabled
- ✅ No node integration in renderer

## 🐛 Troubleshooting

### "Connection refused"

- Check Mac has Screen Sharing enabled
- Verify firewall allows VNC (port 5900)
- Confirm IP address and port are correct

### "Black screen"

- Wait 5-10 seconds for initial connection
- Check VNC password is correct
- Try disconnecting and reconnecting

### "websockify not starting"

- Make sure `npm install` completed successfully
- Check `node_modules/.bin/websockify` exists
- Try reinstalling: `rm -rf node_modules && npm install`

### "App won't launch"

- Linux: Make `.AppImage` executable: `chmod +x *.AppImage`
- macOS: Allow in Security & Privacy if blocked
- Windows: Allow through SmartScreen if warned

## 🎨 Customization

### Change Default Port

Edit `src/renderer.js`:

```javascript
let wsPort = 6080; // Change this to your preferred port
```

### Add More Presets

Edit `src/index.html`:

```html
<button class="preset-btn" data-host="your.mac.ip" data-port="5900">
    My Custom Mac
</button>
```

### Modify UI Colors

Edit `src/styles.css` - look for gradient definitions:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

## 📚 Related Documentation

- [Main Project README](../README.md)
- [Docker Setup Guide](../DOCKER_SETUP.md)
- [MCP Setup Guide](../MCP_SETUP.md)

## 🤝 Contributing

Found a bug? Have a feature request?

1. Check existing issues
2. Create new issue with details
3. Submit PR with fixes/features

## 📄 License

MIT License - see [LICENSE](../LICENSE)

## 🙏 Credits

- Built with [Electron](https://www.electronjs.org/)
- VNC client by [noVNC](https://github.com/novnc/noVNC)
- Based on [MCP Remote macOS Use](https://github.com/your-repo)

---

**Made with ❤️ for the MCP community**
