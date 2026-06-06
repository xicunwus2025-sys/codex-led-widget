const sizeOrder = ["medium", "small"];
const stateLabels = { ok: "Green", warn: "Yellow", danger: "Red", loading: "Loading" };

const els = {
  body: document.body,
  led: document.getElementById("led"),
  stateText: document.getElementById("stateText"),
  refreshBtn: document.getElementById("refreshBtn"),
  closeBtn: document.getElementById("closeBtn"),
  liquid: document.getElementById("liquid"),
  remaining: document.getElementById("remaining"),
  primaryText: document.getElementById("primaryText"),
  secondaryText: document.getElementById("secondaryText"),
  planText: document.getElementById("planText"),
  planBadge: document.getElementById("planBadge"),
  peekPrimary: document.getElementById("peekPrimary"),
  peekSecondary: document.getElementById("peekSecondary"),
  peekPlan: document.getElementById("peekPlan"),
  statusText: document.getElementById("statusText"),
  shell: document.querySelector(".shell"),
  orb: document.querySelector(".orb")
};

let currentSize = "medium";
let refreshTimer = null;
let loading = false;
let hasRenderedQuota = false;
let dragStart = null;
let dragWindow = null;
let didDrag = false;
let hoverTimer = null;
let isPeekOpen = false;

function setSize(size) {
  currentSize = size;
  els.body.dataset.size = size;
}

function nextSize() {
  const index = sizeOrder.indexOf(currentSize);
  return sizeOrder[(index + 1) % sizeOrder.length];
}

function setState(state) {
  els.body.dataset.state = state;
  els.stateText.textContent = stateLabels[state] || state;
}

function classify(remaining) {
  if (remaining <= 0) return "danger";
  if (remaining < 10) return "warn";
  return "ok";
}

function formatWindow(window) {
  if (!window) return "--";
  const reset = formatReset(window.resetsAt);
  return reset ? `${window.remainingPercent}% / ${reset}` : `${window.remainingPercent}%`;
}

function formatReset(value) {
  if (!value) return "";
  const ms = new Date(value).getTime() - Date.now();
  if (!Number.isFinite(ms) || ms <= 0) return "";
  const totalMins = Math.max(1, Math.round(ms / 60000));
  const days = Math.floor(totalMins / 1440);
  const hours = Math.floor((totalMins % 1440) / 60);
  const mins = totalMins % 60;
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

async function refresh() {
  if (loading) return;
  loading = true;
  if (!hasRenderedQuota) {
    setState("loading");
    els.statusText.textContent = "Reading Codex quota...";
  } else {
    els.statusText.textContent = "Refreshing...";
  }
  try {
    const data = await window.quotaWidget.readQuota();
    const remaining = Number.isFinite(data.remainingPercent) ? data.remainingPercent : 0;
    setState(classify(remaining));
    els.remaining.textContent = `${remaining}%`;
    els.liquid.style.height = `${remaining}%`;
    els.primaryText.textContent = formatWindow(data.primary);
    els.secondaryText.textContent = formatWindow(data.secondary);
    els.planText.textContent = data.plan || "--";
    els.planBadge.textContent = data.plan || "--";
    els.peekPrimary.textContent = formatWindow(data.primary);
    els.peekSecondary.textContent = formatWindow(data.secondary);
    els.peekPlan.textContent = data.plan || "--";
    els.statusText.textContent = `Updated ${new Date(data.fetchedAt).toLocaleTimeString()} / auto refresh 60s`;
    hasRenderedQuota = true;
  } catch (error) {
    if (!hasRenderedQuota) {
      setState("danger");
      els.remaining.textContent = "--%";
      els.liquid.style.height = "0%";
      els.primaryText.textContent = "--";
      els.secondaryText.textContent = "--";
      els.planText.textContent = "--";
    }
    els.statusText.textContent = error.message || "Unable to read Codex quota";
  } finally {
    loading = false;
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(refresh, 60000);
  }
}

document.addEventListener("pointerdown", async (event) => {
  if (event.button !== 0 || event.target.closest("button")) return;
  clearTimeout(hoverTimer);
  dragStart = { x: event.screenX, y: event.screenY };
  dragWindow = await window.quotaWidget.getBounds();
  didDrag = false;
  event.target.setPointerCapture?.(event.pointerId);
});

document.addEventListener("pointermove", (event) => {
  if (!dragStart || !dragWindow) return;
  const dx = event.screenX - dragStart.x;
  const dy = event.screenY - dragStart.y;
  if (Math.abs(dx) + Math.abs(dy) < 2) return;
  didDrag = true;
  window.quotaWidget.moveTo(dragWindow.x + dx, dragWindow.y + dy);
});

document.addEventListener("pointerup", () => {
  dragStart = null;
  dragWindow = null;
  setTimeout(() => {
    didDrag = false;
  }, 0);
});

document.addEventListener("dblclick", async (event) => {
  if (didDrag || event.target.closest("button")) return;
  if (isPeekOpen) await closePeek();
  const size = nextSize();
  setSize(size);
  setSize(await window.quotaWidget.setSize(size));
});

function getOrbScreenCenter() {
  const orb = els.orb.getBoundingClientRect();
  return window.quotaWidget.getBounds().then((bounds) => ({
    x: bounds.x + orb.left + orb.width / 2,
    y: bounds.y + orb.top + orb.height / 2
  }));
}

async function openPeek() {
  if (currentSize !== "small" || isPeekOpen || didDrag) return;
  const center = await getOrbScreenCenter();
  const direction = await window.quotaWidget.showPeek(center.x, center.y);
  if (direction === "none") return;
  els.body.dataset.peek = direction;
  isPeekOpen = true;
}

async function closePeek() {
  if (!isPeekOpen) return;
  const center = await getOrbScreenCenter();
  els.body.dataset.peek = "none";
  await window.quotaWidget.hidePeek(center.x, center.y);
  isPeekOpen = false;
}

function schedulePeek() {
  clearTimeout(hoverTimer);
  hoverTimer = setTimeout(openPeek, 650);
}

function cancelPeek() {
  clearTimeout(hoverTimer);
  closePeek();
}

els.shell.addEventListener("pointerenter", schedulePeek);
els.shell.addEventListener("pointerleave", cancelPeek);
els.orb.addEventListener("pointerenter", schedulePeek);

els.refreshBtn.addEventListener("click", refresh);
els.closeBtn.addEventListener("click", () => window.quotaWidget.close());

(async function boot() {
  setSize(await window.quotaWidget.getSize());
  await refresh();
})();
