#!/bin/bash
# Quick reference for Docker commands

echo "MCP Remote macOS Control - Docker Commands"
echo "==========================================="
echo ""

show_help() {
    echo "Usage: ./docker-commands.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start-basic     - Start MCP server (connect to existing Mac)"
    echo "  start-vm        - Start MCP server with macOS VM"
    echo "  start-dev       - Start development mode"
    echo "  stop            - Stop all containers"
    echo "  logs            - View logs"
    echo "  shell           - Open shell in container"
    echo "  build           - Build Docker images"
    echo "  clean           - Clean up containers and images"
    echo "  status          - Show container status"
    echo "  vnc             - Show VNC connection info"
    echo ""
}

start_basic() {
    echo "🚀 Starting MCP Server (Basic Mode)"
    docker-compose --profile basic up -d
    echo "✅ Started! Check status with: ./docker-commands.sh status"
}

start_vm() {
    echo "🚀 Starting MCP Server with macOS VM"
    echo "⚠️  This requires KVM support and macOS installation media"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose --profile vm up -d
        echo "✅ Started! Connect VNC to localhost:5900"
        echo "📝 Check logs with: ./docker-commands.sh logs"
    fi
}

start_dev() {
    echo "🚀 Starting Development Mode"
    docker-compose --profile dev up
}

stop_all() {
    echo "🛑 Stopping all containers..."
    docker-compose --profile basic --profile vm --profile dev down
    echo "✅ Stopped"
}

show_logs() {
    echo "📋 Container Logs"
    echo "================"
    docker-compose logs -f --tail=100
}

open_shell() {
    echo "🐚 Opening shell..."
    CONTAINER=$(docker ps --filter "name=mcp" --format "{{.Names}}" | head -1)
    if [ -z "$CONTAINER" ]; then
        echo "❌ No running MCP container found"
        echo "Start one first with: ./docker-commands.sh start-basic"
        exit 1
    fi
    docker exec -it "$CONTAINER" bash
}

build_images() {
    echo "🔨 Building Docker images..."
    docker-compose build
    echo "✅ Build complete"
}

clean_all() {
    echo "🧹 Cleaning up..."
    read -p "This will remove containers, images, and volumes. Continue? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose --profile basic --profile vm --profile dev down -v --rmi all
        echo "✅ Cleaned up"
    fi
}

show_status() {
    echo "📊 Container Status"
    echo "=================="
    docker-compose ps
    echo ""
    echo "🔌 Port Mappings"
    echo "==============="
    docker ps --filter "name=mcp" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

show_vnc() {
    echo "🖥️  VNC Connection Info"
    echo "====================="
    echo ""

    if docker ps | grep -q "mcp-macos-vm"; then
        echo "macOS VM VNC: localhost:5900"
        echo "MCP Server: localhost:8080"
        echo "SSH: localhost:10022"
    elif docker ps | grep -q "mcp-macos-control"; then
        echo "Remote Mac VNC: Check MACOS_HOST in .env"
        echo "MCP Server: localhost:8080"
    else
        echo "❌ No MCP containers running"
        echo "Start one with: ./docker-commands.sh start-basic"
    fi
}

# Main command handler
case "$1" in
    start-basic)
        start_basic
        ;;
    start-vm)
        start_vm
        ;;
    start-dev)
        start_dev
        ;;
    stop)
        stop_all
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    build)
        build_images
        ;;
    clean)
        clean_all
        ;;
    status)
        show_status
        ;;
    vnc)
        show_vnc
        ;;
    *)
        show_help
        ;;
esac
