#!/bin/bash
# Start macOS VM with QEMU and MCP Server

set -e

echo "🚀 Starting macOS VM with MCP Server"
echo "======================================"

# Configuration
RAM="${RAM:-8G}"
CORES="${CORES:-4}"
VM_DIR="/vm-data"
OSX_KVM_DIR="/opt/OSX-KVM"

# Check for KVM support
if [ ! -e /dev/kvm ]; then
    echo "❌ Error: /dev/kvm not found. Make sure:"
    echo "  1. Docker is running with --privileged flag"
    echo "  2. KVM is available on host (run: docker run --rm --privileged multiarch/qemu-user-static --reset -p yes)"
    echo "  3. Device is passed with --device=/dev/kvm"
    exit 1
fi

echo "✅ KVM support detected"

# Create necessary directories
mkdir -p "$VM_DIR"/{disk,iso,snapshots}

# Check if macOS disk image exists
DISK_IMG="$VM_DIR/disk/macos.qcow2"

if [ ! -f "$DISK_IMG" ]; then
    echo "📀 No macOS disk image found. Creating..."
    echo ""
    echo "You need to provide a macOS installation image. Options:"
    echo ""
    echo "Option 1: Download macOS installer (recommended)"
    echo "  1. On a Mac, download macOS from App Store"
    echo "  2. Convert to ISO: sudo /path/to/macOS.app/Contents/Resources/createinstallmedia --volume /Volumes/MyVolume"
    echo "  3. Place in: $VM_DIR/iso/macos.iso"
    echo ""
    echo "Option 2: Use BaseSystem.dmg"
    echo "  1. Get BaseSystem.dmg from OSX-KVM"
    echo "  2. Place in: $VM_DIR/iso/BaseSystem.dmg"
    echo ""
    echo "Option 3: Use existing QCOW2 image"
    echo "  1. Place your pre-installed image at: $DISK_IMG"
    echo ""

    # Create empty disk for installation
    qemu-img create -f qcow2 "$DISK_IMG" 128G
    echo "✅ Created 128GB virtual disk at $DISK_IMG"
fi

# Start VNC server first
echo "🖥️  Starting VNC server on port 5900..."

# Build QEMU command
QEMU_CMD=(
    qemu-system-x86_64
    -enable-kvm
    -m "$RAM"
    -smp cores="$CORES",threads=2
    -cpu Penryn,vendor=GenuineIntel,kvm=on,+sse3,+sse4.2,+aes,+xsave,+avx,+xsaveopt,+xsavec,+xgetbv1,+avx2,+bmi2,+smep,+bmi1,+fma,+movbe,+invpcid
    -machine q35,accel=kvm
    -device isa-applesmc,osk="ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc"
    -smbios type=2
    -device ich9-intel-hda -device hda-duplex
    -device ich9-ahci,id=sata
    -drive id=ESP,if=none,format=qcow2,file="$OSX_KVM_DIR/ESP.qcow2"
    -device ide-hd,bus=sata.2,drive=ESP
    -drive id=SystemDisk,if=none,file="$DISK_IMG",format=qcow2
    -device ide-hd,bus=sata.4,drive=SystemDisk
    -netdev user,id=net0,hostfwd=tcp::10022-:22,hostfwd=tcp::5900-:5900
    -device vmxnet3,netdev=net0,id=net0,mac=52:54:00:c9:18:27
    -monitor stdio
    -vnc 0.0.0.0:0
    -usb -device usb-kbd -device usb-tablet
)

# Add installation media if present
if [ -f "$VM_DIR/iso/macos.iso" ]; then
    echo "📀 Found macOS installation ISO"
    QEMU_CMD+=(-drive id=InstallMedia,format=raw,if=none,file="$VM_DIR/iso/macos.iso")
    QEMU_CMD+=(-device ide-hd,bus=sata.3,drive=InstallMedia)
elif [ -f "$VM_DIR/iso/BaseSystem.dmg" ]; then
    echo "📀 Found BaseSystem.dmg"
    # Convert DMG to IMG if needed
    if [ ! -f "$VM_DIR/iso/BaseSystem.img" ]; then
        dmg2img "$VM_DIR/iso/BaseSystem.dmg" "$VM_DIR/iso/BaseSystem.img"
    fi
    QEMU_CMD+=(-drive id=InstallMedia,format=raw,if=none,file="$VM_DIR/iso/BaseSystem.img")
    QEMU_CMD+=(-device ide-hd,bus=sata.3,drive=InstallMedia)
fi

echo "🖥️  VM Configuration:"
echo "  RAM: $RAM"
echo "  CPU Cores: $CORES"
echo "  Disk: $DISK_IMG"
echo "  VNC: localhost:5900"
echo ""

# Start QEMU in background
echo "⚙️  Starting QEMU..."
"${QEMU_CMD[@]}" &
QEMU_PID=$!

# Wait for VM to start
echo "⏳ Waiting for VM to start..."
sleep 10

# Check if QEMU is still running
if ! kill -0 $QEMU_PID 2>/dev/null; then
    echo "❌ QEMU failed to start. Check logs above."
    exit 1
fi

echo "✅ macOS VM started (PID: $QEMU_PID)"
echo "🔌 VNC available at: localhost:5900"
echo ""

# Wait for macOS to boot and VNC to be available
echo "⏳ Waiting for macOS to boot (this may take 2-5 minutes)..."
for i in {1..60}; do
    if nc -z localhost 5900 2>/dev/null; then
        echo "✅ VNC is ready!"
        break
    fi
    sleep 5
done

# Start MCP server
echo ""
echo "🚀 Starting MCP Server..."
cd /app

# Set environment for MCP server to connect to local VM
export MACOS_HOST=localhost
export MACOS_PORT=5900

# Start MCP server
python -m mcp_remote_macos_use.server &
MCP_PID=$!

echo "✅ MCP Server started (PID: $MCP_PID)"
echo ""
echo "================================"
echo "🎉 Setup Complete!"
echo "================================"
echo ""
echo "VNC: localhost:5900"
echo "MCP: localhost:8080"
echo "SSH: localhost:10022 (if configured in macOS)"
echo ""
echo "To connect from Claude Desktop, use:"
echo "  MACOS_HOST=localhost"
echo "  MACOS_PORT=5900"
echo ""
echo "Press Ctrl+C to stop..."

# Handle shutdown
trap "echo 'Shutting down...'; kill $QEMU_PID $MCP_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Wait for processes
wait $QEMU_PID $MCP_PID
