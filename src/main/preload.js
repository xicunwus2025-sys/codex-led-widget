const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("quotaWidget", {
  readQuota: () => ipcRenderer.invoke("quota:read"),
  close: () => ipcRenderer.invoke("window:close"),
  hide: () => ipcRenderer.invoke("window:hide"),
  setSize: (size) => ipcRenderer.invoke("window:setSize", size),
  setSizeAtOrbCenter: (size, screenCenterX, screenCenterY, localCenterX, localCenterY) =>
    ipcRenderer.invoke("window:setSizeAtOrbCenter", size, screenCenterX, screenCenterY, localCenterX, localCenterY),
  getSize: () => ipcRenderer.invoke("window:getSize"),
  getBounds: () => ipcRenderer.invoke("window:getBounds"),
  showPeek: (screenCenterX, screenCenterY) => ipcRenderer.invoke("window:showPeek", screenCenterX, screenCenterY),
  hidePeek: (screenCenterX, screenCenterY) => ipcRenderer.invoke("window:hidePeek", screenCenterX, screenCenterY),
  moveTo: (x, y) => ipcRenderer.send("window:moveTo", x, y)
});
