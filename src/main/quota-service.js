const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const TIMEOUT_MS = 15000;

function resolveCodexPath() {
  const candidates = [];
  if (process.env.CODEX_CLI_PATH) candidates.push(process.env.CODEX_CLI_PATH);

  const localAppData = process.env.LOCALAPPDATA || "";
  const binRoot = path.join(localAppData, "OpenAI", "Codex", "bin");
  if (fs.existsSync(binRoot)) {
    for (const dir of fs.readdirSync(binRoot).reverse()) {
      candidates.push(path.join(binRoot, dir, "codex.exe"));
    }
  }

  for (const candidate of candidates) {
    if (candidate && fs.existsSync(candidate)) return candidate;
  }
  return "codex.exe";
}

async function readQuota() {
  const child = spawn(resolveCodexPath(), ["app-server", "--listen", "stdio://"], {
    stdio: ["pipe", "pipe", "pipe"],
    windowsHide: true
  });

  let buffer = "";
  let stderr = "";
  let nextId = 1;
  const pending = new Map();

  const cleanup = () => {
    for (const request of pending.values()) clearTimeout(request.timer);
    pending.clear();
    if (!child.killed) child.kill();
  };

  const send = (method, params) => {
    const id = nextId++;
    const payload = params === undefined ? { id, method } : { id, method, params };
    child.stdin.write(`${JSON.stringify(payload)}\n`);

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error(`Codex request timed out: ${method}`));
      }, TIMEOUT_MS);
      pending.set(id, { resolve, reject, timer });
    });
  };

  child.stdout.on("data", (chunk) => {
    buffer += chunk.toString("utf8");
    let index;
    while ((index = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, index).trim();
      buffer = buffer.slice(index + 1);
      if (!line) continue;
      handleMessage(line, pending);
    }
  });

  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString("utf8");
  });

  return new Promise((resolve, reject) => {
    child.once("error", (error) => {
      cleanup();
      reject(error);
    });

    child.once("exit", (code) => {
      if (pending.size > 0) {
        cleanup();
        reject(new Error(stderr || `Codex app-server exited with code ${code}`));
      }
    });

    (async () => {
      try {
        await send("initialize", {
          clientInfo: {
            name: "codex-quota-glass-widget",
            title: "Codex Quota Glass",
            version: "1.0.0"
          },
          capabilities: null
        });
        const result = await send("account/rateLimits/read");
        cleanup();
        resolve(normalize(result));
      } catch (error) {
        cleanup();
        reject(new Error(stderr || error.message));
      }
    })();
  });
}

function handleMessage(line, pending) {
  let message;
  try {
    message = JSON.parse(line);
  } catch {
    return;
  }
  const request = pending.get(message.id);
  if (!request) return;

  clearTimeout(request.timer);
  pending.delete(message.id);

  if (message.error) request.reject(new Error(message.error.message || JSON.stringify(message.error)));
  else request.resolve(message.result);
}

function normalize(result) {
  const byId = result.rateLimitsByLimitId || {};
  const snapshot = byId.codex || result.rateLimits || Object.values(byId)[0];
  if (!snapshot) throw new Error("Codex did not return quota data.");

  const primary = normalizeWindow(snapshot.primary);
  const secondary = normalizeWindow(snapshot.secondary);
  const active = primary || secondary;

  return {
    limitName: snapshot.limitName || "Codex",
    plan: String(snapshot.planType || "unknown").toUpperCase(),
    reached: snapshot.rateLimitReachedType || null,
    primary,
    secondary,
    remainingPercent: active ? active.remainingPercent : 0,
    fetchedAt: new Date().toISOString()
  };
}

function normalizeWindow(window) {
  if (!window) return null;
  const usedPercent = clamp(Math.round(Number(window.usedPercent || 0)), 0, 100);
  return {
    usedPercent,
    remainingPercent: 100 - usedPercent,
    resetsAt: window.resetsAt ? new Date(window.resetsAt * 1000).toISOString() : null
  };
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

module.exports = { readQuota };
