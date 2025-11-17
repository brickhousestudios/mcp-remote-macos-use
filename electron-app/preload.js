const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // VNC connection
  startVNCConnection: (config) => ipcRenderer.invoke('start-vnc-connection', config),
  stopVNCConnection: () => ipcRenderer.invoke('stop-vnc-connection'),

  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),

  // Listen for events from main process
  onNewConnection: (callback) => ipcRenderer.on('new-connection', callback),
  onDisconnect: (callback) => ipcRenderer.on('disconnect', callback),
  onSendKeyCombo: (callback) => ipcRenderer.on('send-key-combo', (event, combo) => callback(combo)),
  onShowAbout: (callback) => ipcRenderer.on('show-about', callback),

  // Remove listeners
  removeListener: (channel) => ipcRenderer.removeAllListeners(channel)
});
