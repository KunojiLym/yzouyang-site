#!/usr/bin/env node
/**
 * Computed line-height ratios for design-system text-style selectors (Playwright).
 * Stdin: JSON array of CSS selectors. Stdout: JSON object selector -> ratio | null.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const STYLES_DIR = process.env.TEXT_STYLE_PROBE_STYLES_DIR
  ? process.env.TEXT_STYLE_PROBE_STYLES_DIR
  : join(ROOT, "src/styles");
const STYLE_SHEETS = [
  "tokens.css",
  "base.css",
  "chrome.css",
  "components.css",
  "home.css",
  "library.css",
  "longform.css",
  "search.css",
];

const selectors = JSON.parse(readFileSync(0, "utf8"));

const probeHtml = `<!DOCTYPE html><html lang="en" data-theme="dark"><head><meta charset="utf-8" /></head><body>
<header class="site-header"><button type="button" class="theme-toggle">Theme</button></header>
<nav class="site-nav"><a href="/systems/">Systems</a></nav>
<p class="record-id">NOTE-2026-001</p>
<p class="credential-card-meta">Meta</p>
<p class="home-record-title">Record</p>
<p class="home-practice-title">Practice</p>
<main class="page"><div class="entrance"><h1>Probe h1</h1><p class="lede">Probe lede</p></div>
<div class="home-plate"><h2>Probe plate</h2></div><h2>Probe page h2</h2><h3>Probe h3</h3></main>
<article class="not-found"><h1>404</h1></article>
<div class="library-panel-header"><h2 class="library-panel-title">Probe</h2></div>
<div class="library-panel--note"><p class="note-dek">Probe dek</p><h2 class="library-panel-title">Note title</h2></div>
<div class="library-index-group--depth-0"><span class="library-index-group-label">G0</span></div>
<div class="library-index-group--depth-1"><span class="library-index-group-label">G1</span></div>
<div class="library-index-group--depth-2"><span class="library-index-group-label">G2</span></div>
<div class="note-body prose"><p class="note-dropcap">Dropcap paragraph text.</p>
<blockquote class="note-blockquote"><p>Probe quote</p></blockquote></div>
</body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setContent(probeHtml, { waitUntil: "domcontentloaded" });
for (const name of STYLE_SHEETS) {
  const css = readFileSync(join(STYLES_DIR, name), "utf8");
  await page.addStyleTag({ content: css });
}
await page.evaluate(() => document.fonts.ready);

const ratios = await page.evaluate((sels) => {
  const out = {};
  for (const sel of sels) {
    let style = null;
    if (sel === ".note-body.prose .note-dropcap") {
      const el = document.querySelector(".note-body.prose p.note-dropcap");
      if (el) style = getComputedStyle(el, "::first-letter");
    } else {
      const el = document.querySelector(sel);
      if (el) style = getComputedStyle(el);
    }
    if (!style) {
      out[sel] = null;
      continue;
    }
    const fontSize = Number.parseFloat(style.fontSize);
    const lineHeight = style.lineHeight;
    if (!Number.isFinite(fontSize) || fontSize <= 0) {
      out[sel] = null;
      continue;
    }
    if (lineHeight.endsWith("px")) {
      out[sel] = Number.parseFloat(lineHeight) / fontSize;
    } else {
      const parsed = Number.parseFloat(lineHeight);
      out[sel] = Number.isFinite(parsed) ? parsed : null;
    }
  }
  return out;
}, selectors);

await browser.close();
process.stdout.write(`${JSON.stringify(ratios)}\n`);
