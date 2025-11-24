const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let websockifyProcess = null;

// Development mode flag
const isDev = process.argv.includes('--dev');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    title: 'MCP macOS Viewer',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false
    },
    icon: path.join(__dirname, 'build', 'icon.png')
  });

  // Load the app
  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Create application menu
  createMenu();

  mainWindow.on('closed', () => {
    mainWindow = null;
    stopWebsockify();
  });
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Connection',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('new-connection');
          }
        },
        {
          label: 'Disconnect',
          accelerator: 'CmdOrCtrl+D',
          click: () => {
            mainWindow.webContents.send('disconnect');
          }
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Control',
      submenu: [
        {
          label: 'Send Ctrl+Alt+Del',
          click: () => {
            mainWindow.webContents.send('send-key-combo', 'ctrl-alt-del');
          }
        },
        {
          label: 'Send Cmd+Q',
          click: () => {
            mainWindow.webContents.send('send-key-combo', 'cmd-q');
          }
        },
        {
          label: 'Send Cmd+Tab',
          click: () => {
            mainWindow.webContents.send('send-key-combo', 'cmd-tab');
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            mainWindow.webContents.send('show-about');
          }
        },
        {
          label: 'Documentation',
          click: () => {
            require('electron').shell.openExternal('https://github.com/your-repo/mcp-remote-macos-use');
          }
        }
      ]
    }
  ];

  // Add DevTools in development
  if (isDev) {
    template.push({
      label: 'Developer',
      submenu: [
        { role: 'toggleDevTools' },
        { type: 'separator' },
        {
          label: 'Reload',
          accelerator: 'F5',
          click: () => {
            mainWindow.reload();
          }
        }
      ]
    });
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Start websockify proxy for VNC
function startWebsockify(vncHost, vncPort, wsPort) {
  return new Promise((resolve, reject) => {
    // Kill existing process
    if (websockifyProcess) {
      websockifyProcess.kill();
    }

    // Find websockify
    const websockifyPath = path.join(__dirname, 'node_modules', '.bin', 'websockify');

    // Start websockify: websockify 0.0.0.0:wsPort vncHost:vncPort
    websockifyProcess = spawn('node', [
      websockifyPath,
      `0.0.0.0:${wsPort}`,
      `${vncHost}:${vncPort}`
    ]);

    websockifyProcess.stdout.on('data', (data) => {
      console.log(`websockify: ${data}`);
      if (data.toString().includes('proxying from')) {
        resolve(true);
      }
    });

    websockifyProcess.stderr.on('data', (data) => {
      console.error(`websockify error: ${data}`);
    });

    websockifyProcess.on('error', (error) => {
      console.error('Failed to start websockify:', error);
      reject(error);
    });

    websockifyProcess.on('close', (code) => {
      console.log(`websockify exited with code ${code}`);
      websockifyProcess = null;
    });

    // Timeout if not started
    setTimeout(() => {
      if (websockifyProcess) {
        resolve(true);
      }
    }, 2000);
  });
}

function stopWebsockify() {
  if (websockifyProcess) {
    websockifyProcess.kill();
    websockifyProcess = null;
  }
}

// IPC handlers
ipcMain.handle('start-vnc-connection', async (event, config) => {
  try {
    const { host, port, wsPort } = config;
    console.log(`Starting VNC connection to ${host}:${port} via websocket ${wsPort}`);

    await startWebsockify(host, port, wsPort);

    return { success: true, wsPort };
  } catch (error) {
    console.error('Error starting VNC connection:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('stop-vnc-connection', async () => {
  stopWebsockify();
  return { success: true };
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  stopWebsockify();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopWebsockify();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});
