#!/usr/bin/env node
import http from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import { join, resolve, extname, normalize } from "node:path";

const root = resolve(process.env.SERVE_DIST_ROOT || "dist");
const host = process.env.SERVE_DIST_HOST || "127.0.0.1";
const port = Number(process.env.SERVE_DIST_PORT || process.argv[2] || 8765);
const shutdownTimeoutMs = Number(process.env.SERVE_DIST_SHUTDOWN_TIMEOUT_MS || 3000);

const types = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
};

function log(event, fields = {}) {
  const detail = Object.entries(fields)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${key}=${String(value)}`)
    .join(" ");
  console.log(`[serve-dist] ${new Date().toISOString()} ${event}${detail ? ` ${detail}` : ""}`);
}

function send(res, status, body) {
  res.writeHead(status, { "content-type": "text/plain; charset=utf-8" });
  res.end(body);
}

function fileFor(urlPath) {
  const decoded = decodeURIComponent(urlPath.split("?")[0]);
  const safe = normalize(decoded).replace(/^(\.\.[/\\])+/, "");
  let path = resolve(join(root, safe));
  if (!path.startsWith(root)) return null;
  if (existsSync(path) && statSync(path).isDirectory()) {
    path = join(path, "index.html");
  }
  if (!existsSync(path) && !extname(path)) {
    path = join(path, "index.html");
  }
  return path.startsWith(root) ? path : null;
}

const server = http.createServer((req, res) => {
  const path = fileFor(req.url || "/");
  if (!path || !existsSync(path) || !statSync(path).isFile()) {
    send(res, 404, "not found");
    return;
  }
  res.writeHead(200, { "content-type": types[extname(path)] || "application/octet-stream" });
  createReadStream(path).pipe(res);
});

log("starting", { root, host, port, pid: process.pid });

server.listen(port, host, () => {
  log("listening", { url: `http://${host}:${port}`, root });
});

server.on("error", (error) => {
  log("error", { code: error.code, message: error.message });
  process.exitCode = 1;
});

let shuttingDown = false;

function shutdown(signal) {
  if (shuttingDown) {
    log("shutdown-already-in-progress", { signal });
    return;
  }
  shuttingDown = true;
  log("shutdown-requested", { signal, timeout_ms: shutdownTimeoutMs });

  const forceExit = setTimeout(() => {
    log("shutdown-timeout", { signal, timeout_ms: shutdownTimeoutMs });
    process.exit(0);
  }, shutdownTimeoutMs);
  forceExit.unref();

  log("server-close-start", { signal });
  server.close((error) => {
    if (error) {
      log("server-close-error", { signal, message: error.message });
      process.exitCode = 1;
    } else {
      log("server-close-complete", { signal });
    }
    clearTimeout(forceExit);
    process.exit(process.exitCode || 0);
  });
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
