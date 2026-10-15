#!/usr/bin/env node
/**
 * Boot CLS matrix for library deep links (Playwright + dist server on :8765).
 * Progress logs go to stderr; stdout is JSON only for cls-*.json consumers.
 */
import { chromium } from "@playwright/test";

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:8765";
const SITE_BASE = (process.env.SITE_BASE_PATH ?? "").replace(/\/$/, "");
const WIDTHS = [375, 768, 769, 784, 800, 900, 1024, 1280];
const SHIFT_WIDTHS = [375, 768, 769, 784, 800, 900, 1024];
const SHIFT_ROUTES = [
  { key: "notes", path: "/notes/#NOTE-2026-005" },
  { key: "systems", path: "/systems/#SYS-03" },
  { key: "credentials", path: "/credentials/#google-cloud" },
];
const ROUTES = [
  { key: "notes", path: "/notes/#NOTE-2026-005" },
  { key: "systems", path: "/systems/#SYS-03" },
  { key: "credentials", path: "/credentials/#google-cloud" },
];
const THEMES = ["dark", "light"];
const RUNS = Math.max(1, Number.parseInt(process.env.CLS_RUNS || "3", 10));

const LAYOUT_SHIFT_INIT = () => {
  window.__layoutShiftSources = [];
  window.__layoutShiftEntryCount = 0;
  window.__layoutShiftObserverActive = false;
  try {
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.hadRecentInput) continue;
        window.__layoutShiftEntryCount += 1;
        for (const source of entry.sources || []) {
          const node = source.node;
          let label = null;
          if (node && node.nodeType === 1) {
            const el = node;
            if (el.classList?.contains("library-pane")) label = "div.library-pane";
            else if (el.classList?.contains("library-panel-body")) label = ".library-panel-body";
            else if (el.classList?.contains("library-index-control")) label = ".library-index-control";
            else if (el.classList?.contains("library-reading-context")) label = "div.library-reading-context";
            else {
              const tag = el.tagName?.toLowerCase() || "node";
              const cls = [...(el.classList || [])].slice(0, 3).join(".");
              label = cls ? `${tag}.${cls}` : tag;
            }
          }
          window.__layoutShiftSources.push({
            value: entry.value,
            startTime: entry.startTime,
            node: label,
            previousRect: {
              x: source.previousRect.x,
              y: source.previousRect.y,
              width: source.previousRect.width,
              height: source.previousRect.height,
            },
            currentRect: {
              x: source.currentRect.x,
              y: source.currentRect.y,
              width: source.currentRect.width,
              height: source.currentRect.height,
            },
          });
        }
      }
    }).observe({ type: "layout-shift", buffered: true });
    window.__layoutShiftObserverActive = true;
  } catch {
    /* ignore */
  }
  window.__cls = 0;
  try {
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) window.__cls += entry.value;
      }
    }).observe({ type: "layout-shift", buffered: true });
  } catch {
    /* ignore */
  }
};

function logProgress(message) {
  console.error(message);
}

function withSiteBase(path) {
  if (!SITE_BASE) return path;
  return `${SITE_BASE}${path}`;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  if (!sorted.length) return null;
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }
  return sorted[mid];
}

async function readClsTotal(page) {
  return page.evaluate(() => {
    let fromObserver = window.__cls || 0;
    let fromEntries = 0;
    for (const entry of performance.getEntriesByType("layout-shift")) {
      if (!entry.hadRecentInput) fromEntries += entry.value;
    }
    return Math.max(fromObserver, fromEntries);
  });
}

async function readCaptureHealth(page) {
  return page.evaluate(() => ({
    libraryShell: Boolean(document.querySelector(".library-shell")),
    librarySplit: Boolean(document.querySelector("#library-split")),
    layoutShiftEntryCount: window.__layoutShiftEntryCount || 0,
    layoutShiftSourceCount: (window.__layoutShiftSources || []).length,
    stylesheetCount: document.styleSheets?.length || 0,
    observerActive: Boolean(window.__layoutShiftObserverActive),
  }));
}

async function waitForClsStable(
  page,
  { intervalMs = 500, stableRounds = 3, timeoutMs = 12_000 } = {}
) {
  const deadline = Date.now() + timeoutMs;
  let last = null;
  let rounds = 0;
  while (Date.now() < deadline) {
    await page.waitForTimeout(intervalMs);
    const value = await readClsTotal(page);
    if (last !== null && value === last) {
      rounds += 1;
      if (rounds >= stableRounds) return value;
    } else {
      rounds = 0;
      last = value;
    }
  }
  const final = await readClsTotal(page);
  throw new Error(`CLS did not stabilize within ${timeoutMs}ms (last value ${final})`);
}

async function measureRoute(page, path, width) {
  await page.setViewportSize({ width, height: 800 });
  const response = await page.goto(`${BASE}${withSiteBase(path)}`, { waitUntil: "load" });
  if (!response || !response.ok()) {
    throw new Error(`navigation failed for ${path} @ ${width}px (${response?.status()})`);
  }
  const hash = new URL(path, BASE).hash.slice(1);
  if (hash) {
    await page
      .locator(
        `.library-panel[data-panel-id="${hash}"].is-active, .library-panel[data-record="${hash}"].is-active`
      )
      .first()
      .waitFor({ state: "visible", timeout: 8000 });
  }
  await page.locator(".library-shell").waitFor({ state: "attached", timeout: 8000 });
  await page
    .locator("#library-split:not(.is-booting)")
    .waitFor({ state: "attached", timeout: 8000 });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);
  const cls = await waitForClsStable(page);
  const capture = await readCaptureHealth(page);
  const sources = await page.evaluate(() => window.__layoutShiftSources || []);
  return { cls, capture, sources };
}

function validateRows(rows) {
  if (!rows.length) {
    console.error("CLS capture failed: no rows");
    process.exit(1);
  }
  for (const row of rows) {
    const capture = row.capture;
    if (!capture?.libraryShell || !capture?.librarySplit) {
      console.error("CLS capture failed: page shell missing", row);
      process.exit(1);
    }
    if (!capture.stylesheetCount) {
      console.error("CLS capture failed: no stylesheets", row);
      process.exit(1);
    }
    if (!capture.observerActive) {
      console.error("CLS capture failed: layout-shift observer not active", row);
      process.exit(1);
    }
  }
}

function clsKey(row) {
  return `${row.route}|${row.width}|${row.theme}`;
}

const SHIFT_TRACK_NODES = ["div.library-pane", ".library-panel-body", "div.library-panels"];

function jumpCountsRuns(runs) {
  const out = {};
  for (const route of SHIFT_ROUTES) {
    out[route.key] = {};
    for (const width of SHIFT_WIDTHS) {
      out[route.key][width] = {};
      for (const node of SHIFT_TRACK_NODES) {
        let jumps = 0;
        for (const run of runs) {
          const list = run?.[route.key]?.[width] || [];
          const item = list.find((entry) => entry.node === node);
          if (!item) continue;
          const dy = Math.abs((item.currentRect?.y ?? 0) - (item.previousRect?.y ?? 0));
          if (dy > 5) jumps += 1;
        }
        out[route.key][width][node] = jumps;
      }
    }
  }
  return out;
}

function medianSourcesRuns(runs) {
  const out = {};
  for (const route of SHIFT_ROUTES) {
    out[route.key] = {};
    for (const width of SHIFT_WIDTHS) {
      const buckets = new Map();
      for (const run of runs) {
        const list = run?.[route.key]?.[width] || [];
        for (const item of list) {
          const key = item.node || "unknown";
          if (!buckets.has(key)) buckets.set(key, []);
          buckets.get(key).push(item);
        }
      }
      const merged = [];
      for (const [node, items] of buckets.entries()) {
        merged.push({
          node,
          count: items.length,
          value: median(items.map((i) => i.value)),
          startTime: median(items.map((i) => i.startTime)),
          previousRect: {
            x: median(items.map((i) => i.previousRect.x)),
            y: median(items.map((i) => i.previousRect.y)),
            width: median(items.map((i) => i.previousRect.width)),
            height: median(items.map((i) => i.previousRect.height)),
          },
          currentRect: {
            x: median(items.map((i) => i.currentRect.x)),
            y: median(items.map((i) => i.currentRect.y)),
            width: median(items.map((i) => i.currentRect.width)),
            height: median(items.map((i) => i.currentRect.height)),
          },
        });
      }
      merged.sort((a, b) => (b.value || 0) - (a.value || 0));
      out[route.key][width] = merged;
    }
  }
  return out;
}

function medianClsRuns(allRuns) {
  const buckets = new Map();
  const captureBuckets = new Map();
  for (const rows of allRuns) {
    for (const row of rows) {
      const key = clsKey(row);
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(row.cls);
      if (!captureBuckets.has(key)) captureBuckets.set(key, []);
      captureBuckets.get(key).push(row.capture);
    }
  }
  const medianRows = [];
  for (const [key, values] of buckets.entries()) {
    const [route, width, theme] = key.split("|");
    const sample = allRuns[0].find(
      (row) => row.route === route && String(row.width) === width && row.theme === theme
    );
    const captures = captureBuckets.get(key) || [];
    const capture = captures[Math.floor(captures.length / 2)] || sample?.capture;
    medianRows.push({
      route,
      path: sample.path,
      width: Number(width),
      theme,
      cls: median(values),
      capture,
    });
  }
  medianRows.sort(
    (a, b) =>
      a.route.localeCompare(b.route) ||
      a.width - b.width ||
      a.theme.localeCompare(b.theme)
  );
  return medianRows;
}

const browser = await chromium.launch();
const clsRuns = [];
const shiftRuns = [];

try {
  for (let run = 0; run < RUNS; run += 1) {
    logProgress(`CLS matrix run ${run + 1}/${RUNS}…`);
    const rows = [];
    const shiftRun = {};
    for (const route of SHIFT_ROUTES) {
      shiftRun[route.key] = {};
    }

    for (const route of ROUTES) {
      for (const width of WIDTHS) {
        for (const theme of THEMES) {
          logProgress(`run ${run + 1}: ${route.key} ${width}px ${theme}…`);
          const context = await browser.newContext({
            viewport: { width, height: 800 },
            colorScheme: theme === "light" ? "light" : "dark",
          });
          await context.addInitScript((t) => {
            try {
              localStorage.clear();
              localStorage.setItem("yz-theme", t);
            } catch {
              /* ignore */
            }
          }, theme);
          await context.addInitScript(LAYOUT_SHIFT_INIT);
          const page = await context.newPage();
          const result = await measureRoute(page, route.path, width);
          rows.push({
            route: route.key,
            path: route.path,
            width,
            theme,
            cls: result.cls,
            capture: result.capture,
          });
          await context.close();
        }
      }
    }

    for (const route of SHIFT_ROUTES) {
      for (const width of SHIFT_WIDTHS) {
        logProgress(`run ${run + 1}: layout-shift sources ${route.key} ${width}px dark…`);
        const context = await browser.newContext({
          viewport: { width, height: 800 },
          colorScheme: "dark",
        });
        await context.addInitScript(() => {
          try {
            localStorage.clear();
            localStorage.setItem("yz-theme", "dark");
          } catch {
            /* ignore */
          }
        });
        await context.addInitScript(LAYOUT_SHIFT_INIT);
        const page = await context.newPage();
        const result = await measureRoute(page, route.path, width);
        shiftRun[route.key][width] = result.sources;
        await context.close();
      }
    }

    clsRuns.push(rows);
    shiftRuns.push(shiftRun);
  }
} finally {
  await browser.close();
}

const cls = medianClsRuns(clsRuns);
validateRows(cls);

const payload = {
  runs: RUNS,
  cls,
  layoutShiftSourcesMedian: medianSourcesRuns(shiftRuns),
  layoutShiftJumpCounts: jumpCountsRuns(shiftRuns),
};

process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
