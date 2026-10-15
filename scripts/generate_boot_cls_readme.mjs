#!/usr/bin/env node
/**
 * Build docs/reviews/boot-cls-2026-10-15/README.md from cls-before.json + cls-after.json.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const dir = join(dirname(fileURLToPath(import.meta.url)), "..", "docs", "reviews", "boot-cls-2026-10-15");

function loadJson(name) {
  return JSON.parse(readFileSync(join(dir, name), "utf8"));
}

function key(row) {
  return `${row.route}|${row.width}|${row.theme}`;
}

function fmt(n) {
  return typeof n === "number" ? n.toFixed(3) : "—";
}

const before = loadJson("cls-before.json");
const after = loadJson("cls-after.json");
const mapB = new Map(before.map((r) => [key(r), r.cls]));
const mapA = new Map(after.map((r) => [key(r), r.cls]));

const routes = ["notes", "systems", "credentials"];
const widths = [...new Set(after.map((r) => r.width))].sort((a, b) => a - b);
const themes = ["dark", "light"];

let md = `# Boot CLS — library deep links\n\n`;
md += `Measured with \`scripts/measure_boot_cls_matrix.mjs\` against local \`dist\` (same flow as \`library boot CLS\` e2e: \`load\` → active panel → \`document.fonts.ready\` → CLS stable). `;
md += `Tables below are generated from \`cls-before.json\` and \`cls-after.json\` via \`scripts/generate_boot_cls_readme.mjs\`. Budget **0.1**.\n\n`;
md += `## What changed\n\n`;
md += `- **Header (769–900px):** fixed \`12.5rem\` (200px) \`.header-search\` slot + \`#search\` min-height so Pagefind mount does not wrap the action row or shrink the library grid (\`chrome.css\`, pre-fix baseline \`862e9d8\`).\n`;
md += `- **Split-pane frame:** \`--library-foot-reserve\` on \`.library-shell\` plus strip/footer \`min-height\` so the painted grid no longer jumps **~376px → ~322px** when strip + footer parse after the frame (\`library.css\`).\n\n`;
md += `Playwright gate (\`library boot CLS\`): deep links @ **769**, **784**, **800**, **900**, and **1024** — all **< 0.1**.\n\n`;

for (const theme of themes) {
  md += `## ${theme}\n\n`;
  md += `| Route | ${widths.join(" | ")} |\n`;
  md += `| --- | ${widths.map(() => "---:").join(" | ")} |\n`;
  for (const route of routes) {
    const cells = widths.map((width) => {
      const b = mapB.get(`${route}|${width}|${theme}`);
      const a = mapA.get(`${route}|${width}|${theme}`);
      if (b === undefined && a === undefined) return "—";
      if (b === undefined) return fmt(a);
      return `${fmt(b)} → **${fmt(a)}**`;
    });
    md += `| ${route} | ${cells.join(" | ")} |\n`;
  }
  md += "\n";
}

md += `## Screenshots @ 784px (\`/systems/#SYS-03\`)\n\n`;
md += `Header: \`before-header-784-*.png\` → \`after-header-784-*.png\`. Viewport: \`before-systems-784-*.png\` → \`after-systems-784-*.png\`.\n`;

writeFileSync(join(dir, "README.md"), md);
console.error(`wrote ${join(dir, "README.md")}`);
