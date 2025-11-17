// VNC viewer logic using noVNC
const RFB = window.RFB;

let rfb = null;
let wsPort = 6080; // Default WebSocket port for websockify

// UI Elements
const connectionPanel = document.getElementById('connection-panel');
const vncPanel = document.getElementById('vnc-panel');
const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');
const fullscreenBtn = document.getElementById('fullscreen-btn');
const fitScreenBtn = document.getElementById('fit-screen-btn');
const statusMessage = document.getElementById('status-message');
const vncCanvas = document.getElementById('vnc-canvas');
const vncStatus = document.getElementById('vnc-status');
const mcpControls = document.getElementById('mcp-controls');
const connectedHost = document.getElementById('connected-host');
const fpsCounter = document.getElementById('fps-counter');

// Form inputs
const vncHostInput = document.getElementById('vnc-host');
const vncPortInput = document.getElementById('vnc-port');
const vncPasswordInput = document.getElementById('vnc-password');
const viewOnlyCheckbox = document.getElementById('view-only');
const mcpEnabledCheckbox = document.getElementById('mcp-enabled');

// Modal
const aboutModal = document.getElementById('about-modal');
const closeModal = document.querySelector('.close');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Load app version
    const version = await window.electronAPI.getAppVersion();
    document.getElementById('app-version').textContent = version;

    // Setup event listeners
    setupEventListeners();

    // Listen for menu actions
    window.electronAPI.onNewConnection(() => showConnectionPanel());
    window.electronAPI.onDisconnect(() => disconnect());
    window.electronAPI.onSendKeyCombo((combo) => sendKeyCombo(combo));
    window.electronAPI.onShowAbout(() => showAbout());
});

function setupEventListeners() {
    // Connect button
    connectBtn.addEventListener('click', connect);

    // Disconnect button
    disconnectBtn.addEventListener('click', disconnect);

    // Fullscreen button
    fullscreenBtn.addEventListener('click', toggleFullscreen);

    // Fit to screen button
    fitScreenBtn.addEventListener('click', fitToScreen);

    // Preset buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            vncHostInput.value = e.target.dataset.host;
            vncPortInput.value = e.target.dataset.port;
        });
    });

    // MCP control buttons
    document.querySelectorAll('.mcp-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            handleMCPAction(action);
        });
    });

    // Modal close
    closeModal.addEventListener('click', () => {
        aboutModal.classList.remove('show');
    });

    // Enter key on inputs
    [vncHostInput, vncPortInput, vncPasswordInput].forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                connect();
            }
        });
    });
}

async function connect() {
    const host = vncHostInput.value.trim();
    const port = parseInt(vncPortInput.value);
    const password = vncPasswordInput.value;
    const viewOnly = viewOnlyCheckbox.checked;
    const mcpEnabled = mcpEnabledCheckbox.checked;

    if (!host || !port) {
        showStatus('Please enter host and port', 'error');
        return;
    }

    try {
        showStatus('Connecting...', 'info');
        connectBtn.disabled = true;
        connectBtn.textContent = 'Connecting...';

        // Start websockify proxy
        const result = await window.electronAPI.startVNCConnection({
            host,
            port,
            wsPort
        });

        if (!result.success) {
            throw new Error(result.error);
        }

        // Wait a bit for websockify to start
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Connect to VNC via WebSocket
        const url = `ws://localhost:${wsPort}`;
        console.log('Connecting to:', url);

        rfb = new RFB(vncCanvas, url, {
            credentials: { password: password || '' },
            viewOnly: viewOnly
        });

        // Setup RFB event handlers
        rfb.addEventListener('connect', handleConnect);
        rfb.addEventListener('disconnect', handleDisconnect);
        rfb.addEventListener('credentialsrequired', handleCredentialsRequired);
        rfb.addEventListener('securityfailure', handleSecurityFailure);

        // Show connected host
        connectedHost.textContent = `${host}:${port}`;

        // Show/hide MCP controls
        if (mcpEnabled) {
            mcpControls.classList.remove('hidden');
        }

        // Start FPS counter
        startFPSCounter();

    } catch (error) {
        console.error('Connection error:', error);
        showStatus(`Connection failed: ${error.message}`, 'error');
        connectBtn.disabled = false;
        connectBtn.textContent = 'Connect';
    }
}

function handleConnect() {
    console.log('VNC connected');
    vncStatus.style.display = 'none';
    connectionPanel.classList.add('hidden');
    vncPanel.classList.remove('hidden');
    showStatus('Connected successfully!', 'success');
}

function handleDisconnect(e) {
    console.log('VNC disconnected:', e.detail);
    rfb = null;
    showConnectionPanel();

    if (e.detail.clean) {
        showStatus('Disconnected', 'info');
    } else {
        showStatus('Connection lost', 'error');
    }
}

function handleCredentialsRequired() {
    console.log('Credentials required');
    const password = prompt('VNC password required:');
    if (password) {
        rfb.sendCredentials({ password });
    } else {
        rfb.disconnect();
    }
}

function handleSecurityFailure(e) {
    console.error('Security failure:', e.detail);
    showStatus(`Security failure: ${e.detail.status}`, 'error');
    disconnect();
}

async function disconnect() {
    if (rfb) {
        rfb.disconnect();
        rfb = null;
    }

    await window.electronAPI.stopVNCConnection();
    showConnectionPanel();
}

function showConnectionPanel() {
    vncPanel.classList.add('hidden');
    connectionPanel.classList.remove('hidden');
    mcpControls.classList.add('hidden');
    vncStatus.style.display = 'flex';
    vncStatus.textContent = 'Connecting...';
    connectBtn.disabled = false;
    connectBtn.textContent = 'Connect';
}

function toggleFullscreen() {
    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        vncPanel.requestFullscreen();
    }
}

function fitToScreen() {
    if (rfb) {
        rfb.scaleViewport = !rfb.scaleViewport;
        fitScreenBtn.textContent = rfb.scaleViewport ? 'Actual Size' : 'Fit to Screen';
    }
}

function sendKeyCombo(combo) {
    if (!rfb) return;

    // Map combo strings to key codes
    const keyMap = {
        'ctrl-alt-del': [0xFFE3, 0xFFE9, 0xFFFF], // Ctrl, Alt, Delete
        'cmd-q': [0xFFE7, 0x0071], // Meta (Cmd), Q
        'cmd-tab': [0xFFE7, 0xFF09] // Meta (Cmd), Tab
    };

    const keys = keyMap[combo];
    if (keys) {
        // Press keys
        keys.forEach(key => rfb.sendKey(key, 'Pressed'));
        // Release keys (in reverse order)
        keys.reverse().forEach(key => rfb.sendKey(key, 'Released'));
    }
}

function handleMCPAction(action) {
    console.log('MCP action:', action);
    showStatus(`MCP action: ${action} (not yet implemented)`, 'info');

    // TODO: Implement actual MCP actions
    // These would call the MCP server tools
    switch (action) {
        case 'screenshot':
            // Call MCP: remote_macos_get_screen
            break;
        case 'list-windows':
            // Call MCP: list_windows
            break;
        case 'extract-elements':
            // Call MCP: extract_all_elements
            break;
    }
}

function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    setTimeout(() => {
        statusMessage.className = 'status-message';
        statusMessage.textContent = '';
    }, 5000);
}

function showAbout() {
    aboutModal.classList.add('show');
}

// FPS Counter
let lastFrameTime = Date.now();
let frameCount = 0;
let fpsInterval;

function startFPSCounter() {
    if (fpsInterval) return;

    fpsInterval = setInterval(() => {
        const now = Date.now();
        const delta = (now - lastFrameTime) / 1000;
        const fps = Math.round(frameCount / delta);

        fpsCounter.textContent = `FPS: ${fps}`;

        lastFrameTime = now;
        frameCount = 0;
    }, 1000);

    // Count frames from RFB updates
    if (rfb) {
        rfb.addEventListener('updatedesktop', () => {
            frameCount++;
        });
    }
}

function stopFPSCounter() {
    if (fpsInterval) {
        clearInterval(fpsInterval);
        fpsInterval = null;
    }
}

// Cleanup on unload
window.addEventListener('beforeunload', () => {
    if (rfb) {
        rfb.disconnect();
    }
    stopFPSCounter();
});
