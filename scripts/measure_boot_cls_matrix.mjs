#!/usr/bin/env node
/**
 * Boot CLS matrix for library deep links (Playwright + dist server on :8765).
 * Progress logs go to stderr; stdout is JSON only for cls-*.json consumers.
 *
 * Usage:
 *   node scripts/measure_boot_cls_matrix.mjs > docs/reviews/boot-cls-2026-10-15/cls-after.json
 *   node scripts/generate_boot_cls_readme.mjs
 */
import { chromium } from "@playwright/test";
const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:8765";
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

async function measureCls(path, width, theme) {
  const browser = await chromium.launch();
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
  await page.goto(`${BASE}${path}`, { waitUntil: "load" });
  const hash = new URL(path, BASE).hash.slice(1);
  if (hash) {
    await page
      .locator(
        `.library-panel[data-panel-id="${hash}"].is-active, .library-panel[data-record="${hash}"].is-active`
      )
      .first()
      .waitFor({ state: "visible", timeout: 8000 });
  }
  await page.evaluate(() => document.fonts.ready);
  let last = null;
  let rounds = 0;
  const deadline = Date.now() + 12_000;
  while (Date.now() < deadline) {
    await page.waitForTimeout(500);
    const value = await page.evaluate(() => window.__cls || 0);
    if (last !== null && value === last) {
      rounds += 1;
      if (rounds >= 3) {
        await browser.close();
        return value;
      }
    } else {
      rounds = 0;
      last = value;
    }
  }
  const final = await page.evaluate(() => window.__cls || 0);
  await browser.close();
  return final;
}

const rows = [];
for (const route of ROUTES) {
  for (const width of WIDTHS) {
    for (const theme of THEMES) {
      logProgress(`measuring ${route.key} ${width}px ${theme}…`);
      const cls = await measureCls(route.path, width, theme);
      rows.push({ route: route.key, path: route.path, width, theme, cls });
      logProgress(`${route.key} ${width} ${theme} ${cls.toFixed(4)}`);
    }
  }
}

process.stdout.write(`${JSON.stringify(rows, null, 2)}\n`);
