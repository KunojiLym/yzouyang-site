import { test, expect } from "@playwright/test";

const ROUTES = ["/", "/about/", "/portfolio/", "/credentials/", "/contact/"];

async function noHorizontalOverflow(page) {
  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth > window.innerWidth + 2;
  });
  expect(overflow).toBe(false);
}

test.describe("smoke", () => {
  for (const route of ROUTES) {
    test(`${route} loads with h1`, async ({ page }) => {
      const res = await page.goto(route, { waitUntil: "domcontentloaded" });
      expect(res?.ok()).toBeTruthy();
      await expect(page.locator("h1").first()).toBeVisible();
      await noHorizontalOverflow(page);
    });
  }
});

test.describe("a11y light + contrast", () => {
  test("landmarks and non-transparent body bg", async ({ page }, testInfo) => {
    await page.goto("/");
    await expect(page.locator("html[lang]")).toHaveCount(1);
    await expect(page.locator("main.page")).toHaveCount(1);
    if (testInfo.project.name === "mobile") {
      await expect(page.locator("details.nav-menu")).toBeVisible();
      await expect(page.locator("details.nav-menu nav[aria-label='Primary']")).toHaveCount(1);
    } else {
      await expect(page.locator("nav.site-nav-desktop")).toBeVisible();
    }
    const paint = await page.evaluate(async () => {
      const link = [...document.querySelectorAll('link[rel="stylesheet"]')].find((el) =>
        (el.getAttribute("href") || "").includes("styles")
      );
      let cssOk = false;
      if (link) {
        try {
          cssOk = (await fetch(link.href)).ok;
        } catch {
          cssOk = false;
        }
      }
      return {
        cssOk,
        bodyBg: getComputedStyle(document.body).backgroundColor,
        htmlBg: getComputedStyle(document.documentElement).backgroundColor,
      };
    });
    expect(paint.cssOk).toBe(true);
    const solid = (c) => c && c !== "transparent" && !/^rgba\(\s*0,\s*0,\s*0,\s*0\s*\)$/.test(c);
    expect(solid(paint.htmlBg) || solid(paint.bodyBg)).toBe(true);
  });
});

test.describe("home", () => {
  test("proof strip, CTAs, portrait chip", async ({ page }, testInfo) => {
    await page.goto("/");
    await expect(page.locator(".proof-strip")).toBeVisible();
    await expect(page.getByRole("link", { name: "Contact" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Digital card" })).toBeVisible();
    await expect(page.locator(".portrait-chip")).toBeVisible();
    await expect(page.locator("body")).not.toContainText("Static migration");

    if (testInfo.project.name === "mobile") {
      const h1Box = await page.locator("h1").first().boundingBox();
      const photoBox = await page.locator(".hero-photo").boundingBox();
      expect(h1Box && photoBox).toBeTruthy();
      expect(h1Box.y).toBeLessThan(photoBox.y);
    }
  });
});

test.describe("nav", () => {
  test("primary navigation", async ({ page }, testInfo) => {
    await page.goto("/about/");
    if (testInfo.project.name === "mobile") {
      const menu = page.locator("details.nav-menu");
      await expect(menu).toBeVisible();
      await menu.locator("summary").click();
      await expect(menu.locator('a[href$="/portfolio/"]')).toBeVisible();
      await expect(menu.locator('a[href$="/credentials/"]')).toBeVisible();
      await expect(menu.locator('a[href$="/about/"][aria-current="page"]')).toBeVisible();
      await expect(menu.getByRole("link", { name: /Blog/ })).toBeVisible();
      await expect(menu.getByRole("link", { name: /Medium/ })).toBeVisible();
      await expect(menu.getByRole("link", { name: /LinkedIn/ })).toBeVisible();
    } else {
      const nav = page.locator("nav.site-nav-desktop");
      await expect(nav.getByRole("link", { name: "About" })).toHaveAttribute(
        "aria-current",
        "page"
      );
      await expect(nav.getByRole("link", { name: /Blog/ })).toBeVisible();
    }
  });
});

test.describe("footer", () => {
  test("public footer", async ({ page }) => {
    await page.goto("/contact/");
    const footer = page.locator("footer.site-footer");
    await expect(footer).toContainText(/©|©|&copy;|2026|202\d/);
    await expect(footer.locator('a[href^="mailto:"]')).toBeVisible();
    await expect(footer).not.toContainText("Phase 1");
    await expect(footer).not.toContainText("Static migration");
  });
});

test.describe("search", () => {
  test("pagefind on portfolio", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop search coverage enough");
    await page.goto("/portfolio/");
    const input = page.locator(".pagefind-ui__search-input");
    await expect(input).toBeVisible({ timeout: 20_000 });
    await input.fill("databricks");
    await expect(page.locator(".pagefind-ui__result").first()).toBeVisible({
      timeout: 15_000,
    });
    const clear = page.locator(".pagefind-ui__search-clear");
    if (await clear.count()) {
      await clear.first().click();
    }
  });
});

test.describe("toc + credentials", () => {
  test("toc jump and issuer groups", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop toc coverage enough");
    await page.goto("/credentials/");
    await expect(page.locator("h3.issuer-group").first()).toBeVisible();
    const tocLink = page.locator(".page-toc a").first();
    await expect(tocLink).toBeVisible();
    const href = await tocLink.getAttribute("href");
    expect(href?.startsWith("#")).toBeTruthy();
    const id = href.slice(1);
    await tocLink.click();
    await expect(page).toHaveURL(new RegExp(`#${id}$`));
    const target = page.locator(`[id="${id}"]`);
    await expect(target).toBeVisible();
    await expect(target).toBeInViewport();
  });
});

test.describe("figma fallback", () => {
  test("open deck link present on about", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/about/");
    const open = page.locator("a.figma-open, a.embed-fallback").first();
    await expect(open).toBeVisible();
    await expect(open).toHaveAttribute("target", "_blank");
  });
});
