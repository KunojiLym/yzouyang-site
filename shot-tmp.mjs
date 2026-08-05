import { chromium } from "playwright";
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "dark" });
const page = await ctx.newPage();
await page.goto("http://127.0.0.1:8099/about/", { waitUntil: "networkidle" });
await page.screenshot({ path: "/tmp/about-fresh.png", fullPage: true });
await browser.close();
console.log("done");
