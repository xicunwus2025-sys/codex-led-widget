const { app, BrowserWindow, ipcMain, screen } = require("electron");
const path = require("node:path");
const net = require("node:net");
const { readQuota } = require("./quota-service");

const sizes = {
  medium: { width: 340, height: 180 },
  small: { width: 340, height: 180 }
};

let win;
let currentSize = "medium";
let instanceServer;
const instanceHost = "127.0.0.1";
const instancePort = 47631;

const gotSingleInstanceLock = app.requestSingleInstanceLock();

if (!gotSingleInstanceLock) {
  app.quit();
}

function focusWindow() {
  if (!win) return;
  if (!win.isVisible()) win.show();
  win.setAlwaysOnTop(true);
  win.focus();
}

function acquirePortLock() {
  return new Promise((resolve) => {
    const server = net.createServer((socket) => {
      socket.on("data", () => focusWindow());
      socket.end();
    });

    server.on("error", (error) => {
      if (error.code !== "EADDRINUSE") {
        resolve(true);
        return;
      }

      const client = net.createConnection({ host: instanceHost, port: instancePort }, () => {
        client.end("focus");
      });
      client.on("error", () => {});
      resolve(false);
    });

    server.listen(instancePort, instanceHost, () => {
      instanceServer = server;
      resolve(true);
    });
  });
}

function createWindow() {
  win = new BrowserWindow({
    ...sizes[currentSize],
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    show: false,
    backgroundColor: "#00000000",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  win.loadFile(path.join(__dirname, "../renderer/index.html"));
  win.once("ready-to-show", () => {
    win.show();
    placeTopRight();
  });
}

function placeTopRight() {
  if (!win) return;
  const display = screen.getPrimaryDisplay();
  const bounds = win.getBounds();
  const area = display.workArea;
  win.setBounds({
    x: area.x + area.width - bounds.width - 24,
    y: area.y + 24,
    width: bounds.width,
    height: bounds.height
  });
}

function setWindowSizeAtOrbCenter(size, screenCenterX, screenCenterY, localCenterX, localCenterY) {
  if (!["medium", "small"].includes(size) || !win) return currentSize;
  const next = sizes[size];
  const proposed = {
    x: Math.round(screenCenterX - localCenterX),
    y: Math.round(screenCenterY - localCenterY),
    width: next.width,
    height: next.height
  };
  const display = screen.getDisplayMatching(proposed);
  const area = display.workArea;
  const x = Math.max(area.x + 8, Math.min(proposed.x, area.x + area.width - next.width - 8));
  const y = Math.max(area.y + 8, Math.min(proposed.y, area.y + area.height - next.height - 8));

  currentSize = size;
  win.setBounds({
    x: Math.round(x),
    y: Math.round(y),
    ...next
  });
  win.webContents.send("window:sizeChanged", currentSize);
  return currentSize;
}

function setWindowSize(size) {
  if (!["medium", "small"].includes(size) || !win) return currentSize;
  currentSize = size;
  win.webContents.send("window:sizeChanged", currentSize);
  return currentSize;
}

function showPeek(screenCenterX, screenCenterY) {
  if (!win || currentSize !== "small") return "none";
  const current = win.getBounds();
  const display = screen.getDisplayMatching(current);
  const area = display.workArea;
  return current.x + current.width <= area.x + area.width - 8 ? "right" : "left";
}

function hidePeek(screenCenterX, screenCenterY) {
  if (!win || currentSize !== "small") return currentSize;
  return currentSize;
}

app.whenReady().then(async () => {
  if (!(await acquirePortLock())) {
    app.quit();
    return;
  }

  createWindow();

  app.on("second-instance", () => {
    focusWindow();
  });

  ipcMain.handle("quota:read", async () => readQuota());
  ipcMain.handle("window:close", () => app.quit());
  ipcMain.handle("window:hide", () => win?.hide());
  ipcMain.handle("window:setSizeAtOrbCenter", (_event, size, screenCenterX, screenCenterY, localCenterX, localCenterY) =>
    setWindowSizeAtOrbCenter(size, screenCenterX, screenCenterY, localCenterX, localCenterY));
  ipcMain.handle("window:setSize", (_event, size) => setWindowSize(size));
  ipcMain.handle("window:getSize", () => currentSize);
  ipcMain.handle("window:getBounds", () => win?.getBounds());
  ipcMain.handle("window:showPeek", (_event, screenCenterX, screenCenterY) => showPeek(screenCenterX, screenCenterY));
  ipcMain.handle("window:hidePeek", (_event, screenCenterX, screenCenterY) => hidePeek(screenCenterX, screenCenterY));
  ipcMain.on("window:moveTo", (_event, x, y) => {
    if (!win) return;
    win.setBounds({
      x: Math.round(x),
      y: Math.round(y),
      ...sizes[currentSize]
    });
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", (event) => {
  event.preventDefault();
});

app.on("before-quit", () => {
  instanceServer?.close();
});
