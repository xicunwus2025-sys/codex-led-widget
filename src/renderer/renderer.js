const i18n = {
  zh: {
    brand: "Codex 额度",
    loading: "读取中",
    ready: "已更新",
    warning: "接近用尽",
    danger: "额度用尽",
    error: "读取失败",
    primary: "5 小时限额",
    secondary: "7 天限额",
    remaining: "剩余",
    resetTime: "重置时间",
    palette: "调色盘",
    bgColor: "背景色",
    textColor: "字体色",
    opacity: "透明度",
    refresh: "刷新",
    hide: "隐藏",
    exit: "退出",
    pin: "置顶",
    unpin: "取消置顶",
    reading: "正在读取 Codex 额度...",
    noData: "未读到额度窗口",
    unknown: "未知",
    after: "后",
    used: "已用",
    lang: "EN"
  },
  en: {
    brand: "Codex Quota",
    loading: "Loading",
    ready: "Updated",
    warning: "Running low",
    danger: "Quota empty",
    error: "Read failed",
    primary: "5h limit",
    secondary: "7d limit",
    remaining: "Remaining",
    resetTime: "Reset",
    palette: "Theme",
    bgColor: "Color",
    textColor: "Text",
    opacity: "Opacity",
    refresh: "Refresh",
    hide: "Hide",
    exit: "Exit",
    pin: "Pin",
    unpin: "Unpin",
    reading: "Reading Codex quota...",
    noData: "No quota window found",
    unknown: "Unknown",
    after: "left",
    used: "used",
    lang: "中"
  }
};

let language = localStorage.getItem("language") || "zh";
let isAlwaysOnTop = true;
let refreshTimer = null;

const FIXED_WINDOW_WIDTH = 291;
const MIN_WINDOW_HEIGHT = 72;
const MAX_WINDOW_HEIGHT = 139;

const els = {
  body: document.body,
  trafficLight: document.getElementById("trafficLight"),
  stateText: document.getElementById("stateText"),
  brandName: document.getElementById("brandName"),
  paletteBtn: document.getElementById("paletteBtn"),
  themeOverlay: document.getElementById("themeOverlay"),
  themePanel: document.getElementById("themePanel"),
  bgColorInput: document.getElementById("bgColorInput"),
  textColorInput: document.getElementById("textColorInput"),
  opacityInput: document.getElementById("opacityInput"),
  bgColorLabel: document.getElementById("bgColorLabel"),
  textColorLabel: document.getElementById("textColorLabel"),
  opacityLabel: document.getElementById("opacityLabel"),
  langBtn: document.getElementById("langBtn"),
  pinBtn: document.getElementById("pinBtn"),
  refreshBtn: document.getElementById("refreshBtn"),
  minimizeBtn: document.getElementById("minimizeBtn"),
  closeBtn: document.getElementById("closeBtn"),
  quotaList: document.getElementById("quotaList")
};

function t(key) {
  return i18n[language][key];
}

function applyLabels() {
  els.brandName.textContent = t("brand");
  els.langBtn.textContent = t("lang");
  els.paletteBtn.title = t("palette");
  els.paletteBtn.setAttribute("aria-label", t("palette"));
  els.bgColorLabel.textContent = t("bgColor");
  els.textColorLabel.textContent = t("textColor");
  els.opacityLabel.textContent = t("opacity");
  els.refreshBtn.title = t("refresh");
  els.refreshBtn.setAttribute("aria-label", t("refresh"));
  els.minimizeBtn.title = t("hide");
  els.minimizeBtn.setAttribute("aria-label", t("hide"));
  els.closeBtn.title = t("exit");
  els.closeBtn.setAttribute("aria-label", t("exit"));
  updatePinButton();
}

function loadTheme() {
  const backgroundColor = localStorage.getItem("theme.backgroundColor") || "#0a2f35";

  return {
    backgroundColor,
    textColor: localStorage.getItem("theme.textColor") || getRecommendedTextColor(backgroundColor),
    opacity: Number(localStorage.getItem("theme.backgroundOpacity") || "72")
  };
}

function saveTheme(theme) {
  localStorage.setItem("theme.backgroundColor", theme.backgroundColor);
  localStorage.setItem("theme.textColor", theme.textColor);
  localStorage.setItem("theme.backgroundOpacity", String(theme.opacity));
}

function applyTheme(theme) {
  const backgroundRgb = hexToRgb(theme.backgroundColor) || hexToRgb("#0a2f35");
  const textRgb = hexToRgb(theme.textColor) || hexToRgb("#dbf5f1");
  const opacity = Math.max(35, Math.min(95, Number(theme.opacity) || 72));
  const alpha = opacity / 100;

  document.documentElement.style.setProperty("--glass-rgb", `${backgroundRgb.r}, ${backgroundRgb.g}, ${backgroundRgb.b}`);
  document.documentElement.style.setProperty("--glass-alpha", alpha.toFixed(2));
  document.documentElement.style.setProperty("--glass-alpha-strong", Math.min(0.96, alpha + 0.12).toFixed(2));
  document.documentElement.style.setProperty("--text", `rgba(${textRgb.r}, ${textRgb.g}, ${textRgb.b}, 0.94)`);
  document.documentElement.style.setProperty("--muted", `rgba(${textRgb.r}, ${textRgb.g}, ${textRgb.b}, 0.68)`);
}

function hexToRgb(hex) {
  const match = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!match) return null;
  return {
    r: parseInt(match[1], 16),
    g: parseInt(match[2], 16),
    b: parseInt(match[3], 16)
  };
}

function getRecommendedTextColor(backgroundColor) {
  const rgb = hexToRgb(backgroundColor) || hexToRgb("#0a2f35");
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
  return luminance > 0.58 ? "#17202a" : "#dbf5f1";
}

function updateThemeFromControls() {
  const theme = {
    backgroundColor: els.bgColorInput.value,
    textColor: els.textColorInput.value,
    opacity: Number(els.opacityInput.value)
  };

  applyTheme(theme);
  saveTheme(theme);
}

function updateBackgroundTheme() {
  els.textColorInput.value = getRecommendedTextColor(els.bgColorInput.value);
  updateThemeFromControls();
}

function updatePinButton() {
  const label = isAlwaysOnTop ? t("unpin") : t("pin");
  els.pinBtn.classList.toggle("active", isAlwaysOnTop);
  els.pinBtn.title = label;
  els.pinBtn.setAttribute("aria-label", label);
}

function setState(state, message) {
  els.body.dataset.state = state;
  els.trafficLight.classList.toggle("loading", state === "loading");
  els.stateText.textContent = message || t(state === "loading" ? "loading" : state);
}

function stateForRemaining(percent) {
  if (percent <= 0) return "danger";
  if (percent < 10) return "warning";
  return "ready";
}

function formatWindowValue(window) {
  if (!window) return "--";
  const remaining = Number.isFinite(window.remainingPercent) ? Math.round(window.remainingPercent) : null;
  const reset = formatResetTime(window.resetsAt);
  const percentPart = remaining === null ? "--" : `${t("remaining")} ${remaining}%`;
  return reset ? `${percentPart} (${t("resetTime")}: ${reset})` : percentPart;
}

function formatResetTime(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (!Number.isFinite(date.getTime())) return "";

  const now = new Date();
  const sameDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  if (sameDay) {
    return date.toLocaleTimeString(language === "zh" ? "zh-CN" : "en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    });
  }

  if (language === "en") {
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

function updateQuota(quota) {
  const percent = Number.isFinite(quota.remainingPercent) ? quota.remainingPercent : 0;
  const state = stateForRemaining(percent);

  renderQuotaList(quota.limits || []);
  setState(state, statusTextForQuota(quota, state));
}

function renderQuotaList(limits) {
  els.quotaList.replaceChildren();

  for (const limit of limits) {
    const group = document.createElement("section");
    group.className = "quota-group";
    group.dataset.limitId = limit.limitId || "";
    if (limit.limitId !== "codex") group.classList.add("secondary-limit");

    const title = document.createElement("h2");
    title.textContent = `${limit.limitName || t("unknown")} 限额`;
    group.appendChild(title);

    group.appendChild(createQuotaRow(t("primary"), limit.primary, "primary"));
    group.appendChild(createQuotaRow(t("secondary"), limit.secondary, "secondary"));
    els.quotaList.appendChild(group);
  }
}

function createQuotaRow(label, window, type) {
  const row = document.createElement("div");
  row.className = `quota-row ${type}`;

  const labelEl = document.createElement("span");
  labelEl.className = "quota-label";
  labelEl.textContent = `${label}:`;

  const valueEl = document.createElement("strong");
  valueEl.className = "quota-value";
  valueEl.textContent = formatWindowValue(window);

  row.append(labelEl, valueEl);
  return row;
}

function statusTextForQuota(quota, state) {
  const fetchedAt = quota.fetchedAt ? new Date(quota.fetchedAt) : new Date();
  const time = formatClockTime(fetchedAt);

  if (!quota.limits || quota.limits.length === 0) return t("noData");
  return `${t(state)} · ${time}`;
}

function formatClockTime(date) {
  return date.toLocaleTimeString(language === "zh" ? "zh-CN" : "en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
}

async function refreshQuota() {
  clearTimeout(refreshTimer);
  setState("loading");

  try {
    const quota = await window.codexQuota.getQuota();
    updateQuota(quota);
    refreshTimer = setTimeout(refreshQuota, 60000);
  } catch (error) {
    els.quotaList.textContent = "";
    setState("error", `${t("error")} · ${formatClockTime(new Date())}`);
    refreshTimer = setTimeout(refreshQuota, 60000);
  }
}

async function bootstrap() {
  const theme = loadTheme();
  els.bgColorInput.value = theme.backgroundColor;
  els.textColorInput.value = theme.textColor;
  els.opacityInput.value = String(theme.opacity);
  applyTheme(theme);
  applyLabels();

  if (window.codexQuota) {
    isAlwaysOnTop = await window.codexQuota.getAlwaysOnTop();
    updatePinButton();
  }

  els.langBtn.addEventListener("click", () => {
    language = language === "zh" ? "en" : "zh";
    localStorage.setItem("language", language);
    applyLabels();
    refreshQuota();
  });

  els.paletteBtn.addEventListener("click", () => {
    toggleThemePanel();
  });
  els.bgColorInput.addEventListener("input", updateBackgroundTheme);
  els.textColorInput.addEventListener("input", updateThemeFromControls);
  els.opacityInput.addEventListener("input", updateThemeFromControls);
  els.themeOverlay.addEventListener("pointerdown", closeThemePanel);
  document.addEventListener("pointerdown", closeThemePanelOnMenuOutsideClick, true);
  els.refreshBtn.addEventListener("click", refreshQuota);
  els.minimizeBtn.addEventListener("click", () => window.codexQuota?.minimize());
  els.closeBtn.addEventListener("click", () => window.codexQuota?.close());
  initResizeHandles();
  els.pinBtn.addEventListener("click", async () => {
    isAlwaysOnTop = await window.codexQuota.setAlwaysOnTop(!isAlwaysOnTop);
    updatePinButton();
  });

  window.codexQuota?.onRefresh(refreshQuota);
  window.codexQuota?.onAlwaysOnTopChanged((value) => {
    isAlwaysOnTop = value;
    updatePinButton();
  });

  refreshQuota();
}

bootstrap();

function initResizeHandles() {
  for (const handle of document.querySelectorAll(".resize-handle")) {
    handle.addEventListener("pointerdown", startWindowResize);
  }
}

async function startWindowResize(event) {
  if (!window.codexQuota?.getWindowBounds || !window.codexQuota?.setWindowBounds) return;
  event.preventDefault();
  event.stopPropagation();

  const handle = event.currentTarget;
  const edge = handle.dataset.edge || "";
  const startBounds = await window.codexQuota.getWindowBounds();
  const startX = event.screenX;
  const startY = event.screenY;

  handle.setPointerCapture?.(event.pointerId);

  const onPointerMove = (moveEvent) => {
    const dx = moveEvent.screenX - startX;
    const dy = moveEvent.screenY - startY;
    window.codexQuota.setWindowBounds(calculateResizeBounds(startBounds, edge, dx, dy));
  };

  const onPointerUp = () => {
    handle.releasePointerCapture?.(event.pointerId);
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
    window.removeEventListener("pointercancel", onPointerUp);
  };

  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
  window.addEventListener("pointercancel", onPointerUp);
}

function calculateResizeBounds(startBounds, edge, dx, dy) {
  const next = { ...startBounds };

  if (edge.includes("s")) {
    next.height = Math.max(MIN_WINDOW_HEIGHT, Math.min(MAX_WINDOW_HEIGHT, startBounds.height + dy));
  }

  if (edge.includes("n")) {
    const height = Math.max(MIN_WINDOW_HEIGHT, Math.min(MAX_WINDOW_HEIGHT, startBounds.height - dy));
    next.y = startBounds.y + (startBounds.height - height);
    next.height = height;
  }

  next.width = FIXED_WINDOW_WIDTH;
  return next;
}

function toggleThemePanel() {
  const willOpen = els.themePanel.hidden;
  els.themePanel.hidden = !willOpen;
  els.themeOverlay.hidden = !willOpen;
  els.paletteBtn.classList.toggle("active", willOpen);
}

function closeThemePanelOnMenuOutsideClick(event) {
  if (els.themePanel.hidden) return;
  if (els.themePanel.contains(event.target) || els.paletteBtn.contains(event.target)) return;

  closeThemePanel();
}

function closeThemePanel() {
  updateThemeFromControls();
  els.themePanel.hidden = true;
  els.themeOverlay.hidden = true;
  els.paletteBtn.classList.remove("active");
}
