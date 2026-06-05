const { app, BrowserWindow, ipcMain, shell, Tray, Menu, nativeImage, screen } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");
const { getQuota } = require("./quota-service");

let mainWindow;
let tray;
let isAlwaysOnTop = true;
let saveBoundsTimer;

const defaultBounds = {
  width: 291,
  height: 139
};

const windowLimits = {
  fixedWidth: 291,
  minHeight: 72,
  maxHeight: 139
};

const trayStates = {
  loading: { color: [156, 168, 184], label: "读取中" },
  ready: { color: [85, 230, 165], label: "额度正常" },
  warning: { color: [255, 209, 102], label: "额度偏低" },
  danger: { color: [255, 102, 122], label: "额度用尽" },
  error: { color: [255, 102, 122], label: "读取失败" }
};

function createWindow() {
  const savedBounds = loadWindowBounds();
  mainWindow = new BrowserWindow({
    width: savedBounds.width,
    height: savedBounds.height,
    x: savedBounds.x,
    y: savedBounds.y,
    minWidth: windowLimits.fixedWidth,
    maxWidth: windowLimits.fixedWidth,
    minHeight: windowLimits.minHeight,
    maxHeight: windowLimits.maxHeight,
    frame: false,
    transparent: true,
    resizable: false,
    thickFrame: false,
    hasShadow: false,
    alwaysOnTop: isAlwaysOnTop,
    skipTaskbar: false,
    icon: createTrayIcon("loading"),
    show: false,
    backgroundColor: "#00000000",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    if (!savedBounds.hasPosition) {
      placeWindowTopRight();
      saveWindowBounds();
    }
  });
  mainWindow.on("resize", scheduleSaveWindowBounds);
  mainWindow.on("move", scheduleSaveWindowBounds);
}

function placeWindowTopRight() {
  if (!mainWindow) return;
  const display = screen.getPrimaryDisplay();
  const { width, height } = mainWindow.getBounds();
  const { workArea } = display;
  mainWindow.setBounds({
    x: workArea.x + workArea.width - width - 24,
    y: workArea.y + 24,
    width,
    height
  });
}

function createTray() {
  tray = new Tray(createTrayIcon("loading"));
  updateTrayStatus("loading");
  rebuildTrayMenu();
  tray.on("click", toggleWindow);
}

function getWindowStatePath() {
  return path.join(app.getPath("userData"), "window-state.json");
}

function loadWindowBounds() {
  try {
    const state = JSON.parse(fs.readFileSync(getWindowStatePath(), "utf8"));
    const bounds = sanitizeWindowBounds(state);
    if (bounds) return bounds;
  } catch {
    // Use defaults on first run or if the state file is invalid.
  }

  return {
    ...defaultBounds,
    hasPosition: false
  };
}

function sanitizeWindowBounds(state) {
  if (!state || typeof state !== "object") return null;
  const width = windowLimits.fixedWidth;
  const height = clampNumber(Math.round(Number(state.height) || defaultBounds.height), windowLimits.minHeight, windowLimits.maxHeight);
  const x = Number.isFinite(state.x) ? Math.round(state.x) : undefined;
  const y = Number.isFinite(state.y) ? Math.round(state.y) : undefined;
  const hasPosition = Number.isFinite(x) && Number.isFinite(y);

  if (hasPosition && !isRectVisible({ x, y, width, height })) {
    return {
      width,
      height,
      hasPosition: false
    };
  }

  return {
    width,
    height,
    x,
    y,
    hasPosition
  };
}

function clampNumber(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function isRectVisible(bounds) {
  return screen.getAllDisplays().some(({ workArea }) => {
    const right = bounds.x + bounds.width;
    const bottom = bounds.y + bounds.height;
    return right > workArea.x && bounds.x < workArea.x + workArea.width && bottom > workArea.y && bounds.y < workArea.y + workArea.height;
  });
}

function scheduleSaveWindowBounds() {
  clearTimeout(saveBoundsTimer);
  saveBoundsTimer = setTimeout(saveWindowBounds, 250);
}

function saveWindowBounds() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  const bounds = mainWindow.getBounds();

  try {
    fs.mkdirSync(app.getPath("userData"), { recursive: true });
    fs.writeFileSync(getWindowStatePath(), `${JSON.stringify(bounds, null, 2)}\n`, "utf8");
  } catch {
    // Failing to persist window state should not affect quota display.
  }
}

function setWindowBounds(bounds) {
  if (!mainWindow || mainWindow.isDestroyed() || !bounds || typeof bounds !== "object") return null;
  const current = mainWindow.getBounds();
  const requestedHeight = Number.isFinite(bounds.height) ? Math.round(bounds.height) : current.height;
  const nextBounds = {
    x: current.x,
    y: Number.isFinite(bounds.y) ? Math.round(bounds.y) : current.y,
    width: windowLimits.fixedWidth,
    height: clampNumber(requestedHeight, windowLimits.minHeight, windowLimits.maxHeight)
  };

  mainWindow.setBounds(nextBounds);
  scheduleSaveWindowBounds();
  return mainWindow.getBounds();
}

function updateTrayStatus(state) {
  const nextState = trayStates[state] ? state : "loading";
  const icon = createTrayIcon(nextState);

  if (tray) {
    tray.setImage(icon);
    tray.setToolTip(`Codex Quota Widget - ${trayStates[nextState].label}`);
  }

  if (mainWindow && typeof mainWindow.setIcon === "function") {
    mainWindow.setIcon(icon);
  }
}

function getQuotaState(quota) {
  const percent = Number.isFinite(quota?.remainingPercent) ? quota.remainingPercent : 0;
  if (percent <= 0) return "danger";
  if (percent < 10) return "warning";
  return "ready";
}

function createTrayIcon(state) {
  const image = nativeImage.createFromBuffer(createCirclePng(trayStates[state].color));
  image.setTemplateImage(false);
  return image;
}

function createCirclePng(color) {
  const size = 32;
  const center = (size - 1) / 2;
  const radius = 10.8;
  const glowRadius = 15.2;
  const data = Buffer.alloc((size * 4 + 1) * size);

  for (let y = 0; y < size; y += 1) {
    const rowOffset = y * (size * 4 + 1);
    data[rowOffset] = 0;

    for (let x = 0; x < size; x += 1) {
      const dx = x - center;
      const dy = y - center;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const pixelOffset = rowOffset + 1 + x * 4;

      let alpha = 0;
      if (distance <= radius) {
        alpha = 255;
      } else if (distance <= glowRadius) {
        alpha = Math.round(90 * (1 - (distance - radius) / (glowRadius - radius)));
      }

      const highlight = Math.max(0, 1 - Math.sqrt((x - 12) ** 2 + (y - 10) ** 2) / 14) * 42;
      data[pixelOffset] = Math.min(255, color[0] + highlight);
      data[pixelOffset + 1] = Math.min(255, color[1] + highlight);
      data[pixelOffset + 2] = Math.min(255, color[2] + highlight);
      data[pixelOffset + 3] = alpha;
    }
  }

  return encodePng(size, size, data);
}

function encodePng(width, height, data) {
  const header = Buffer.from("89504e470d0a1a0a", "hex");
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  return Buffer.concat([
    header,
    pngChunk("IHDR", ihdr),
    pngChunk("IDAT", zlib.deflateSync(data)),
    pngChunk("IEND", Buffer.alloc(0))
  ]);
}

function pngChunk(type, data) {
  const typeBuffer = Buffer.from(type, "ascii");
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length, 0);

  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])), 0);

  return Buffer.concat([length, typeBuffer, data, crc]);
}

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = crc & 1 ? 0xedb88320 ^ (crc >>> 1) : crc >>> 1;
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function rebuildTrayMenu() {
  if (!tray) return;
  tray.setContextMenu(
    Menu.buildFromTemplate([
      { label: "显示/隐藏", click: toggleWindow },
      { label: "刷新额度", click: () => mainWindow?.webContents.send("quota:refresh") },
      {
        label: isAlwaysOnTop ? "取消置顶" : "置顶",
        click: () => setAlwaysOnTop(!isAlwaysOnTop)
      },
      { type: "separator" },
      { label: "退出", click: () => app.quit() }
    ])
  );
}

function setAlwaysOnTop(value) {
  isAlwaysOnTop = Boolean(value);
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(isAlwaysOnTop);
    mainWindow.webContents.send("window:alwaysOnTopChanged", isAlwaysOnTop);
  }
  rebuildTrayMenu();
  return isAlwaysOnTop;
}

function toggleWindow() {
  if (!mainWindow) return;
  if (mainWindow.isVisible()) {
    mainWindow.hide();
  } else {
    mainWindow.show();
    mainWindow.focus();
  }
}

app.whenReady().then(() => {
  createWindow();
  createTray();

  ipcMain.handle("quota:get", async () => {
    updateTrayStatus("loading");
    try {
      const quota = await getQuota();
      updateTrayStatus(getQuotaState(quota));
      return quota;
    } catch (error) {
      updateTrayStatus("error");
      throw error;
    }
  });
  ipcMain.handle("window:minimize", () => mainWindow?.hide());
  ipcMain.handle("window:close", () => app.quit());
  ipcMain.handle("window:bounds:get", () => mainWindow?.getBounds());
  ipcMain.handle("window:bounds:set", (_event, bounds) => setWindowBounds(bounds));
  ipcMain.handle("window:alwaysOnTop:get", () => isAlwaysOnTop);
  ipcMain.handle("window:alwaysOnTop:set", (_event, value) => setAlwaysOnTop(value));
  ipcMain.handle("external:openCodex", () => {
    shell.openPath(path.join(process.env.LOCALAPPDATA || "", "OpenAI", "Codex", "bin", "codex.exe"));
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", (event) => {
  event.preventDefault();
});

app.on("before-quit", () => {
  clearTimeout(saveBoundsTimer);
  saveWindowBounds();
});
