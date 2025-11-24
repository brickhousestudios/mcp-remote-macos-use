# Docker Setup Guide

Run MCP Remote macOS Control in Docker - with or without a macOS VM!

## 🚀 Quick Start

### Option 1: Connect to Existing Mac (VNC)

```bash
# 1. Create .env file
cp .env.example .env

# 2. Edit .env with your Mac's IP
nano .env
# Set: MACOS_HOST=192.168.1.100
# Set: MACOS_VNC_PASSWORD=your_password

# 3. Start container
docker-compose --profile basic up -d

# 4. Check logs
docker-compose logs -f mcp-server
```

### Option 2: Run macOS VM in Docker (QEMU/KVM)

```bash
# 1. Enable KVM support
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# 2. Start VM
docker-compose --profile vm up -d

# 3. Access VNC to complete macOS installation
# VNC: localhost:5900

# 4. Check logs
docker-compose logs -f mcp-with-macos-vm
```

### Option 3: Development Mode

```bash
# Start with live code reloading
docker-compose --profile dev up

# Make changes to src/ - they'll be reflected immediately
```

## 📋 Prerequisites

### For Basic VNC Connection:
- Docker installed
- Docker Compose installed
- Existing Mac with Screen Sharing enabled

### For macOS VM:
- Docker installed
- Docker Compose installed
- **KVM support** on host (Linux only)
- **128GB+ disk space** for macOS VM
- **8GB+ RAM** recommended
- macOS installation media (see below)

## 🖥️ Running macOS VM in Docker

### Step 1: Check KVM Support

```bash
# Check if KVM is available
ls -la /dev/kvm

# If not found, enable virtualization in BIOS
# On Ubuntu/Debian:
sudo apt install qemu-kvm libvirt-daemon-system

# Verify KVM works
kvm-ok
```

### Step 2: Get macOS Installation Media

You have 3 options:

#### Option A: Download macOS Installer (Recommended)

```bash
# On a Mac:
# 1. Download macOS from App Store (e.g., macOS Sonoma)
# 2. The installer will be in /Applications/

# 3. Create bootable ISO:
sudo hdiutil create -o /tmp/macOS.cdr -size 16g -layout SPUD -fs HFS+J
sudo hdiutil attach /tmp/macOS.cdr.dmg -noverify -mountpoint /Volumes/install_build
sudo /Applications/Install\ macOS\ Sonoma.app/Contents/Resources/createinstallmedia --volume /Volumes/install_build --nointeraction
hdiutil detach /Volumes/Install\ macOS\ Sonoma
hdiutil convert /tmp/macOS.cdr.dmg -format UDTO -o /tmp/macOS.iso
mv /tmp/macOS.iso.cdr /tmp/macOS.iso

# 4. Copy to vm-data/iso/:
mkdir -p vm-data/iso
cp /tmp/macOS.iso vm-data/iso/
```

#### Option B: Use BaseSystem.dmg

```bash
# Download from OSX-KVM
mkdir -p vm-data/iso
cd vm-data/iso
curl -L https://raw.githubusercontent.com/kholia/OSX-KVM/master/fetch-macOS-v2.py -o fetch-macOS.py
python3 fetch-macOS.py

# This will download BaseSystem.dmg
```

#### Option C: Use Pre-installed Image

```bash
# If you have an existing macOS QCOW2 image:
mkdir -p vm-data/disk
cp /path/to/your/macos.qcow2 vm-data/disk/macos.qcow2
```

### Step 3: Configure VM Settings

Edit `docker-compose.yml` or set environment variables:

```bash
# RAM (default: 8G)
export MACOS_VM_RAM=16G

# CPU Cores (default: 4)
export MACOS_VM_CORES=8

# VNC Password
export MACOS_VNC_PASSWORD=your_vnc_password
```

### Step 4: Start macOS VM

```bash
# Start the VM
docker-compose --profile vm up -d

# Watch startup logs
docker-compose logs -f mcp-with-macos-vm
```

Output should show:
```
🚀 Starting macOS VM with MCP Server
✅ KVM support detected
📀 Found macOS installation ISO
🖥️  Starting QEMU...
✅ macOS VM started
🔌 VNC available at: localhost:5900
🚀 Starting MCP Server...
✅ MCP Server started
🎉 Setup Complete!
```

### Step 5: Complete macOS Installation

```bash
# Connect via VNC
# macOS: Screen Sharing app → localhost:5900
# Linux: vncviewer localhost:5900
# Windows: TightVNC → localhost:5900

# Follow macOS installation wizard:
# 1. Select language
# 2. Disk Utility → Erase → "macOS" → APFS
# 3. Install macOS → Select "macOS" disk
# 4. Wait 20-30 minutes
# 5. Complete setup wizard
```

### Step 6: Enable Screen Sharing in macOS

Once macOS boots:
```
1. System Settings → Sharing
2. Enable "Screen Sharing"
3. Set VNC password (if needed)
```

### Step 7: Connect MCP Server

```bash
# MCP server is already running and connected to VM!
# Check status:
docker-compose exec mcp-with-macos-vm python -c "from vnc_client import VNCClient; print('Connected!')"
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# VNC Connection
MACOS_HOST=192.168.1.100    # Mac IP or 'localhost' for VM
MACOS_PORT=5900              # VNC port
MACOS_VNC_PASSWORD=          # VNC password
MACOS_VNC_USERNAME=          # VNC username (optional)
MACOS_VNC_ENCRYPTION=        # VNC encryption (optional)

# VM Configuration (for macOS VM mode)
MACOS_VM_RAM=8G              # VM RAM
MACOS_VM_CORES=4             # VM CPU cores

# Logging
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
```

### Docker Compose Profiles

```bash
# Basic: Connect to existing Mac
docker-compose --profile basic up

# VM: Run macOS in Docker
docker-compose --profile vm up

# Dev: Development mode with live reload
docker-compose --profile dev up
```

## 🎯 Using with Claude Desktop

### For Docker Container

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "macos-control-docker": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-macos-control",
        "python",
        "-m",
        "mcp_remote_macos_use.server"
      ],
      "env": {
        "MACOS_HOST": "192.168.1.100",
        "MACOS_PORT": "5900",
        "MACOS_VNC_PASSWORD": "your_password"
      }
    }
  }
}
```

### For macOS VM in Docker

```json
{
  "mcpServers": {
    "macos-vm-docker": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-macos-vm",
        "python",
        "-m",
        "mcp_remote_macos_use.server"
      ],
      "env": {
        "MACOS_HOST": "localhost",
        "MACOS_PORT": "5900"
      }
    }
  }
}
```

## 🛠️ Troubleshooting

### Issue: KVM not available

```bash
# Error: /dev/kvm not found

# Solution 1: Enable KVM on host
sudo modprobe kvm
sudo modprobe kvm-intel  # or kvm-amd

# Solution 2: Run Docker with proper privileges
docker run --privileged --device=/dev/kvm ...
```

### Issue: VM won't start

```bash
# Check logs
docker-compose logs mcp-with-macos-vm

# Common issues:
# 1. Not enough RAM - increase MACOS_VM_RAM
# 2. No installation media - check vm-data/iso/
# 3. KVM not available - check /dev/kvm
```

### Issue: VNC connection refused

```bash
# Wait longer - macOS takes 2-5 minutes to boot
docker-compose logs -f mcp-with-macos-vm

# Check VNC port is open
docker ps | grep 5900
nc -zv localhost 5900
```

### Issue: Slow performance

```bash
# Increase VM resources
export MACOS_VM_RAM=16G
export MACOS_VM_CORES=8
docker-compose --profile vm up -d --force-recreate

# Enable KVM acceleration
# Verify: grep -E 'svm|vmx' /proc/cpuinfo
```

## 📊 Performance Tips

### For macOS VM:

1. **Allocate enough RAM**: 8GB minimum, 16GB recommended
2. **Use KVM acceleration**: Verify `/dev/kvm` exists
3. **SSD storage**: Use SSD for vm-data directory
4. **Dedicated cores**: Allocate at least 4 CPU cores
5. **No nested virtualization**: Run on bare metal, not in a VM

### For VNC Connection:

1. **Local network**: Keep MCP server on same network as Mac
2. **Wired connection**: Use Ethernet instead of WiFi
3. **Connection pooling**: Already enabled by default

## 🎬 Advanced Usage

### Custom QEMU Options

Edit `docker/start-macos-vm.sh` to customize QEMU:

```bash
# Add more RAM
QEMU_CMD+=(-m 16G)

# Add more cores
QEMU_CMD+=(-smp cores=8,threads=2)

# Add passthrough device
QEMU_CMD+=(-device vfio-pci,host=01:00.0)
```

### Snapshots

```bash
# Create snapshot
docker exec mcp-macos-vm qemu-img snapshot -c clean-install /vm-data/disk/macos.qcow2

# List snapshots
docker exec mcp-macos-vm qemu-img snapshot -l /vm-data/disk/macos.qcow2

# Restore snapshot
docker exec mcp-macos-vm qemu-img snapshot -a clean-install /vm-data/disk/macos.qcow2
```

### SSH Access

```bash
# Enable SSH in macOS:
# System Settings → Sharing → Remote Login

# Connect from host:
ssh user@localhost -p 10022
```

## 📚 Directory Structure

```
mcp-remote-macos-use/
├── docker/
│   └── start-macos-vm.sh       # VM startup script
├── vm-data/                     # VM data (auto-created)
│   ├── disk/
│   │   └── macos.qcow2         # macOS disk image
│   ├── iso/
│   │   └── macos.iso           # Installation media
│   └── snapshots/               # VM snapshots
├── logs/                        # MCP server logs
├── Dockerfile                   # Basic MCP server
├── Dockerfile.vm                # MCP + macOS VM
├── docker-compose.yml          # Orchestration
└── .env                        # Configuration
```

## 🎯 Example Workflows

### Workflow 1: Test automation in VM

```bash
# 1. Start VM
docker-compose --profile vm up -d

# 2. Complete macOS setup via VNC
# 3. Enable Screen Sharing

# 4. Connect Claude Desktop to VM
# 5. Test: "Take a screenshot"
# 6. Test: "Open Safari and go to google.com"
```

### Workflow 2: Development cycle

```bash
# 1. Start dev container
docker-compose --profile dev up

# 2. Edit src/advanced_handlers.py
# 3. Test immediately (no rebuild needed)
# 4. Check logs in real-time
```

### Workflow 3: CI/CD testing

```bash
# In CI pipeline:
docker-compose --profile vm up -d
docker-compose exec mcp-with-macos-vm python -m pytest
docker-compose down
```

## 🔒 Security Notes

1. **VNC passwords**: Always set strong VNC passwords
2. **Network isolation**: Use Docker networks to isolate VM
3. **Firewall**: Restrict VNC port (5900) to trusted IPs
4. **No public exposure**: Never expose VNC publicly
5. **Regular updates**: Keep macOS and Docker updated

## 🆘 Getting Help

- **Logs**: `docker-compose logs -f`
- **Shell access**: `docker exec -it mcp-macos-vm bash`
- **VM console**: Connect VNC to localhost:5900
- **GitHub issues**: Report problems with logs

## 📖 Additional Resources

- [OSX-KVM](https://github.com/kholia/OSX-KVM) - macOS on QEMU/KVM
- [Docker Documentation](https://docs.docker.com/)
- [QEMU Documentation](https://www.qemu.org/docs/master/)
- [Main README](README.md)
- [MCP Setup Guide](MCP_SETUP.md)
