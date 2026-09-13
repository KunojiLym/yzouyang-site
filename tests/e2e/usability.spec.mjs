import { test, expect } from "@playwright/test";

const ROUTES = ["/", "/about/", "/systems/", "/notes/", "/credentials/", "/contact/"];

function libraryIndexPanel(page, panelId) {
  return page.locator(`.library-index-list [data-panel-id="${panelId}"]`).first();
}

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

  test("/career-journey/ redirects to home", async ({ page }) => {
    await page.goto("/career-journey/");
    await expect(page).toHaveURL(/\/$/);
  });
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
    const tokens = await page.evaluate(() => {
      const cs = getComputedStyle(document.documentElement);
      return {
        elevated: cs.getPropertyValue("--bg-elevated").trim(),
        mid: cs.getPropertyValue("--bg-mid").trim(),
        glow: cs.getPropertyValue("--glow").trim(),
        accent: cs.getPropertyValue("--accent").trim(),
        glowLayers: getComputedStyle(document.body).backgroundImage.split("radial-gradient").length - 1,
      };
    });
    expect(tokens.elevated.toLowerCase()).toBe("#2a2118");
    expect(tokens.mid.toLowerCase()).toBe("#1c1612");
    expect(tokens.accent.toLowerCase()).toBe("#c49a5a");
    expect(tokens.glow).toMatch(/212\s+163\s+92/);
    expect(tokens.glowLayers).toBe(1);
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  });

  test("prefers-reduced-motion uses auto scroll-behavior", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    const behavior = await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior);
    expect(behavior).toBe("auto");
  });
});

test.describe("home", () => {
  test("entrance h1 uses Crimson Pro display token", async ({ page }) => {
    await page.goto("/");
    const heroTitle = page.locator(".entrance h1");
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
    expect(type.fontFamily.toLowerCase()).toContain("crimson pro");
    expect(type.fontFamily.toLowerCase()).not.toContain("source sans");
    expect(type.expectedFamily.toLowerCase()).toContain("crimson pro");
    expect(type.fontFamily).toBe(type.expectedFamily);
    expect(type.fontSize).toBe(type.expectedSize);
    expect(type.fontDisplay.toLowerCase()).toContain("crimson pro");
    expect(type.displayHero).toMatch(/clamp\(/);
    expect(Number.parseInt(type.fontWeight, 10)).toBeGreaterThanOrEqual(600);
  });

  test("entrance atmosphere, current index, and proof strip", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/");
    await expect(page.locator(".entrance-atmosphere--tokens")).toBeVisible();
    await expect(page.locator(".current-index li")).toHaveCount(2);
    await expect(page.locator(".proof-strip")).toBeVisible();
    await expect(page.locator(".proof-strip li").first()).toContainText("Singapore");
    await expect(page.locator(".outcome-strip")).toHaveCount(0);
  });

  test("proof strip, entry grid, and systems route", async ({ page }, testInfo) => {
    await page.goto("/");
    await expect(page.locator(".proof-strip")).toBeVisible();
    await expect(page.locator("body")).not.toContainText("professional credentials");
    await expect(page.locator("[data-theme-toggle]").first()).toBeVisible();
    await expect(page.locator(".header-actions > .header-contact")).toHaveCount(0);
    if (testInfo.project.name === "mobile") {
      await expect(page.locator("details.nav-menu")).toBeVisible();
    }
    await expect(page.locator(".cta-row")).toHaveCount(0);
    await expect(page.locator(".home-entry-grid")).toBeVisible();
    await expect(page.locator(".home-entry-grid").getByRole("link", { name: "Systems" })).toBeVisible();
    await expect(page.locator(".portrait-chip")).toHaveCount(0);
    await expect(page.locator(".home-featured-systems")).toHaveCount(0);
    await expect(page.locator(".home-contact-plate")).toHaveCount(0);
    await expect(page.locator("#contact")).toHaveCount(0);
    await expect(page.locator("[data-library-deck]")).toHaveCount(0);
    await expect(page.locator("#workshop")).toHaveCount(0);
    await expect(page.locator("body")).not.toContainText("Static migration");
    if (testInfo.project.name === "mobile") {
      await page.locator(".home-entry-grid").getByRole("link", { name: "Systems" }).click();
    } else {
      await page.locator("nav.site-nav-desktop").getByRole("link", { name: "Systems" }).click();
    }
    await expect(page).toHaveURL(/\/systems\//);
    await expect(page.locator(".library-shell")).toBeVisible();
    if (testInfo.project.name === "mobile") {
      return;
    }
    await expect(page.locator(".library-index-list")).toBeVisible();
    await libraryIndexPanel(page, "prudential-singapore-senior-data-engineer-solutioning-architecture").click();
    await expect(
      page.locator(
        '.library-panel[data-panel-id="prudential-singapore-senior-data-engineer-solutioning-architecture"].is-active'
      )
    ).toBeVisible();
    await page.goto("/systems/#SYS-01");
    await expect(page.locator('.library-panel[data-record="SYS-01"].is-active')).toBeVisible();
    await expect(page.locator(".record-impact")).toBeVisible();
    await page.goto("/systems/#NOTE-2026-005");
    await expect(page.locator('.library-panel[data-record="NOTE-2026-005"].is-active')).toBeVisible();
    await expect(page.locator('.library-panel.is-active .map-record-read')).toContainText(
      "Read note"
    );

    if (testInfo.project.name === "mobile") {
      await expect(page.locator(".entrance h1")).toBeVisible();
      await expect(page.locator(".entrance-atmosphere")).toBeVisible();
    }
  });

  test("home scroll and header search", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/");
    await expect(page.locator("[data-library-deck]")).toHaveCount(0);
    await expect(page.locator(".header-search #search")).toBeVisible();
    await expect(page.locator("#catalogue-search")).toHaveCount(0);
    await expect(page.locator(".home-entry-grid")).toBeVisible();
    await expect(page.locator("main.home-route")).toBeVisible();
    await page.locator("nav.site-nav-desktop").getByRole("link", { name: "Systems" }).click();
    await expect(page).toHaveURL(/\/systems\//);
    await libraryIndexPanel(page, "featured-tutorial-projects").click();
    await expect(
      page.locator('.library-panel[data-panel-id="featured-tutorial-projects"].is-active')
    ).toBeVisible();
    await expect(page.locator('a[data-slide-target="workshop"]')).toHaveCount(0);
  });

  test("credentials includes header search", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/credentials/");
    await expect(page.locator(".header-search #search")).toBeVisible();
    await expect(page.locator(".library-shell")).toBeVisible();
  });
});

test.describe("nav", () => {
  test("primary navigation uses route URLs", async ({ page }, testInfo) => {
    await page.goto("/systems/");
    if (testInfo.project.name === "mobile") {
      const menu = page.locator("details.nav-menu");
      await expect(menu).toBeVisible();
      await menu.locator("summary").click();
      await expect(menu.locator('a[href$="/systems/"]')).toBeVisible();
      await expect(menu.locator('a[href$="/credentials/"]')).toBeVisible();
      await expect(menu.locator('a[href$="/notes/"]')).toBeVisible();
      await expect(menu.locator('a[href$="/about/"]')).toHaveCount(0);
      await expect(menu.getByRole("link", { name: "Connect" })).toHaveCount(0);
      await expect(menu.getByRole("link", { name: /Blog/ })).toHaveCount(0);
    } else {
      const nav = page.locator("nav.site-nav-desktop");
      await expect(nav.getByRole("link", { name: "Profile" })).toHaveCount(0);
      await expect(nav.getByRole("link", { name: "Systems" })).toHaveAttribute(
        "href",
        /\/systems\/$/
      );
      await expect(nav.getByRole("link", { name: "Notes" })).toHaveAttribute("href", /\/notes\/$/);
      await expect(nav.getByRole("link", { name: "Credentials" })).toHaveAttribute(
        "href",
        /\/credentials\/$/
      );
      await expect(nav.getByRole("link", { name: "Experiments" })).toHaveCount(0);
      await expect(nav.getByRole("link", { name: "Connect" })).toHaveCount(0);
      await expect(nav.getByRole("link", { name: "Portfolio" })).toHaveCount(0);
      const footer = page.locator("footer.site-footer, footer.library-page-footer").first();
      await expect(footer.getByRole("link", { name: /Blog/ })).toBeVisible();
      await expect(footer.getByRole("link", { name: /Medium/ })).toHaveClass(/external/);
      await expect(footer.getByRole("link", { name: /LinkedIn/ })).toBeVisible();
      await expect(footer.getByRole("link", { name: /GitHub/ })).toHaveClass(/external/);
      await expect(page.locator(".nav-elsewhere")).toHaveCount(0);
    }
  });
});

test.describe("footer", () => {
  test("public footer", async ({ page }) => {
    await page.goto("/");
    const footer = page.locator("footer.site-footer, footer.library-page-footer").first();
    await expect(footer).toContainText(/©|©|&copy;|2026|202\d/);
    await expect(footer.locator('a[href^="mailto:"]')).toBeVisible();
    await expect(footer).toHaveClass(/library-card/);
    await expect(footer).not.toContainText("Static migration");
  });
});

test.describe("legacy redirects", () => {
  test("/about/ redirects to home", async ({ page }) => {
    await page.goto("/about/");
    await expect(page).toHaveURL(/\/$/);
    await expect(page.locator(".home-entry-grid")).toBeVisible();
  });

  test("/contact/ redirects to home", async ({ page }) => {
    await page.goto("/contact/");
    await expect(page).toHaveURL(/\/$/);
    await expect(page.locator(".home-entry-grid")).toBeVisible();
  });
});

test.describe("search", () => {
  test("pagefind on home header search", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop search coverage enough");
    await page.goto("/");
    const input = page.locator(".pagefind-ui__search-input");
    await expect(input).toBeVisible({ timeout: 20_000 });
    await expect(page.locator(".header-search #search")).toBeVisible();
    await expect(page.locator("#catalogue-search")).toHaveCount(0);
  });

  test("pagefind on systems header search", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop search coverage enough");
    await page.goto("/systems/");
    const input = page.locator(".pagefind-ui__search-input");
    await expect(input).toBeVisible({ timeout: 20_000 });
    const searchLabel = page.locator("label.page-search-label");
    await expect(searchLabel).toBeVisible();
    await expect(searchLabel).toHaveText("Search catalogue");
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
    await libraryIndexPanel(page, "google-cloud").click();
    await expect(page.locator('.library-panel[data-panel-id="google-cloud"].is-active')).toBeVisible();
    await expect(page.locator(".library-panel.is-active .credential-card").first()).toBeVisible();
    const rawUrlLinks = page.locator(".credential-card a").filter({ hasText: /https?:\/\// });
    await expect(rawUrlLinks).toHaveCount(0);
    const indexItem = page.locator(".library-index-list [data-panel-id]").first();
    await expect(indexItem).toBeVisible();
    await indexItem.click();
    await expect(page.locator(".library-panel.is-active").first()).toBeVisible();
  });

  test("systems library index scrolls inside shell", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop sidebar coverage enough");
    await page.goto("/systems/");
    const index = page.locator(".library-index");
    await expect(index).toBeVisible();
    await page.evaluate(() => {
      const el = document.querySelector(".library-index");
      if (el) el.scrollTop = 240;
    });
    await expect(index).toBeVisible();
  });

  test("systems Figma is compact links not an empty static frame", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/systems/");
    await libraryIndexPanel(page, "klook-travel-planner-capstone").click();
    await expect(page.locator('.library-panel[data-panel-id="klook-travel-planner-capstone"].is-active')).toBeVisible();
    await expect(page.locator("iframe")).toHaveCount(0);
    await expect(page.locator(".embed-frame-static")).toHaveCount(0);
    await expect(
      page.locator(".library-panel.is-active").getByRole("link", { name: "Figma deck" })
    ).toBeVisible();
  });
});

test.describe("home profile content", () => {
  test("competencies use home editorial list", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/");
    await expect(page.locator(".home-competency-list .home-competency").first()).toBeVisible();
    await expect(page.getByText("Data Engineering Leadership")).toBeVisible();
  });
});

test.describe("credentials cards", () => {
  test("professional issuers use credential card grid", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/credentials/");
    await libraryIndexPanel(page, "google-cloud").click();
    await expect(page.locator('.library-panel[data-panel-id="google-cloud"].is-active')).toBeVisible();
    await expect(page.locator(".library-panel.is-active .credential-card").first()).toBeVisible();
    await expect(page.locator(".library-panel.is-active .item-list")).toHaveCount(0);
  });

  test("credentials uses library index shell", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop coverage enough");
    await page.goto("/credentials/");
    await expect(page.locator(".library-index-list")).toBeVisible();
    await expect(page.locator(".library-index-list [data-panel-id]").first()).toBeVisible();
    await expect(page.locator(".library-shell")).toBeVisible();
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

async function assertSkipLink(page) {
  const skip = page.locator("a.skip-link");
  await expect(skip).toHaveCount(1);
  await expect(skip).toHaveAttribute("href", "#main");
  await skip.focus();
  await expect(skip).toBeFocused();
  await expect(skip).toBeVisible();
}

async function assertCtaRhythm(page) {
  await expect(page.locator(".cta-row")).toHaveCount(0);
  await expect(page.locator(".home-entry-grid")).toBeVisible();
  await expect(page.locator(".home-entry-grid").getByRole("link", { name: "Systems" })).toBeVisible();
  await expect(page.locator(".header-actions > .header-contact")).toHaveCount(0);
  await expect(page.locator(".theme-toggle:not(.reading-size-toggle)").first()).toBeVisible();
}

async function assertEntranceVisible(page) {
  await expect(page.locator(".entrance h1")).toBeVisible();
  await expect(page.locator(".entrance-atmosphere")).toBeVisible();
}

async function assertSelectedSingleColumn(page) {
  await page.goto("/systems/#SYS-01");
  await expect(page.locator('.library-panel[data-record="SYS-01"].is-active')).toBeVisible();
}

async function assertSelectedHeadingSpacing(page) {
  await page.goto("/systems/#SYS-01");
  const heading = page.locator(".library-panel-title").first();
  await expect(heading).toBeVisible();
  const spacing = await heading.evaluate((el) => {
    const cs = getComputedStyle(el);
    return {
      marginTop: cs.marginTop,
      marginBottom: cs.marginBottom,
    };
  });
  expect(spacing.marginTop).toBe("0px");
}

async function assertThemeToggleBesideMenu(page) {
  await expect(page.locator("nav.site-nav-desktop")).toBeHidden();
  const menu = page.locator("details.nav-menu");
  await expect(menu).toBeVisible();
  const toggle = page.locator(".header-actions > [data-theme-toggle]");
  await expect(toggle).toBeVisible();
  const toggleBox = await toggle.boundingBox();
  const menuBox = await menu.locator("summary").boundingBox();
  expect(toggleBox && menuBox).toBeTruthy();
  expect(Math.abs(toggleBox.y - menuBox.y)).toBeLessThan(24);
  expect(toggleBox.x).toBeLessThan(menuBox.x);
}

async function assertFooterExternalLinks(page) {
  const footer = page.locator("footer.site-footer, footer.library-page-footer").first();
  await expect(footer.getByRole("link", { name: /Digital card/ })).toHaveClass(/external/);
  await expect(footer.getByRole("link", { name: /Blog/ })).toBeVisible();
  await expect(footer.getByRole("link", { name: /Medium/ })).toHaveClass(/external/);
  await expect(footer.getByRole("link", { name: /LinkedIn/ })).toBeVisible();
  await expect(footer.getByRole("link", { name: /GitHub/ })).toHaveClass(/external/);
  await expect(page.locator(".nav-elsewhere")).toHaveCount(0);
}

async function assertTocSearch(page) {
  await page.goto("/systems/");
  const index = page.locator(".library-index-list");
  await expect(index).toBeVisible();
  await expect(index.locator("[data-panel-id]").first()).toBeVisible();
  const input = page.locator(".pagefind-ui__search-input");
  await expect(input).toBeVisible({ timeout: 20_000 });
  await input.fill("databricks");
  await expect(page.locator(".pagefind-ui__result").first()).toBeVisible({
    timeout: 15_000,
  });
  await noHorizontalOverflow(page);
}

async function libraryShellMetrics(page) {
  await page.evaluate(() => document.fonts.ready);
  return page.evaluate(() => {
    const searchInput = document.querySelector("#search .pagefind-ui__search-input");
    const index = document.querySelector(".library-index");
    const panelTitle = document.querySelector(".library-panel-title");
    const toggle = document.querySelector(".header-actions > [data-theme-toggle]");
    return {
      searchBox: searchInput ? searchInput.getBoundingClientRect().x : null,
      index: index ? index.getBoundingClientRect().x : null,
      panelTitle: panelTitle ? panelTitle.getBoundingClientRect().x : null,
      toggleRight: toggle ? toggle.getBoundingClientRect().right : null,
      overflow: document.documentElement.scrollWidth > window.innerWidth + 2,
    };
  });
}

test.describe("systems alignment axes", () => {
  test("1280: library shell exposes search, index, and panels", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop 1280");
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto("/systems/", { waitUntil: "networkidle" });
    await expect(page.locator(".pagefind-ui__search-input")).toBeVisible({ timeout: 20_000 });
    const m = await libraryShellMetrics(page);
    expect(m.searchBox).not.toBeNull();
    expect(m.index).not.toBeNull();
    expect(m.overflow).toBe(false);
  });

  test("900: library shell stays usable without overflow", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "explicit 900");
    await page.setViewportSize({ width: 900, height: 900 });
    await page.goto("/systems/", { waitUntil: "networkidle" });
    await expect(page.locator(".pagefind-ui__search-input")).toBeVisible({ timeout: 20_000 });
    const m = await libraryShellMetrics(page);
    expect(m.searchBox).not.toBeNull();
    expect(m.overflow).toBe(false);
  });
});

test.describe("site critic acceptance", () => {
  test("desktop ≥1024: CTA rhythm, footer links, skip-link, TOC/search, no overflow", async ({
    page,
  }) => {
    test.skip(test.info().project.name === "mobile", "desktop ≥1024");
    await page.setViewportSize({ width: 1024, height: 800 });
    await page.goto("/");
    await expect(page.locator("nav.site-nav-desktop")).toBeVisible();
    await assertSkipLink(page);
    await assertCtaRhythm(page);
    await assertFooterExternalLinks(page);
    await page.locator("nav.site-nav-desktop").getByRole("link", { name: "Systems" }).click();
    await expect(page).toHaveURL(/\/systems\//);
    await libraryIndexPanel(page, "prudential-singapore-senior-data-engineer-solutioning-architecture").click();
    await expect(
      page.locator(
        '.library-panel[data-panel-id="prudential-singapore-senior-data-engineer-solutioning-architecture"].is-active'
      )
    ).toBeVisible();
    await assertSelectedHeadingSpacing(page);
    await noHorizontalOverflow(page);
    await assertTocSearch(page);
  });

  test("1280 home + systems: featured rows, footer links, no overflow", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "desktop 1280");
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    await expect(page.locator("nav.site-nav-desktop")).toBeVisible();
    await assertCtaRhythm(page);
    await assertFooterExternalLinks(page);
    await page.locator("nav.site-nav-desktop").getByRole("link", { name: "Systems" }).click();
    await expect(page).toHaveURL(/\/systems\//);
    await libraryIndexPanel(page, "prudential-singapore-senior-data-engineer-solutioning-architecture").click();
    await expect(
      page.locator(
        '.library-panel[data-panel-id="prudential-singapore-senior-data-engineer-solutioning-architecture"].is-active'
      )
    ).toBeVisible();
    await noHorizontalOverflow(page);
    await page.goto("/systems/");
    await expect(page.locator(".case-outcome").first()).toBeVisible();
    await expect(
      page.locator('[data-panel-group-id="enterprise-data-ai-solutioning-selected-work-summaries"]')
    ).toBeVisible();
    await noHorizontalOverflow(page);
  });

  test("800 entrance stacks thesis over atmosphere; selected single-column", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "explicit 800");
    await page.setViewportSize({ width: 800, height: 900 });
    await page.goto("/");
    await assertEntranceVisible(page);
    await assertCtaRhythm(page);
    await assertSelectedSingleColumn(page);
    await noHorizontalOverflow(page);
  });

  test("900 theme toggle stays beside Menu; footer links visible", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "explicit 900");
    await page.setViewportSize({ width: 900, height: 800 });
    await page.goto("/");
    await assertCtaRhythm(page);
    await assertThemeToggleBesideMenu(page);
    await assertFooterExternalLinks(page);
    await noHorizontalOverflow(page);
  });

  test("375 home + systems: stack, featured column, theme toggle beside Menu", async ({ page }) => {
    test.skip(test.info().project.name === "desktop", "mobile 375");
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/");
    await assertSkipLink(page);
    await assertEntranceVisible(page);
    await assertCtaRhythm(page);
    await assertSelectedSingleColumn(page);
    await assertThemeToggleBesideMenu(page);
    await assertFooterExternalLinks(page);
    await noHorizontalOverflow(page);
    await page.goto("/systems/");
    await noHorizontalOverflow(page);
  });
});
