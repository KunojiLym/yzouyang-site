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
md += `- **Library strip + footer:** \`--library-strip-min-height\` and \`--library-page-footer-min-height\` on \`.library-strip\` / \`.library-page-footer\` so strip and footer block size is stable before paint (no \`max-height\` reserve on \`.library-frame\` — that double-counted and left a ~52px gap under the footer).\n\n`;
md += `Playwright gate (\`library boot CLS\`): deep links @ **375**, **768**, **769**, **784**, **800**, **900**, **1024**, and **1280** — all **< 0.1** in \`cls-after.json\`.\n\n`;
md += `**Pane shift (Visual Design):** Removing \`.library-frame\` \`max-height\` reserve fixes the ~52px empty band under the footer and the ~19px Credentials pane jump from double-counting strip/footer. Index-control and notes reading-context **boot-only** reserves (scoped to \`.library-panel--note.is-active\`, not all mid-band widths) replace the round-4 regression that forced \`display:flex\` on \`[hidden]\` reading context for every notes route.\n\n`;

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
