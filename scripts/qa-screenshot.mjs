import { chromium, devices } from "playwright";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "..", "qa-shots");
fs.mkdirSync(OUT, { recursive: true });

const pages = [
  ["home", "/"],
  ["about", "/about/"],
  ["portfolio", "/portfolio/"],
  ["credentials", "/credentials/"],
  ["contact", "/contact/"],
];

async function shot(page, name, suffix) {
  const file = path.join(OUT, `${name}-${suffix}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log("wrote", file);
}

const browser = await chromium.launch();
const desktop = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  colorScheme: "dark",
});
const mobile = await browser.newContext({
  ...devices["iPhone 13"],
  colorScheme: "dark",
});

for (const [name, route] of pages) {
  const d = await desktop.newPage();
  await d.goto(`http://127.0.0.1:8765${route}`, { waitUntil: "networkidle" });
  await d.waitForTimeout(500);
  await shot(d, name, "desktop");
  const issues = await d.evaluate(() => {
    const out = [];
    for (const img of document.images) {
      if (!img.complete || img.naturalWidth === 0) out.push(`broken-img:${img.src}`);
    }
    if (document.documentElement.scrollWidth > window.innerWidth + 2) {
      out.push(
        `horizontal-overflow:${document.documentElement.scrollWidth}>${window.innerWidth}`
      );
    }
    const search = document.querySelector("#search .pagefind-ui__search-input");
    if (search) {
      const cs = getComputedStyle(search);
      out.push(
        `search-bg:${cs.backgroundColor};search-color:${cs.color};search-border:${cs.borderColor}`
      );
    }
    const nav = document.querySelector(".site-nav");
    if (nav) out.push(`nav-height:${Math.round(nav.getBoundingClientRect().height)}`);
    out.push(`iframes:${document.querySelectorAll("iframe").length}`);
    // long bare URLs
    let longLinks = 0;
    for (const a of document.querySelectorAll("a")) {
      if ((a.textContent || "").trim().length > 60) longLinks += 1;
    }
    out.push(`long-link-labels:${longLinks}`);
    return out;
  });
  console.log(name, "desktop-meta", JSON.stringify(issues));
  await d.close();

  const m = await mobile.newPage();
  await m.goto(`http://127.0.0.1:8765${route}`, { waitUntil: "networkidle" });
  await m.waitForTimeout(500);
  await shot(m, name, "mobile");
  const mIssues = await m.evaluate(() => {
    const out = [];
    if (document.documentElement.scrollWidth > window.innerWidth + 2) {
      out.push(
        `horizontal-overflow:${document.documentElement.scrollWidth}>${window.innerWidth}`
      );
    }
    const nav = document.querySelector(".site-nav");
    if (nav) out.push(`nav-height:${Math.round(nav.getBoundingClientRect().height)}`);
    return out;
  });
  console.log(name, "mobile-meta", JSON.stringify(mIssues));
  await m.close();
}

const p = await desktop.newPage();
await p.goto("http://127.0.0.1:8765/portfolio/", { waitUntil: "networkidle" });
await p.waitForTimeout(700);
const input = p.locator(".pagefind-ui__search-input");
if ((await input.count()) > 0) {
  await input.fill("databricks");
  await p.waitForTimeout(900);
  await shot(p, "portfolio-search", "desktop");
}
await p.close();
await browser.close();
