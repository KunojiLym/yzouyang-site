#!/usr/bin/env node
/**
 * Computed line-height ratios from built dist pages (Playwright).
 * Stdin: JSON { distDir?, stylesDir?, probes: Array<{ page, selector, width? }> }
 *        or legacy JSON array of selector strings (uses default probe map).
 * Stdout: JSON object selector -> ratio | null.
 */
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DEFAULT_DIST = join(ROOT, "dist");
const DEFAULT_STYLES = join(ROOT, "src/styles");

function listStylesheets(stylesDir) {
  return readdirSync(stylesDir)
    .filter((name) => name.endsWith(".css"))
    .sort()
    .map((name) => join(stylesDir, name));
}

function defaultProbeForSelector(selector) {
  if (
    selector.includes("home-") ||
    selector.includes("home-plate") ||
    selector === ".entrance .lede" ||
    selector.startsWith(".entrance") ||
    selector.includes("site-nav") ||
    selector.includes("header-actions")
  ) {
    if (selector === ".home-snap-proposition .lede") {
      return { page: "index.html", width: 900 };
    }
    if (selector === ".entrance .lede") {
      return { page: "index.html", width: 800 };
    }
    return { page: "index.html", width: 1280 };
  }
  if (selector.includes("not-found")) {
    return { page: "404.html", width: 1280 };
  }
  if (selector.includes("note-dropcap") || selector.includes("note-body")) {
    return { page: "notes/index.html", width: 1280 };
  }
  if (selector.includes("credential") || selector.includes("issuer")) {
    return { page: "credentials/index.html", width: 1280 };
  }
  if (selector.includes("library-") || selector.includes("note-")) {
    return { page: "notes/index.html", width: 1280 };
  }
  return { page: "systems/index.html", width: 1280 };
}

function parseInput(raw) {
  const parsed = JSON.parse(raw);
  if (Array.isArray(parsed)) {
    return {
      distDir: process.env.TEXT_STYLE_PROBE_DIST || DEFAULT_DIST,
      stylesDir: process.env.TEXT_STYLE_PROBE_STYLES_DIR || DEFAULT_STYLES,
      overrideStyles: Boolean(process.env.TEXT_STYLE_PROBE_STYLES_DIR),
      probes: parsed.map((selector) => ({
        selector,
        ...defaultProbeForSelector(selector),
      })),
    };
  }
  const stylesDir = parsed.stylesDir || process.env.TEXT_STYLE_PROBE_STYLES_DIR || DEFAULT_STYLES;
  return {
    distDir: parsed.distDir || process.env.TEXT_STYLE_PROBE_DIST || DEFAULT_DIST,
    stylesDir,
    overrideStyles: Boolean(parsed.overrideStyles ?? process.env.TEXT_STYLE_PROBE_STYLES_DIR),
    probes: parsed.probes || [],
  };
}

function syntheticProbeHtml() {
  return `<!DOCTYPE html>
<html lang="en" data-theme="dark">
  <head><meta charset="utf-8" /></head>
  <body>
    <header class="site-header"><div class="header-actions"><nav class="site-nav"><a href="/systems/">Systems</a></nav></div></header>
    <main class="page library-route" data-library-route="notes">
      <div class="home-snap-proposition"><p class="lede">Home lede</p></div>
      <div class="entrance"><h1>Probe h1</h1><p class="lede">Entrance lede</p></div>
      <div class="home-plate"><h2>Probe plate</h2></div>
      <h2>Probe page h2</h2>
      <h3>Probe h3</h3>
      <div class="library-panel-header"><h2 class="library-panel-title">Probe</h2></div>
      <article class="library-panel library-panel--note is-active">
        <h2 class="library-panel-title">Note title</h2>
        <p class="note-dek">Probe dek</p>
        <div class="note-body prose"><p class="note-dropcap">Dropcap paragraph text.</p></div>
      </article>
      <div class="library-index-group--depth-2"><span class="library-index-group-label">G2</span></div>
      <p class="record-id">NOTE-2026-001</p>
      <p class="credential-card-meta">Meta</p>
    </main>
    <article class="not-found"><h1>404</h1></article>
  </body>
</html>`;
}

function localizeDistHtml(html, distDir) {
  const assetsRoot = join(distDir, "assets").replace(/\\/g, "/");
  return html
    .replace(/href="\//g, `href="file://${distDir.replace(/\\/g, "/")}/`)
    .replace(/src="\//g, `src="file://${distDir.replace(/\\/g, "/")}/`)
    .replaceAll(`file://${distDir.replace(/\\/g, "/")}/assets/`, `file://${assetsRoot}/`);
}

const input = parseInput(readFileSync(0, "utf8"));
const styleFiles = listStylesheets(input.stylesDir);
const bundledCssPath = join(input.distDir, "styles.css");
const useBundledCss = !input.overrideStyles && existsSync(bundledCssPath);

const browser = await chromium.launch();
const ratios = {};

for (const probe of input.probes) {
  const selector = probe.selector;
  if (!selector || ratios[selector] !== undefined) {
    continue;
  }
  const pagePath = join(input.distDir, probe.page);
  const width = probe.width ?? 1280;
  const page = await browser.newPage({ viewport: { width, height: 800 } });
  let html = existsSync(pagePath)
    ? localizeDistHtml(readFileSync(pagePath, "utf8"), input.distDir)
    : syntheticProbeHtml();
  await page.setContent(html, { waitUntil: "domcontentloaded" });
  if (useBundledCss) {
    const css = readFileSync(bundledCssPath, "utf8");
    await page.addStyleTag({ content: css });
  } else {
    for (const cssPath of styleFiles) {
      const css = readFileSync(cssPath, "utf8");
      await page.addStyleTag({ content: css });
    }
  }
  await page.evaluate(() => document.fonts.ready);

  const ratio = await page.evaluate((sel) => {
    let style = null;
    if (sel === ".note-body.prose .note-dropcap") {
      const el = document.querySelector(".note-body.prose p.note-dropcap")
        || document.querySelector(".note-body.prose > p:first-of-type");
      if (el) style = getComputedStyle(el, "::first-letter");
    } else if (sel === ".entrance .lede") {
      const el =
        document.querySelector(".home-snap-proposition .lede")
        || document.querySelector(".entrance .lede");
      if (el) style = getComputedStyle(el);
    } else if (sel === ".library-index-group--depth-2 > .library-index-group-label") {
      const el =
        document.querySelector(".library-index-group--depth-2 > .library-index-group-label")
        || document.querySelector(".library-index-group--depth-1 > .library-index-group-label");
      if (el) style = getComputedStyle(el);
    } else {
      const el = document.querySelector(sel);
      if (el) style = getComputedStyle(el);
    }
    if (!style) return null;
    const fontSize = Number.parseFloat(style.fontSize);
    const lineHeight = style.lineHeight;
    if (!Number.isFinite(fontSize) || fontSize <= 0) return null;
    if (lineHeight.endsWith("px")) {
      return Number.parseFloat(lineHeight) / fontSize;
    }
    const parsed = Number.parseFloat(lineHeight);
    return Number.isFinite(parsed) ? parsed : null;
  }, selector);

  ratios[selector] = ratio;
  await page.close();
}

await browser.close();
process.stdout.write(`${JSON.stringify(ratios)}\n`);
