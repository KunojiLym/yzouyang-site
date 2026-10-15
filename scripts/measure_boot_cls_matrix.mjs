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
const WIDTHS = [769, 784, 800, 900, 1024];
const ROUTES = [
  { key: "notes", path: "/notes/#NOTE-2026-005" },
  { key: "systems", path: "/systems/#SYS-03" },
  { key: "credentials", path: "/credentials/#google-cloud" },
];
const THEMES = ["dark", "light"];

function logProgress(message) {
  console.error(message);
}

function withSiteBase(path) {
  if (!SITE_BASE) return path;
  return `${SITE_BASE}${path}`;
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

async function measureCls(page, path, width, theme) {
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

const browser = await chromium.launch();
const rows = [];
try {
  for (const route of ROUTES) {
    for (const width of WIDTHS) {
      for (const theme of THEMES) {
        logProgress(`measuring ${route.key} ${width}px ${theme}…`);
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
        logProgress(`${route.key} ${width} ${theme} ${cls.toFixed(4)}`);
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}

validateRows(rows);
process.stdout.write(`${JSON.stringify(rows, null, 2)}\n`);
