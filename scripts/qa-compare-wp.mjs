import { chromium, devices } from "playwright";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "..", "qa-shots", "compare");
fs.mkdirSync(OUT, { recursive: true });

const pairs = [
  ["home", "https://www.yzouyang.com/", "http://127.0.0.1:8765/"],
  ["about", "https://www.yzouyang.com/about/", "http://127.0.0.1:8765/about/"],
  ["portfolio", "https://www.yzouyang.com/portfolio/", "http://127.0.0.1:8765/portfolio/"],
  ["credentials", "https://www.yzouyang.com/credentials/", "http://127.0.0.1:8765/credentials/"],
];

async function meta(page, label) {
  return page.evaluate((src) => {
    const h1 = document.querySelector("h1");
    const title = document.title;
    const navLinks = [...document.querySelectorAll("nav a, .site-nav a, .main-navigation a, #menu-main-menu a")]
      .map((a) => (a.textContent || "").trim())
      .filter(Boolean)
      .slice(0, 20);
    const uniqueNav = [...new Set(navLinks)];
    const bg = getComputedStyle(document.body).backgroundColor;
    const color = getComputedStyle(document.body).color;
    const imgs = [...document.images].filter((i) => i.naturalWidth > 0).length;
    const iframes = document.querySelectorAll("iframe").length;
    const posts = document.querySelectorAll("article, .post, .blog-card, .entry").length;
    const ctas = [...document.querySelectorAll("a")]
      .map((a) => (a.textContent || "").trim())
      .filter((t) => /about|portfolio|credential|contact|view/i.test(t))
      .slice(0, 12);
    return {
      src,
      title,
      h1: h1 ? h1.textContent.trim().slice(0, 80) : null,
      bg,
      color,
      imgs,
      iframes,
      postsApprox: posts,
      nav: uniqueNav,
      sampleCtas: [...new Set(ctas)].slice(0, 8),
      scrollH: document.documentElement.scrollHeight,
    };
  }, label);
}

const browser = await chromium.launch();
const desktop = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  colorScheme: "light", // WP is light; compare both under light for WP fidelity
});
const desktopDark = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  colorScheme: "dark",
});
const mobile = await browser.newContext({
  ...devices["iPhone 13"],
  colorScheme: "light",
});

const report = [];

for (const [name, wp, local] of pairs) {
  for (const [ctx, suffix, url, kind] of [
    [desktop, "wp-desktop", wp, "wp"],
    [desktopDark, "static-desktop-dark", local, "static"],
    [desktop, "static-desktop-light", local, "static"],
    [mobile, "wp-mobile", wp, "wp"],
    [mobile, "static-mobile", local, "static"],
  ]) {
    const page = await ctx.newPage();
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(1200);
      const file = path.join(OUT, `${name}-${suffix}.png`);
      await page.screenshot({ path: file, fullPage: false });
      const m = await meta(page, kind);
      m.file = path.basename(file);
      m.page = name;
      m.kind = kind;
      m.suffix = suffix;
      report.push(m);
      console.log("wrote", file);
    } catch (e) {
      console.error("FAIL", name, suffix, e.message);
      report.push({ page: name, kind, suffix, error: e.message });
    }
    await page.close();
  }
}

fs.writeFileSync(path.join(OUT, "meta.json"), JSON.stringify(report, null, 2));
console.log("meta", path.join(OUT, "meta.json"));
await browser.close();
