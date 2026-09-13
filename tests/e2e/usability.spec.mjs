import { test, expect } from "@playwright/test";

const LIVE_ROUTES = ["/", "/systems/", "/notes/", "/credentials/"];
const REDIRECTS = [
  ["/about/", /\/$/],
  ["/contact/", /\/$/],
  ["/career-journey/", /\/$/],
  ["/portfolio/", /\/systems\/(?:$|#)/],
  ["/perspectives/", /\/notes\/(?:$|#)/],
  ["/blog/", /\/notes\/(?:$|#)/],
];

function libraryIndexPanel(page, panelId) {
  return page.locator(`.library-index-list [data-panel-id="${panelId}"]`).first();
}

async function noHorizontalOverflow(page) {
  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth > window.innerWidth + 2;
  });
  expect(overflow).toBe(false);
}

async function assertSkipLink(page) {
  const skip = page.locator("a.skip-link");
  await expect(skip).toHaveCount(1);
  await expect(skip).toHaveAttribute("href", "#main");
  await skip.focus();
  await expect(skip).toBeFocused();
  await expect(skip).toBeVisible();
}

async function assertHomeEntryGrid(page) {
  await expect(page.locator(".home-entry-grid")).toBeVisible();
  await expect(page.locator(".home-entry-grid").getByRole("link", { name: "Systems" })).toBeVisible();
  await expect(page.locator(".home-entry-grid").getByRole("link", { name: "Notes" })).toBeVisible();
  await expect(page.locator(".home-entry-grid").getByRole("link", { name: "Credentials" })).toBeVisible();
}

async function assertFooterLinks(page) {
  const footer = page.locator("footer.site-footer, footer.library-page-footer").first();
  await expect(footer).toHaveClass(/library-card/);
  await expect(footer.locator('a[href^="mailto:"]')).toBeVisible();
  await expect(footer.getByRole("link", { name: /Blog/ })).toBeVisible();
  await expect(footer.getByRole("link", { name: /Medium/ })).toHaveClass(/external/);
  await expect(footer.getByRole("link", { name: /LinkedIn/ })).toBeVisible();
  await expect(footer.getByRole("link", { name: /GitHub/ })).toHaveClass(/external/);
}

test.describe("smoke", () => {
  for (const route of LIVE_ROUTES) {
    test(`${route} loads with h1`, async ({ page }) => {
      const res = await page.goto(route, { waitUntil: "domcontentloaded" });
      expect(res?.ok()).toBeTruthy();
      await expect(page.locator("h1").first()).toBeVisible();
      await noHorizontalOverflow(page);
    });
  }
});

test.describe("legacy redirects", () => {
  for (const [route, dest] of REDIRECTS) {
    test(`${route} redirects`, async ({ page }) => {
      await page.goto(route);
      await expect(page).toHaveURL(dest);
      await expect(page.locator("h1").first()).toBeVisible();
    });
  }
});

test.describe("chrome", () => {
  test("landmarks, skip-link, and primary nav", async ({ page }, testInfo) => {
    await page.goto("/");
    await expect(page.locator("html[lang]")).toHaveCount(1);
    await expect(page.locator("main#main.page")).toHaveCount(1);
    await assertSkipLink(page);
    if (testInfo.project.name === "mobile") {
      const menu = page.locator("details.nav-menu");
      await expect(menu).toBeVisible();
      await menu.locator("summary").click();
      const nav = menu.locator("nav[aria-label='Primary']");
      await expect(nav.getByRole("link", { name: "Systems" })).toHaveAttribute("href", /\/systems\/$/);
      await expect(nav.getByRole("link", { name: "Notes" })).toHaveAttribute("href", /\/notes\/$/);
      await expect(nav.getByRole("link", { name: "Credentials" })).toHaveAttribute(
        "href",
        /\/credentials\/$/
      );
      await expect(nav.getByRole("link", { name: "Profile" })).toHaveCount(0);
      await expect(nav.getByRole("link", { name: "Connect" })).toHaveCount(0);
      await expect(nav.getByRole("link", { name: /Blog/ })).toHaveCount(0);
    } else {
      const nav = page.locator("nav.site-nav-desktop");
      await expect(nav).toBeVisible();
      await expect(nav.getByRole("link", { name: "Systems" })).toHaveAttribute("href", /\/systems\/$/);
      await expect(nav.getByRole("link", { name: "Notes" })).toHaveAttribute("href", /\/notes\/$/);
      await expect(nav.getByRole("link", { name: "Credentials" })).toHaveAttribute(
        "href",
        /\/credentials\/$/
      );
      await expect(nav.getByRole("link", { name: "Profile" })).toHaveCount(0);
      await expect(nav.getByRole("link", { name: "Connect" })).toHaveCount(0);
      await expect(nav.getByRole("link", { name: "Portfolio" })).toHaveCount(0);
    }
  });

  test("library-card footer", async ({ page }) => {
    await page.goto("/");
    await assertFooterLinks(page);
    const footer = page.locator("footer.site-footer, footer.library-page-footer").first();
    await expect(footer).toContainText(/©|&copy;|202\d/);
    await expect(page.locator(".nav-elsewhere")).toHaveCount(0);
  });

  test("sticky header wrap", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/credentials/");
    const wrap = page.locator(".site-header-wrap");
    await expect(wrap).toBeVisible();
    expect(await wrap.evaluate((el) => getComputedStyle(el).position)).toBe("sticky");
    await page.evaluate(() => window.scrollTo(0, 1200));
    await expect(wrap).toBeInViewport();
  });

  test("prefers-reduced-motion uses auto scroll-behavior", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    const behavior = await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior);
    expect(behavior).toBe("auto");
  });
});

test.describe("home", () => {
  test("entrance uses Crimson Pro and token atmosphere", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/");
    const heroTitle = page.locator(".entrance h1");
    await expect(heroTitle).toBeVisible();
    await expect(page.locator(".entrance-atmosphere--tokens")).toBeVisible();
    const type = await heroTitle.evaluate((el) => {
      const cs = getComputedStyle(el);
      return {
        fontFamily: cs.fontFamily,
        fontWeight: cs.fontWeight,
        displayHero: cs.getPropertyValue("--text-display-hero").trim(),
      };
    });
    expect(type.fontFamily.toLowerCase()).toContain("crimson pro");
    expect(type.fontFamily.toLowerCase()).not.toContain("source sans");
    expect(type.displayHero).toMatch(/clamp\(/);
    expect(Number.parseInt(type.fontWeight, 10)).toBeGreaterThanOrEqual(600);
  });

  test("current index, proof strip, entry grid, competencies", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".current-index li")).toHaveCount(2);
    await expect(page.locator(".proof-strip")).toBeVisible();
    await expect(page.locator(".proof-strip li").first()).toContainText("Singapore");
    await assertHomeEntryGrid(page);
    await expect(page.locator(".home-competency-list .home-competency").first()).toBeVisible();
    await expect(page.getByText("Data Engineering Leadership")).toBeVisible();
    await expect(page.locator("main.home-route")).toBeVisible();
    await expect(page.locator("[data-theme-toggle]").first()).toBeVisible();
  });

  test("home omits the retired scroll-home chrome", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/");
    await expect(page.locator(".cta-row")).toHaveCount(0);
    await expect(page.locator(".header-actions > .header-contact")).toHaveCount(0);
    await expect(page.locator(".portrait-chip")).toHaveCount(0);
    await expect(page.locator(".home-featured-systems")).toHaveCount(0);
    await expect(page.locator(".home-contact-plate")).toHaveCount(0);
    await expect(page.locator("#contact")).toHaveCount(0);
    await expect(page.locator("[data-library-deck]")).toHaveCount(0);
    await expect(page.locator("#workshop")).toHaveCount(0);
    await expect(page.locator(".outcome-strip")).toHaveCount(0);
    await expect(page.locator("#catalogue-search")).toHaveCount(0);
    await expect(page.locator("body")).not.toContainText("professional credentials");
    await expect(page.locator("body")).not.toContainText("Static migration");
  });
});

test.describe("library shell", () => {
  test("systems index opens a panel and honors hash records", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop sidebar coverage");
    await page.goto("/systems/");
    await expect(page.locator(".library-shell")).toBeVisible();
    await expect(page.locator(".library-index-list")).toBeVisible();
    await libraryIndexPanel(
      page,
      "prudential-singapore-senior-data-engineer-solutioning-architecture"
    ).click();
    await expect(
      page.locator(
        '.library-panel[data-panel-id="prudential-singapore-senior-data-engineer-solutioning-architecture"].is-active'
      )
    ).toBeVisible();
    await page.goto("/systems/#SYS-01", { waitUntil: "load" });
    await expect(page.locator('.library-panel[data-record="SYS-01"].is-active')).toBeVisible();
    await expect(page.locator(".library-panel.is-active .record-impact")).toBeVisible();
    await page.goto("/systems/#NOTE-2026-005", { waitUntil: "load" });
    await expect(page.locator('.library-panel[data-record="NOTE-2026-005"].is-active')).toBeVisible();
    await expect(page.locator(".library-panel.is-active .map-record-read")).toContainText("Read note");
  });

  test("notes library opens a writing panel", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop sidebar coverage");
    await page.goto("/notes/");
    await expect(page.locator(".library-shell")).toBeVisible();
    await libraryIndexPanel(page, "NOTE-2026-005").click();
    await expect(page.locator('.library-panel[data-panel-id="NOTE-2026-005"].is-active')).toBeVisible();
  });

  test("credentials issuer panel uses credential cards", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop sidebar coverage");
    await page.goto("/credentials/");
    await expect(page.locator(".library-shell")).toBeVisible();
    await libraryIndexPanel(page, "google-cloud").click();
    await expect(page.locator('.library-panel[data-panel-id="google-cloud"].is-active')).toBeVisible();
    await expect(page.locator(".library-panel.is-active .credential-card").first()).toBeVisible();
    await expect(page.locator(".library-panel.is-active .item-list")).toHaveCount(0);
    const rawUrlLinks = page.locator(".credential-card a").filter({ hasText: /https?:\/\// });
    await expect(rawUrlLinks).toHaveCount(0);
  });

  test("systems Figma stays a compact link", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/systems/");
    await libraryIndexPanel(page, "featured-product-ux-projects").click();
    await expect(
      page.locator('.library-panel[data-panel-id="featured-product-ux-projects"].is-active')
    ).toBeVisible();
    await expect(page.locator("iframe")).toHaveCount(0);
    await expect(page.locator(".embed-frame-static")).toHaveCount(0);
    await expect(
      page.locator(".library-panel.is-active").getByRole("link", { name: "Figma deck" })
    ).toBeVisible();
  });

  test("mobile systems shows index then back from a panel", async ({ page }) => {
    test.skip(test.info().project.name === "desktop", "mobile master-detail");
    await page.goto("/systems/");
    await expect(page.locator(".library-shell")).toBeVisible();
    await expect(page.locator(".library-index-list")).toBeVisible();
    await libraryIndexPanel(
      page,
      "prudential-singapore-senior-data-engineer-solutioning-architecture"
    ).click();
    await expect(
      page.locator(
        '.library-panel[data-panel-id="prudential-singapore-senior-data-engineer-solutioning-architecture"].is-active'
      )
    ).toBeVisible();
    await expect(page.locator(".library-index-list")).toBeHidden();
    await page.locator(".library-back").click();
    await expect(page.locator(".library-index-list")).toBeVisible();
  });
});

test.describe("search", () => {
  test("header Pagefind on systems returns catalogue hits", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop search coverage enough");
    await page.goto("/systems/");
    await expect(page.locator(".header-search #search")).toBeVisible();
    const searchLabel = page.locator("label.page-search-label");
    await expect(searchLabel).toHaveText("Search catalogue");
    const input = page.locator(".pagefind-ui__search-input");
    await expect(input).toBeVisible({ timeout: 20_000 });
    await expect(input).toHaveAttribute("id", "pagefind-search-input");
    await input.fill("databricks");
    await expect(page.locator(".pagefind-ui__result").first()).toBeVisible({ timeout: 15_000 });
  });
});

test.describe("layout", () => {
  test("desktop library shell keeps search and index without overflow", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop 1280");
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto("/systems/", { waitUntil: "networkidle" });
    await expect(page.locator(".pagefind-ui__search-input")).toBeVisible({ timeout: 20_000 });
    await expect(page.locator(".library-index")).toBeVisible();
    await noHorizontalOverflow(page);
  });

  test("narrow desktop keeps a single-column library split", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "explicit 800");
    await page.setViewportSize({ width: 800, height: 900 });
    await page.goto("/");
    await expect(page.locator(".entrance h1")).toBeVisible();
    await assertHomeEntryGrid(page);
    await page.goto("/systems/#SYS-01", { waitUntil: "load" });
    await expect(page.locator('.library-panel[data-record="SYS-01"].is-active')).toBeVisible();
    const columns = await page
      .locator(".library-split")
      .evaluate((el) => getComputedStyle(el).gridTemplateColumns);
    expect(columns.split(" ").length).toBe(1);
    await noHorizontalOverflow(page);
  });

  test("900px theme toggle sits beside Menu", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "explicit 900");
    await page.setViewportSize({ width: 900, height: 800 });
    await page.goto("/");
    await expect(page.locator("nav.site-nav-desktop")).toBeHidden();
    const menu = page.locator("details.nav-menu");
    const toggle = page.locator(".header-actions > [data-theme-toggle]");
    await expect(menu).toBeVisible();
    await expect(toggle).toBeVisible();
    const toggleBox = await toggle.boundingBox();
    const menuBox = await menu.locator("summary").boundingBox();
    expect(toggleBox && menuBox).toBeTruthy();
    expect(Math.abs(toggleBox.y - menuBox.y)).toBeLessThan(24);
    expect(toggleBox.x).toBeLessThan(menuBox.x);
    await noHorizontalOverflow(page);
  });
});
