const { contextBridge, ipcRenderer } = require('electron');

// Expose a secure API to the renderer process
contextBridge.exposeInMainWorld('nebula', {
  // App info
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  getApiBaseUrl: () => ipcRenderer.invoke('get-api-base-url'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // Platform detection
  platform: process.platform,
  isDesktop: true,
});