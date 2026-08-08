import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

export const PORT = Number(process.env.E2E_PORT || 8765);
export const HOST = process.env.E2E_HOST || "127.0.0.1";
export const BASE_URL = process.env.E2E_BASE_URL || `http://${HOST}:${PORT}`;

const STATE_FILE = resolve("test-results", "e2e-server-state.json");
const READY_TIMEOUT_MS = Number(process.env.E2E_SERVER_READY_TIMEOUT_MS || 30_000);
const TEARDOWN_TIMEOUT_MS = Number(process.env.E2E_SERVER_TEARDOWN_TIMEOUT_MS || 5_000);

function log(event, fields = {}) {
  const detail = Object.entries(fields)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${key}=${String(value)}`)
    .join(" ");
  console.log(`[e2e-server] ${new Date().toISOString()} ${event}${detail ? ` ${detail}` : ""}`);
}

async function writeState(state) {
  await mkdir(dirname(STATE_FILE), { recursive: true });
  await writeFile(STATE_FILE, `${JSON.stringify(state, null, 2)}\n`, "utf8");
}

async function readState() {
  try {
    return JSON.parse(await readFile(STATE_FILE, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

async function removeState() {
  await rm(STATE_FILE, { force: true });
}

async function isReady(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1000);
  try {
    const response = await fetch(url, { signal: controller.signal });
    return response.status < 500;
  } catch {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

async function waitForReady(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await isReady(url)) return true;
    await new Promise((resolveWait) => setTimeout(resolveWait, 250));
  }
  return false;
}

function processExists(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function waitForExit(pid, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (!processExists(pid)) return true;
    await new Promise((resolveWait) => setTimeout(resolveWait, 250));
  }
  return !processExists(pid);
}

export async function startE2EServer() {
  const root = resolve("dist");
  log("setup-start", { base_url: BASE_URL, root });

  if (await isReady(BASE_URL)) {
    log("reuse-existing-server", { base_url: BASE_URL });
    await writeState({ reused: true, baseURL: BASE_URL });
    return;
  }

  if (!existsSync(root)) {
    log("dist-missing", { root });
    throw new Error(`Cannot start e2e server because ${root} does not exist. Run the site build first.`);
  }

  log("node-server-start", { script: "scripts/serve-dist.mjs", host: HOST, port: PORT });
  const child = spawn(process.execPath, ["scripts/serve-dist.mjs", String(PORT)], {
    cwd: process.cwd(),
    env: {
      ...process.env,
      SERVE_DIST_HOST: HOST,
      SERVE_DIST_PORT: String(PORT),
    },
    stdio: "inherit",
    windowsHide: true,
  });
  child.unref();

  log("node-server-spawned", { pid: child.pid });

  if (!(await waitForReady(BASE_URL, READY_TIMEOUT_MS))) {
    log("node-server-ready-timeout", { pid: child.pid, timeout_ms: READY_TIMEOUT_MS });
    if (child.pid) {
      try {
        process.kill(child.pid, "SIGTERM");
      } catch (error) {
        log("node-server-ready-timeout-kill-error", { pid: child.pid, message: error.message });
      }
    }
    throw new Error(`Timed out waiting for e2e server at ${BASE_URL}`);
  }

  await writeState({
    reused: false,
    pid: child.pid,
    baseURL: BASE_URL,
    startedAt: new Date().toISOString(),
  });
  log("node-server-ready", { pid: child.pid, base_url: BASE_URL });
}

export async function stopE2EServer() {
  log("teardown-start", { state_file: STATE_FILE });
  const state = await readState();
  if (!state) {
    log("teardown-no-state");
    return;
  }

  if (state.reused) {
    log("teardown-skip-reused-server", { base_url: state.baseURL });
    await removeState();
    return;
  }

  if (!state.pid) {
    log("teardown-missing-pid");
    await removeState();
    return;
  }

  if (!processExists(state.pid)) {
    log("node-server-already-exited", { pid: state.pid });
    await removeState();
    return;
  }

  log("node-server-stop-requested", { pid: state.pid, timeout_ms: TEARDOWN_TIMEOUT_MS });
  try {
    process.kill(state.pid, "SIGTERM");
  } catch (error) {
    log("node-server-stop-request-error", { pid: state.pid, message: error.message });
    await removeState();
    return;
  }

  if (await waitForExit(state.pid, TEARDOWN_TIMEOUT_MS)) {
    log("node-server-stop-complete", { pid: state.pid });
  } else {
    log("node-server-stop-timeout", { pid: state.pid, timeout_ms: TEARDOWN_TIMEOUT_MS });
    try {
      process.kill(state.pid, "SIGKILL");
    } catch (error) {
      log("node-server-stop-force-error", { pid: state.pid, message: error.message });
    }
    await waitForExit(state.pid, 1000);
    log("node-server-stop-forced", { pid: state.pid });
  }

  await removeState();
  log("teardown-complete");
}
