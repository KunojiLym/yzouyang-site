import { test, expect } from "@playwright/test";

const ROUTES = ["/", "/about/", "/portfolio/", "/credentials/", "/career-journey/"];

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
    await expect(page.locator("main#main.page")).toHaveCount(1);
    const skip = page.locator("a.skip-link");
    await expect(skip).toHaveCount(1);
    await expect(skip).toHaveAttribute("href", "#main");
    await skip.focus();
    await expect(skip).toBeFocused();
    await expect(skip).toBeVisible();
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

  test("prefers-reduced-motion uses auto scroll-behavior", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    const behavior = await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior);
    expect(behavior).toBe("auto");
  });
});

test.describe("home", () => {
  test("hero h1 uses Fraunces display token", async ({ page }) => {
    await page.goto("/");
    const heroTitle = page.locator(".hero h1");
    await expect(heroTitle).toBeVisible();
    const type = await heroTitle.evaluate((el) => {
      const cs = getComputedStyle(el);
      const probe = document.createElement("span");
      probe.style.fontFamily = "var(--font-display)";
      probe.style.fontSize = "var(--text-display-hero)";
      el.appendChild(probe);
      const expected = getComputedStyle(probe);
      const out = {
        fontFamily: cs.fontFamily,
        fontSize: cs.fontSize,
        fontWeight: cs.fontWeight,
        expectedFamily: expected.fontFamily,
        expectedSize: expected.fontSize,
        fontDisplay: cs.getPropertyValue("--font-display").trim(),
        displayHero: cs.getPropertyValue("--text-display-hero").trim(),
      };
      probe.remove();
      return out;
    });
    expect(type.fontFamily.toLowerCase()).toContain("fraunces");
    expect(type.fontFamily.toLowerCase()).not.toContain("sora");
    expect(type.expectedFamily.toLowerCase()).toContain("fraunces");
    expect(type.fontFamily).toBe(type.expectedFamily);
    expect(type.fontSize).toBe(type.expectedSize);
    expect(type.fontDisplay.toLowerCase()).toContain("fraunces");
    expect(type.displayHero).toMatch(/clamp\(/);
    expect(Number.parseInt(type.fontWeight, 10)).toBeGreaterThanOrEqual(600);
  });

  test("outcome strip is three columns at desktop, proof pills match", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/");
    const items = page.locator(".outcome-strip li");
    await expect(items).toHaveCount(3);
    const boxes = await items.evaluateAll((els) =>
      els.map((el) => {
        const r = el.getBoundingClientRect();
        return { y: r.y, x: r.x };
      })
    );
    expect(Math.abs(boxes[0].y - boxes[2].y)).toBeLessThan(2);
    expect(boxes[2].x).toBeGreaterThan(boxes[1].x);
    const pillPaint = await page.locator(".proof-strip li").evaluateAll((els) =>
      els.map((el) => {
        const cs = getComputedStyle(el);
        return { bg: cs.backgroundColor, border: cs.borderTopColor };
      })
    );
    expect(pillPaint.length).toBeGreaterThan(1);
    for (const pill of pillPaint) {
      expect(pill.bg).toBe(pillPaint[0].bg);
      expect(pill.border).toBe(pillPaint[0].border);
    }
  });

  test("proof strip, CTAs, portrait chip, contact section", async ({ page }, testInfo) => {
    await page.goto("/");
    await expect(page.locator(".outcome-strip")).toBeVisible();
    await expect(page.locator(".outcome-strip .metric").first()).toBeVisible();
    await expect(page.locator(".proof-strip")).toBeVisible();
    await expect(page.locator("body")).not.toContainText("professional credentials");
    await expect(page.locator(".header-actions > .header-contact")).toBeVisible();
    await expect(page.locator(".nav-menu .header-contact")).toHaveCount(0);
    if (testInfo.project.name === "mobile") {
      await expect(page.locator("details.nav-menu")).toBeVisible();
    }
    await expect(page.getByRole("link", { name: "Digital card" })).toBeVisible();
    const ctaRow = page.locator(".cta-row");
    await expect(ctaRow.locator(".btn-primary")).toHaveCount(1);
    await expect(ctaRow.locator(".btn-primary")).toHaveText("Contact");
    await expect(ctaRow.locator("a.btn")).toHaveCount(2);
    await expect(page.locator(".hero .btn-primary")).toHaveCount(1);
    await expect(page.locator(".header-actions > .header-contact.btn-primary")).toHaveCount(0);
    await expect(page.locator(".portrait-chip")).toBeVisible();
    await expect(page.locator("#contact")).toBeVisible();
    await expect(page.locator("body")).not.toContainText("Static migration");

    if (testInfo.project.name === "mobile") {
      const h1Box = await page.locator("h1").first().boundingBox();
      const photoBox = await page.locator(".hero-photo").boundingBox();
      expect(h1Box && photoBox).toBeTruthy();
      expect(h1Box.y).toBeLessThan(photoBox.y);
    }
  });

  test("header contact jumps to #contact", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/about/");
    await page.locator(".header-actions > .header-contact").click();
    await expect(page).toHaveURL(/#contact$/);
    await expect(page.locator("#contact")).toBeInViewport();
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
      await expect(menu.locator('a[href$="/contact/"]')).toHaveCount(0);
      await expect(menu.getByRole("link", { name: /Blog/ })).toBeVisible();
      await expect(menu.getByRole("link", { name: /Medium/ })).toBeVisible();
      await expect(menu.getByRole("link", { name: /LinkedIn/ })).toBeVisible();
    } else {
      const nav = page.locator("nav.site-nav-desktop");
      await expect(nav.getByRole("link", { name: "About" })).toHaveAttribute(
        "aria-current",
        "page"
      );
      await expect(nav.getByRole("link", { name: "Contact" })).toHaveCount(0);
      await expect(nav.getByRole("link", { name: /Blog/ })).toBeVisible();
    }
  });
});

test.describe("footer", () => {
  test("public footer", async ({ page }) => {
    await page.goto("/");
    const footer = page.locator("footer.site-footer");
    await expect(footer).toContainText(/©|©|&copy;|2026|202\d/);
    await expect(footer.locator('a[href^="mailto:"]')).toBeVisible();
    await expect(footer).not.toContainText("Phase 1");
    await expect(footer).not.toContainText("Static migration");
  });
});

test.describe("contact redirect", () => {
  test("/contact/ targets home #contact", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/contact/");
    await page.waitForURL(/#contact/, { timeout: 10_000 });
    await expect(page.locator("#contact")).toBeVisible();
  });
});

test.describe("search", () => {
  test("pagefind on portfolio", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop search coverage enough");
    await page.goto("/portfolio/");
    const input = page.locator(".pagefind-ui__search-input");
    await expect(input).toBeVisible({ timeout: 20_000 });
    const searchLabel = page.locator("label.page-search-label");
    await expect(searchLabel).toBeVisible();
    await expect(searchLabel).toHaveText("Search this page");
    await expect(input).toHaveAttribute("id", "pagefind-search-input");
    await expect(input).toHaveAttribute("name", "q");
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
    await expect(page.locator("h3.issuer-group + ul h4").first()).toBeVisible();
    await expect(page.locator("h3.issuer-group + ul h3")).toHaveCount(0);
    const rawUrlLinks = page.locator(".item-list a").filter({ hasText: /https?:\/\// });
    await expect(rawUrlLinks).toHaveCount(0);
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

  test("portfolio sidebar TOC stays sticky while scrolling", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop sidebar coverage enough");
    await page.goto("/portfolio/");
    const toc = page.locator(".page-toc-sidebar");
    await expect(toc).toBeVisible();
    const position = await toc.evaluate((el) => getComputedStyle(el).position);
    expect(position).toBe("sticky");
    await page.evaluate(() => window.scrollTo(0, 1400));
    await expect(toc).toBeInViewport();
  });

  test("portfolio Figma surface is dark preview not iframe", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/portfolio/");
    await expect(page.locator("iframe")).toHaveCount(0);
    const preview = page.locator(".embed-frame-static").first();
    await expect(preview).toBeVisible();
    const bg = await preview.evaluate((el) => getComputedStyle(el).backgroundColor);
    expect(bg).not.toMatch(/^rgb\(\s*255,\s*255,\s*255/);
    await expect(page.locator(".embed-fallback").first()).toBeVisible();
  });
});

test.describe("about writing + figma", () => {
  test("selected writing and open deck", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/about/");
    await expect(page.locator("#selected-writing")).toBeVisible();
    await expect(page.locator(".writing-list a.external").first()).toBeVisible();
    await expect(page.locator(".cj-link-card")).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Read my career journey" })).toBeVisible();
    const open = page.locator("a.figma-open, a.embed-fallback").first();
    await expect(open).toBeVisible();
    await expect(open).toHaveAttribute("target", "_blank");
  });

  test("about has sidebar TOC like other long pages", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/about/");
    await expect(page.locator(".page-with-toc")).toBeVisible();
    await expect(page.locator(".page-toc-sidebar")).toBeVisible();
    await expect(page.locator(".page-toc-sidebar a").first()).toBeVisible();
    await expect(page.locator("details.section-fold").first()).toBeVisible();
    await expect(page.locator("details.section-fold").first()).toHaveAttribute("open", "");
    await expect(
      page.locator("details.section-fold > summary :is(h1, h2, h3, h4, h5, h6)")
    ).toHaveCount(0);
    const firstSummary = page.locator("details.section-fold > summary").first();
    await expect(firstSummary).toHaveAttribute("id", /.+/);
    await expect(firstSummary).not.toHaveText("");
  });
});

test.describe("sticky header", () => {
  test("header wrap stays sticky while scrolling", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/credentials/");
    const wrap = page.locator(".site-header-wrap");
    await expect(wrap).toBeVisible();
    const position = await wrap.evaluate((el) => getComputedStyle(el).position);
    expect(position).toBe("sticky");
    await page.evaluate(() => window.scrollTo(0, 1200));
    await expect(wrap).toBeInViewport();
  });
});
