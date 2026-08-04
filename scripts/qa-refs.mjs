import { chromium } from "playwright";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "..", "qa-shots", "refs");
fs.mkdirSync(OUT, { recursive: true });

const sites = [
  ["sourabh", "https://sourabhkothari.vercel.app/"],
  ["rishabh", "https://www.rishabhchaturvedi.dev/"],
  ["mouzan", "https://my-portfolio-jz1h.vercel.app/"],
  ["mihir", "https://chauhan-mihir.vercel.app/"],
  ["hanif", "https://hanifabdlh.vercel.app/"],
  ["dinesh", "https://dineshbarri.dev/"],
  ["anirban", "https://anirban-portfolio-delta.vercel.app/"],
];

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  colorScheme: "dark",
});

const report = [];

for (const [name, url] of sites) {
  const page = await ctx.newPage();
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(1500);
    const file = path.join(OUT, `${name}-desktop.png`);
    await page.screenshot({ path: file, fullPage: false });

    // try scroll mid for long pages
    await page.evaluate(() => window.scrollBy(0, 900));
    await page.waitForTimeout(600);
    const mid = path.join(OUT, `${name}-mid.png`);
    await page.screenshot({ path: mid, fullPage: false });

    const meta = await page.evaluate(() => {
      const bg = getComputedStyle(document.body).backgroundColor;
      const color = getComputedStyle(document.body).color;
      const h1 = document.querySelector("h1")?.textContent?.trim()?.slice(0, 100) || null;
      const nav = [...document.querySelectorAll("nav a, header a")]
        .map((a) => (a.textContent || "").trim())
        .filter(Boolean)
        .slice(0, 12);
      const sections = [...document.querySelectorAll("section, [id]")]
        .map((el) => el.id || el.getAttribute("aria-label") || "")
        .filter(Boolean)
        .slice(0, 15);
      const fonts = [...new Set(
        [...document.querySelectorAll("h1,h2,body")]
          .map((el) => getComputedStyle(el).fontFamily.split(",")[0].replace(/['"]/g, "").trim())
      )].slice(0, 6);
      return {
        title: document.title,
        h1,
        bg,
        color,
        nav: [...new Set(nav)],
        sections,
        fonts,
        scrollH: document.documentElement.scrollHeight,
        darkish: (() => {
          const m = bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
          if (!m) return null;
          return (Number(m[1]) + Number(m[2]) + Number(m[3])) / 3 < 80;
        })(),
      };
    });
    meta.name = name;
    meta.url = url;
    report.push(meta);
    console.log("ok", name, meta.h1, "dark=", meta.darkish, "h=", meta.scrollH);
  } catch (e) {
    console.error("fail", name, e.message);
    report.push({ name, url, error: e.message });
  }
  await page.close();
}

fs.writeFileSync(path.join(OUT, "meta.json"), JSON.stringify(report, null, 2));
await browser.close();
