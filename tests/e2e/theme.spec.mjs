import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const ROUTES = ["/", "/portfolio/", "/credentials/"];
const KNOWN_THIRD_PARTY_EXCLUDES = ["#search"];

async function setTheme(page, theme) {
  await page.addInitScript((value) => {
    localStorage.setItem("yz-theme", value);
  }, theme);
}

test.describe("dual theme", () => {
  for (const theme of ["dark", "light"]) {
    test.describe(theme, () => {
      for (const route of ROUTES) {
        test(`${route} paints ${theme} tokens without FOUC`, async ({ page }) => {
          await setTheme(page, theme);
          await page.goto(route, { waitUntil: "domcontentloaded" });
          const state = await page.evaluate(() => {
            const root = document.documentElement;
            const cs = getComputedStyle(root);
            return {
              dataTheme: root.getAttribute("data-theme"),
              bg: cs.getPropertyValue("--bg-deep").trim().toLowerCase(),
              link: cs.getPropertyValue("--accent-link").trim().toLowerCase(),
              accent: cs.getPropertyValue("--accent").trim().toLowerCase(),
            };
          });
          expect(state.dataTheme).toBe(theme);
          expect(state.accent).toBe("#d4a35c");
          if (theme === "light") {
            expect(state.bg).toBe("#f4f0e8");
            expect(state.link).toBe("#856012");
          } else {
            expect(state.bg).toBe("#0c1412");
          }
        });
      }
    });
  }

  test("boot script precedes stylesheet (no-FOUC smoke)", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    const order = await page.evaluate(() => {
      const html = document.documentElement.outerHTML;
      return {
        boot: html.indexOf('yz-theme'),
        css: html.indexOf('rel="stylesheet"'),
        dataTheme: document.documentElement.getAttribute("data-theme"),
      };
    });
    expect(order.boot).toBeGreaterThan(-1);
    expect(order.css).toBeGreaterThan(order.boot);
    expect(["dark", "light"]).toContain(order.dataTheme);
  });

  test("prefers-color-scheme light applies when store is empty", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.addInitScript(() => localStorage.removeItem("yz-theme"));
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  });

  test("toggle is labeled, pressed, and persists", async ({ page }) => {
    await setTheme(page, "dark");
    await page.goto("/", { waitUntil: "domcontentloaded" });
    const toggle = page.locator("[data-theme-toggle]").first();
    await expect(toggle).toBeVisible();
    await expect(toggle).toHaveAttribute("aria-pressed", "false");
    await expect(toggle).toHaveAccessibleName(/theme: dark/i);
    await toggle.click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await expect(toggle).toHaveAttribute("aria-pressed", "true");
    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  });

  test("prefers-reduced-motion keeps theme change instant", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await setTheme(page, "dark");
    await page.goto("/");
    const toggle = page.locator("[data-theme-toggle]").first();
    await toggle.click();
    const duration = await page.evaluate(() => getComputedStyle(document.documentElement).transitionDuration);
    expect(duration === "0s" || duration === "0s, 0s" || !duration || duration === "initial").toBeTruthy();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  });
});

test.describe("axe contrast both themes", () => {
  for (const theme of ["dark", "light"]) {
    for (const route of ROUTES) {
      test(`${theme} ${route} has no contrast violations`, async ({ page }, testInfo) => {
        await setTheme(page, theme);
        await page.goto(route, { waitUntil: "networkidle" });
        const results = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa"])
          .disableRules(["color-contrast-enhanced"])
          .exclude(KNOWN_THIRD_PARTY_EXCLUDES)
          .options({ iframes: false })
          .analyze();
        const contrast = results.violations
          .map((v) => ({
            ...v,
            nodes: v.nodes.filter((node) => node.target[0] !== "iframe"),
          }))
          .filter((v) => v.nodes.length && (v.id === "color-contrast" || v.id.includes("contrast")));
        if (contrast.length) {
          await testInfo.attach(`axe-contrast-${theme}${route.replaceAll("/", "-")}.json`, {
            body: JSON.stringify(contrast, null, 2),
            contentType: "application/json",
          });
        }
        expect(contrast, `${theme} ${route} contrast`).toEqual([]);
      });
    }
  }
});
