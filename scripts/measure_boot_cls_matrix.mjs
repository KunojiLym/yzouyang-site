#!/usr/bin/env node
/**
 * Boot CLS matrix for library deep links (Playwright + dist server on :8765).
 * Progress logs go to stderr; stdout is JSON only for cls-*.json consumers.
 *
 * Usage (local dist must serve chrome/styles — use root base_path):
 *   SITE_BASE_PATH= uv run python scripts/build.py --skip-pagefind && npx pagefind --site dist
 *   node scripts/serve-dist.mjs 8765 &
 *   node scripts/measure_boot_cls_matrix.mjs > docs/reviews/boot-cls-2026-10-15/cls-after.json
 *   node scripts/generate_boot_cls_readme.mjs
 */
import { chromium } from "@playwright/test";

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:8765";
const SITE_BASE = (process.env.SITE_BASE_PATH ?? "").replace(/\/$/, "");
const WIDTHS = [375, 768, 769, 784, 800, 900, 1024, 1280];
const SHIFT_WIDTHS = [769, 784, 800, 900, 1024];
const SHIFT_ROUTES = [
  { key: "notes", path: "/notes/#NOTE-2026-005" },
  { key: "systems", path: "/systems/#SYS-03" },
];
const ROUTES = [
  { key: "notes", path: "/notes/#NOTE-2026-005" },
  { key: "systems", path: "/systems/#SYS-03" },
  { key: "credentials", path: "/credentials/#google-cloud" },
];
const THEMES = ["dark", "light"];
const RUNS = Math.max(1, Number.parseInt(process.env.CLS_RUNS || "3", 10));
const SHIFT_TARGETS = ["div.library-pane", ".library-panel-body", ".library-index-control"];

function logProgress(message) {
  console.error(message);
}

function withSiteBase(path) {
  if (!SITE_BASE) return path;
  return `${SITE_BASE}${path}`;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
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

async function readShiftPositions(page) {
  return page.evaluate((targets) => {
    const map = {
      "div.library-pane": ".library-pane",
      ".library-panel-body": ".library-panel.is-active .library-panel-body",
      ".library-index-control": ".library-index-control",
    };
    const out = {};
    for (const key of targets) {
      const el = document.querySelector(map[key]);
      out[key] = el ? Math.round(el.getBoundingClientRect().y) : null;
    }
    return out;
  }, SHIFT_TARGETS);
}

async function measureElementShifts(page, path, width) {
  await page.setViewportSize({ width, height: 800 });
  await page.goto(`${BASE}${withSiteBase(path)}`, { waitUntil: "domcontentloaded" });
  const hash = new URL(path, BASE).hash.slice(1);
  if (hash) {
    await page
      .locator(
        `.library-panel[data-panel-id="${hash}"].is-active, .library-panel[data-record="${hash}"].is-active`
      )
      .first()
      .waitFor({ state: "visible", timeout: 8000 });
  }
  let bootY = null;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const booting = await page.locator("#library-split.is-booting").count();
    if (booting > 0) {
      bootY = await readShiftPositions(page);
      break;
    }
    await page.waitForTimeout(16);
  }
  if (!bootY) {
    bootY = await readShiftPositions(page);
  }
  await page.locator("#library-split:not(.is-booting)").waitFor({ state: "attached", timeout: 8000 });
  await page.evaluate(() => document.fonts.ready);
  const settledY = await readShiftPositions(page);
  const shifts = {};
  for (const key of SHIFT_TARGETS) {
    const before = bootY[key];
    const after = settledY[key];
    shifts[key] =
      before === null || after === null
        ? null
        : { beforeY: before, afterY: after, deltaY: after - before };
  }
  return shifts;
}

async function measureCls(page, path, width) {
  await page.setViewportSize({ width, height: 800 });
  await page.goto(`${BASE}${withSiteBase(path)}`, { waitUntil: "load" });
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
  return waitForClsStable(page);
}

function validateRows(rows) {
  if (!rows.length) {
    console.error("CLS capture failed: no rows");
    process.exit(1);
  }
  const values = rows.map((row) => row.cls);
  if (values.every((cls) => cls === 0)) {
    console.error("CLS capture failed: every cls value is 0 (broken capture)");
    process.exit(1);
  }
  const max = Math.max(...values);
  if (max < 0.000_5) {
    console.error(`CLS capture failed: max cls ${max} is below noise floor`);
    process.exit(1);
  }
}

function clsKey(row) {
  return `${row.route}|${row.width}|${row.theme}`;
}

function medianShiftRuns(runs) {
  const out = {};
  for (const route of SHIFT_ROUTES) {
    out[route.key] = {};
    for (const width of SHIFT_WIDTHS) {
      out[route.key][width] = {};
      for (const target of SHIFT_TARGETS) {
        const deltas = runs
          .map((run) => run?.[route.key]?.[width]?.[target]?.deltaY)
          .filter((value) => typeof value === "number");
        const befores = runs
          .map((run) => run?.[route.key]?.[width]?.[target]?.beforeY)
          .filter((value) => typeof value === "number");
        const afters = runs
          .map((run) => run?.[route.key]?.[width]?.[target]?.afterY)
          .filter((value) => typeof value === "number");
        out[route.key][width][target] = {
          beforeY: befores.length ? median(befores) : null,
          afterY: afters.length ? median(afters) : null,
          deltaY: deltas.length ? median(deltas) : null,
        };
      }
    }
  }
  return out;
}

function medianClsRuns(allRuns) {
  const buckets = new Map();
  for (const rows of allRuns) {
    for (const row of rows) {
      const key = clsKey(row);
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(row.cls);
    }
  }
  const medianRows = [];
  for (const [key, values] of buckets.entries()) {
    const [route, width, theme] = key.split("|");
    const sample = allRuns[0].find(
      (row) => row.route === route && String(row.width) === width && row.theme === theme
    );
    medianRows.push({
      route,
      path: sample.path,
      width: Number(width),
      theme,
      cls: median(values),
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
            window.__cls = 0;
            new PerformanceObserver((list) => {
              for (const entry of list.getEntries()) {
                if (!entry.hadRecentInput) window.__cls += entry.value;
              }
            }).observe({ type: "layout-shift", buffered: true });
          }, theme);
          const page = await context.newPage();
          const cls = await measureCls(page, route.path, width, theme);
          rows.push({ route: route.key, path: route.path, width, theme, cls });
          await context.close();
        }
      }
    }

    for (const route of SHIFT_ROUTES) {
      for (const width of SHIFT_WIDTHS) {
        logProgress(`run ${run + 1}: shifts ${route.key} ${width}px dark…`);
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
        const page = await context.newPage();
        shiftRun[route.key][width] = await measureElementShifts(page, route.path, width);
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
  elementShiftMedian: medianShiftRuns(shiftRuns),
};

process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
