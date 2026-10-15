import { test, expect } from "@playwright/test";

const LIVE_ROUTES = ["/", "/systems/", "/notes/", "/credentials/"];
const REDIRECTS = [
  { from: "/about/", path: "/" },
  { from: "/contact/", path: "/" },
  { from: "/career-journey/", path: "/" },
  { from: "/portfolio/", path: "/systems/", allowHash: true },
  { from: "/work/", path: "/systems/", allowHash: true },
  { from: "/systems/catalogue/", path: "/systems/", allowHash: true },
  { from: "/perspectives/", path: "/notes/", allowHash: true },
  { from: "/blog/", path: "/notes/", allowHash: true },
];

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function expectedRedirectUrl(baseURL, { path, allowHash = false }) {
  const href = new URL(path, baseURL).href;
  if (allowHash) {
    return new RegExp(`^${escapeRegExp(href)}(?:#.+)?$`);
  }
  return href;
}

function libraryIndexPanel(page, panelId) {
  return page.locator(`.library-index-list [data-panel-id="${panelId}"]`).first();
}

async function visibleLibraryPanelIds(page) {
  return page.locator(".library-panels > .library-panel").evaluateAll((nodes) =>
    nodes
      .filter((node) => getComputedStyle(node).display !== "none")
      .map((node) => node.getAttribute("data-panel-id"))
  );
}

/** Wait until layout-shift total is unchanged for several consecutive samples. */
async function waitForClsStable(
  page,
  { intervalMs = 500, stableRounds = 3, timeoutMs = 12_000 } = {}
) {
  const deadline = Date.now() + timeoutMs;
  let last = null;
  let rounds = 0;
  while (Date.now() < deadline) {
    await page.waitForTimeout(intervalMs);
    const value = await page.evaluate(() => window.__cls || 0);
    if (last !== null && value === last) {
      rounds += 1;
      if (rounds >= stableRounds) return value;
    } else {
      rounds = 0;
      last = value;
    }
  }
  const final = await page.evaluate(() => window.__cls || 0);
  throw new Error(`CLS did not stabilize within ${timeoutMs}ms (last value ${final})`);
}

async function librarySplitGridColumnCount(page) {
  return page.locator(".library-split").evaluate((el) => {
    const columns = getComputedStyle(el).gridTemplateColumns.trim();
    if (!columns || columns === "none") return 0;
    return columns.split(/\s+/).length;
  });
}

async function activeIndexRowInView(page) {
  return page.evaluate(() => {
    const body = document.querySelector(".library-index-body");
    const active = document.querySelector(
      ".library-index-trigger[aria-current='location']"
    );
    if (!body || !active) return false;
    const row = active.closest("li");
    if (!row) return false;
    const margin = 12;
    const bodyRect = body.getBoundingClientRect();
    const rowRect = row.getBoundingClientRect();
    return (
      rowRect.top >= bodyRect.top + margin - 1 &&
      rowRect.bottom <= bodyRect.bottom - margin + 1
    );
  });
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

async function assertHomeEntrance(page) {
  await expect(page.locator(".home-featured-records")).toBeVisible();
  await expect(page.locator(".home-record-row")).toHaveCount(4);
  await expect(page.locator(".home-practice-item").first()).toBeVisible();
}

async function assertFooterLinks(page) {
  const footer = page.locator("footer.site-footer, footer.library-page-footer").first();
  await expect(footer).toHaveClass(/library-card/);
  await expect(footer.locator('a[href^="mailto:"]')).toBeVisible();
  await expect(footer.getByRole("link", { name: /Digital card/ })).toHaveClass(/external/);
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
  for (const spec of REDIRECTS) {
    test(`${spec.from} redirects`, async ({ page, baseURL }) => {
      await page.goto(spec.from);
      await expect(page).toHaveURL(expectedRedirectUrl(baseURL, spec));
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
    await expect(footer).not.toContainText("Static migration");
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

  test("paced sections, featured strip, and practice areas", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".home-snap-section")).toHaveCount(4);
    await expect(page.locator(".home-record-row")).toHaveCount(4);
    await expect(page.locator(".home-record-strip")).toBeVisible();
    await expect(page.locator(".home-context-strip")).toBeVisible();
    await expect(page.locator(".home-context-strip li").first()).toContainText("Singapore");
    await expect(page.locator(".entrance-actions")).toBeVisible();
    await assertHomeEntrance(page);
    await expect(
      page.getByRole("heading", { name: "Governed data platforms", exact: true })
    ).toBeVisible();
    await expect(page.getByText("Operating principle")).toBeVisible();
    await expect(page.locator(".home-entry-grid")).toHaveCount(0);
    await expect(page.locator("main.home-route")).toBeVisible();
    await expect(page.locator("[data-theme-toggle]").first()).toBeVisible();
  });

  test("featured grid, one frame, and one primary action", async ({ page }) => {
    test.skip(test.info().project.name === "mobile", "widths are set per case");
    const widths = [375, 768, 1024, 1280, 1440];
    for (const width of widths) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/", { waitUntil: "networkidle" });
      await expect(page.locator(".home-scroll-hint")).toHaveCount(0);
      await expect(page.locator(".entrance-action--primary")).toHaveCount(1);
      await expect(page.locator(".entrance-action--secondary")).toHaveCount(1);
      await expect(page.locator(".home-record-row")).toHaveCount(4);

      const metrics = await page.evaluate(() => {
        const contentLeft = (el) => {
          const rect = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          return rect.left + parseFloat(cs.paddingLeft) + parseFloat(cs.borderLeftWidth);
        };
        const hero = document.querySelector(".home-hero .entrance-copy");
        const strip = document.querySelector(".home-record-strip");
        const header = document.querySelector(".site-header");
        const track = strip.querySelector(".home-record-strip-track");
        const columns = getComputedStyle(track).gridTemplateColumns.split(" ").filter(Boolean).length;
        const cards = [...document.querySelectorAll(".home-record-row")].map((el) => {
          const rect = el.getBoundingClientRect();
          return rect.left >= -1 && rect.right <= window.innerWidth + 1;
        });
        const ctaTops = [...document.querySelectorAll(".home-record-cta")].map(
          (el) => el.getBoundingClientRect().top
        );
        const rowTops = [...document.querySelectorAll(".home-record-row")].map(
          (el) => el.getBoundingClientRect().top
        );
        const ctaDeltaByRow = rowTops.map((top, index) => ({ top, cta: ctaTops[index] }));
        const grouped = new Map();
        for (const item of ctaDeltaByRow) {
          const key = Math.round(item.top);
          const list = grouped.get(key) || [];
          list.push(item.cta);
          grouped.set(key, list);
        }
        const ctaAligned = [...grouped.values()].every((tops) => {
          const min = Math.min(...tops);
          const max = Math.max(...tops);
          return max - min <= 1;
        });
        const search = document.querySelector("#search .pagefind-ui__search-input");
        const theme = document.querySelector("[data-theme-toggle]");
        const menu = document.querySelector(".nav-menu > summary");
        const reading = document.querySelector(".header-actions > [data-reading-size-toggle]");
        const heightOf = (el) => (el ? el.getBoundingClientRect().height : 0);
        const visibleSteps = [...document.querySelectorAll(".reading-size-step")]
          .map((el) => el.getBoundingClientRect())
          .filter((rect) => rect.width > 0 && rect.height > 0);
        const proof = document.querySelector(".entrance-proof");
        const proofCs = getComputedStyle(proof);
        const probe = document.createElement("span");
        probe.style.color = "var(--text-default)";
        probe.style.borderTop = "1px solid var(--line-soft)";
        document.body.appendChild(probe);
        const probeCs = getComputedStyle(probe);
        const textColor = probeCs.color;
        const lineSoft = probeCs.borderTopColor;
        probe.remove();
        const primary = document.querySelector(".entrance-action--primary");
        const secondary = document.querySelector(".entrance-action--secondary");
        const order = [...hero.children].map((el) => el.className);
        const ledeIndex = order.findIndex((name) => name.includes("lede"));
        const proofIndex = order.findIndex((name) => name.includes("entrance-proof"));
        const actionIndex = order.findIndex((name) => name.includes("entrance-actions"));
        return {
          pageOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
          stripScrollable: strip.scrollWidth > strip.clientWidth + 1,
          cards,
          columns,
          heroX: contentLeft(hero),
          stripX: contentLeft(strip),
          headerX: contentLeft(header),
          ctaAligned,
          searchH: heightOf(search),
          themeH: heightOf(theme),
          menuH: heightOf(menu),
          readingH: heightOf(reading),
          themeBorder: getComputedStyle(theme).borderTopColor,
          lineSoft,
          stepMin: visibleSteps.reduce(
            (min, rect) => Math.min(min, rect.width, rect.height),
            Number.POSITIVE_INFINITY
          ),
          proofSize: parseFloat(proofCs.fontSize),
          proofMatchesText: proofCs.color === textColor,
          primaryH: heightOf(primary),
          primaryBorderTop: parseFloat(getComputedStyle(primary).borderTopWidth),
          secondaryBorderTop: parseFloat(getComputedStyle(secondary).borderTopWidth),
          proofBeforeActions: ledeIndex < proofIndex && proofIndex < actionIndex,
        };
      });

      expect(metrics.pageOverflow, `overflow @${width}`).toBe(false);
      expect(metrics.stripScrollable, `strip scroll @${width}`).toBe(false);
      expect(metrics.cards.every(Boolean), `cards in view @${width}`).toBe(true);
      expect(Math.abs(metrics.heroX - metrics.stripX), `hero vs strip @${width}`).toBeLessThanOrEqual(1);
      expect(Math.abs(metrics.heroX - metrics.headerX), `hero vs header @${width}`).toBeLessThanOrEqual(1);
      expect(metrics.ctaAligned, `cta alignment @${width}`).toBe(true);
      expect(metrics.proofBeforeActions, `proof order @${width}`).toBe(true);
      expect(metrics.proofMatchesText, `proof colour @${width}`).toBe(true);
      expect(metrics.themeBorder, `theme border @${width}`).toBe(metrics.lineSoft);
      expect(metrics.primaryBorderTop, `primary border @${width}`).toBeGreaterThan(0);
      expect(metrics.secondaryBorderTop, `secondary border @${width}`).toBe(0);
      expect(metrics.primaryH, `primary height @${width}`).toBeGreaterThanOrEqual(39);
      expect(metrics.primaryH, `primary height @${width}`).toBeLessThanOrEqual(41);

      if (width < 640) {
        expect(metrics.columns, `columns @${width}`).toBe(1);
      } else if (width < 1152) {
        expect(metrics.columns, `columns @${width}`).toBe(2);
      } else {
        expect(metrics.columns, `columns @${width}`).toBe(4);
      }

      if (width === 1280) {
        expect(metrics.proofSize, "proof size @1280").toBeGreaterThanOrEqual(16.5);
        expect(metrics.proofSize, "proof size @1280").toBeLessThanOrEqual(17.5);
        expect(Math.abs(metrics.heroX - 24), "hero x @1280").toBeLessThanOrEqual(1);
      }
      if (width === 1440) {
        expect(metrics.proofSize, "proof size @1440").toBeGreaterThanOrEqual(18.5);
        expect(metrics.proofSize, "proof size @1440").toBeLessThanOrEqual(19.5);
        expect(Math.abs(metrics.heroX - 104), "hero x @1440").toBeLessThanOrEqual(1);
      }
      if (width <= 768) {
        expect(metrics.searchH, `search height @${width}`).toBeGreaterThanOrEqual(39);
        expect(metrics.searchH, `search height @${width}`).toBeLessThanOrEqual(41);
        expect(metrics.themeH, `theme height @${width}`).toBeGreaterThanOrEqual(39);
        expect(metrics.themeH, `theme height @${width}`).toBeLessThanOrEqual(41);
        expect(metrics.menuH, `menu height @${width}`).toBeGreaterThanOrEqual(39);
        expect(metrics.menuH, `menu height @${width}`).toBeLessThanOrEqual(41);
        const compact = [metrics.searchH, metrics.themeH, metrics.menuH];
        expect(Math.max(...compact) - Math.min(...compact), `header controls @${width}`).toBeLessThanOrEqual(0.5);
      } else {
        const controls = [metrics.searchH, metrics.themeH];
        if (metrics.readingH > 0) controls.push(metrics.readingH);
        if (metrics.menuH > 0) controls.push(metrics.menuH);
        const min = Math.min(...controls);
        const max = Math.max(...controls);
        expect(max - min, `header control height @${width} ${controls.join(",")}`).toBeLessThanOrEqual(0.5);
      }
      if (width >= 1024) {
        expect(metrics.stepMin, `reading step @${width}`).toBeGreaterThanOrEqual(24);
      }
    }
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
  test("exactly one library panel is visible after a deep link and an index click", async ({
    page,
  }) => {
    test.skip(test.info().project.name === "mobile", "desktop panel stack");
    await page.setViewportSize({ width: 1440, height: 900 });

    await page.goto("/systems/#stb-data-engineer-applied-ml", { waitUntil: "load" });
    await expect
      .poll(() => visibleLibraryPanelIds(page))
      .toEqual(["stb-data-engineer-applied-ml"]);
    await libraryIndexPanel(
      page,
      "prudential-singapore-senior-data-engineer-solutioning-architecture"
    ).click();
    await expect
      .poll(() => visibleLibraryPanelIds(page))
      .toEqual(["prudential-singapore-senior-data-engineer-solutioning-architecture"]);

    await page.goto("/notes/#NOTE-2025-021", { waitUntil: "load" });
    await expect.poll(() => visibleLibraryPanelIds(page)).toEqual(["NOTE-2025-021"]);
    await page.locator(".library-index-rail-expand").click();
    const noteTrigger = libraryIndexPanel(page, "NOTE-2026-005");
    await expect(noteTrigger).toBeVisible();
    await noteTrigger.click();
    await expect.poll(() => visibleLibraryPanelIds(page)).toEqual(["NOTE-2026-005"]);
  });

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
    await page.goto("/notes/#NOTE-2026-005", { waitUntil: "load" });
    await expect(page.locator(".library-shell")).toBeVisible();
    await expect(page.locator('.library-panel[data-panel-id="NOTE-2026-005"].is-active')).toBeVisible();
  });

  test("notes deep link shows full reading pane at 1024px", async ({ browser }) => {
    test.skip(test.info().project.name === "mobile", "viewport is set per case");
    const context = await browser.newContext({
      viewport: { width: 1024, height: 800 },
    });
    await context.addInitScript(() => {
      try {
        localStorage.clear();
      } catch {
        /* ignore */
      }
    });
    const page = await context.newPage();
    await page.goto("/notes/#NOTE-2026-005", { waitUntil: "load" });
    await page.waitForFunction(
      () => !document.querySelector(".library-split")?.classList.contains("is-booting")
    );
    const paneHeight = await page.locator(".library-pane").evaluate((el) => {
      return el.getBoundingClientRect().height;
    });
    expect(paneHeight).toBeGreaterThan(400);
    const active = page.locator(".library-panel.is-active");
    await expect(active).toHaveAttribute("data-panel-id", "NOTE-2026-005");
    await expect(active.locator(".library-panel-title")).toBeVisible();
    await expect(active.locator(".library-panel-body")).toBeVisible();
    await context.close();
  });

  test("notes deep link scrolls catalogue index to active article", async ({
    page,
    context,
  }) => {
    test.skip(test.info().project.name === "mobile", "desktop sidebar coverage");
    await context.addInitScript(() => {
      localStorage.setItem("yz-library-index-pinned:/notes/", "1");
    });
    await page.goto("/notes/#NOTE-2025-021", { waitUntil: "load" });
    await expect(
      page.locator('.library-panel[data-panel-id="NOTE-2025-021"].is-active')
    ).toBeVisible();
    await expect(
      page.locator('.library-index-trigger[aria-current="location"]')
    ).toHaveAttribute("data-panel-id", "NOTE-2025-021");
    await expect.poll(() => activeIndexRowInView(page)).toBe(true);
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

  test("notes index starts collapsed and Escape dismisses overlay", async ({ page, context }) => {
    test.skip(test.info().project.name === "mobile", "desktop rail overlay coverage");
    await context.addInitScript(() => {
      localStorage.clear();
    });
    await page.goto("/notes/");
    await expect(page.locator(".library-split")).toHaveClass(/is-index-unpinned/);
    await expect(page.locator(".library-split")).toHaveClass(/is-index-collapsed/);
    await expect(page.locator(".library-reading-context")).toBeVisible();
    const expand = page.locator(".library-index-rail-expand");
    await expect(expand).toHaveAttribute("aria-expanded", "false");
    await expand.click();
    await expect(page.locator(".library-split")).toHaveClass(/is-index-overlay-open/);
    await expect(page.locator(".library-reading-context")).toBeHidden();
    await expect(expand).toHaveAttribute("aria-expanded", "true");
    await page.keyboard.press("Escape");
    await expect(page.locator(".library-split")).not.toHaveClass(/is-index-overlay-open/);
    await expect(page.locator(".library-reading-context")).toBeVisible();
    await expect(expand).toHaveAttribute("aria-expanded", "false");
    await page.locator(".library-index-rail-pin").click();
    await expect(page.locator(".library-reading-context")).toBeHidden();
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
    await expect(page.locator(".home-entry-grid")).toHaveCount(0);
    await page.goto("/systems/#SYS-01", { waitUntil: "load" });
    await expect(page.locator('.library-panel[data-record="SYS-01"].is-active')).toBeVisible();
    expect(await librarySplitGridColumnCount(page)).toBe(1);
    await noHorizontalOverflow(page);
  });

  test("library routes use one layout across the 48rem/49rem seam", async ({ browser }) => {
    test.skip(test.info().project.name === "mobile", "explicit viewports");
    const libraryRoutes = [
      "/notes/#NOTE-2026-005",
      "/systems/#SYS-01",
      "/credentials/#google-cloud",
    ];
    const stackedWidths = [775, 769, 783, 784];
    for (const width of stackedWidths) {
      const context = await browser.newContext({
        viewport: { width, height: 900 },
      });
      await context.addInitScript(() => {
        try {
          localStorage.clear();
        } catch {
          /* ignore */
        }
      });
      const page = await context.newPage();
      for (const path of libraryRoutes) {
        await page.goto(path, { waitUntil: "load" });
        await page.waitForFunction(
          () => !document.querySelector(".library-split")?.classList.contains("is-booting")
        );
        expect(await librarySplitGridColumnCount(page), `${path} @${width}px`).toBe(1);
        await expect(page.locator(".library-panel.is-active")).toBeVisible();
      }
      await context.close();
    }

    const mobileContext = await browser.newContext({
      viewport: { width: 768, height: 900 },
    });
    await mobileContext.addInitScript(() => {
      try {
        localStorage.clear();
      } catch {
        /* ignore */
      }
    });
    const mobilePage = await mobileContext.newPage();
    await mobilePage.goto("/notes/#NOTE-2026-005", { waitUntil: "load" });
    await expect(mobilePage.locator(".library-split")).toHaveClass(/is-detail-open/);
    await expect(mobilePage.locator(".library-index-list")).toBeHidden();
    await mobileContext.close();
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

test.describe("library focus order", () => {
  test("first Tab on a deep-linked record is the skip link", async ({ page }) => {
    const routes = [
      { path: "/notes/#NOTE-2026-005", panel: "NOTE-2026-005" },
      { path: "/systems/#verify", panel: "verify" },
      { path: "/credentials/#academic-qualifications", panel: "academic-qualifications" },
    ];
    for (const route of routes) {
      await page.goto(route.path, { waitUntil: "load" });
      await expect(
        page.locator(`.library-panel[data-panel-id="${route.panel}"].is-active`)
      ).toBeVisible();
      await page.keyboard.press("Tab");
      await expect(page.locator("a.skip-link")).toBeFocused();
      const panelScroll = await page.locator(".library-panels").evaluate((el) => el.scrollTop);
      const windowScroll = await page.evaluate(() => window.scrollY);
      expect(panelScroll, route.path).toBe(0);
      expect(windowScroll, route.path).toBe(0);
    }
  });

  test("library DOM order: index before pane before footer", async ({ page }) => {
    const viewports = [
      { width: 1280, height: 800 },
      { width: 800, height: 600 },
      { width: 375, height: 812 },
    ];
    const routes = [
      { label: "systems-overview", path: "/systems/" },
      { label: "systems-deep", path: "/systems/#verify" },
      { label: "credentials-deep", path: "/credentials/#google-cloud" },
      { label: "notes-deep", path: "/notes/#NOTE-2026-005" },
    ];
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      for (const route of routes) {
        await page.goto(route.path, { waitUntil: "load" });
        await page.waitForFunction(
          () => !document.querySelector("#library-split")?.classList.contains("is-booting")
        );
        const order = await page.evaluate(() => {
          const index = document.querySelector(".library-index");
          const pane = document.querySelector(".library-pane");
          const footer = document.querySelector("footer.library-page-footer");
          if (!index || !pane || !footer) {
            return {
              ok: false,
              missing: {
                index: !index,
                pane: !pane,
                footer: !footer,
              },
            };
          }
          const nodes = [index, pane, footer];
          for (let i = 0; i < nodes.length - 1; i += 1) {
            const relation = nodes[i].compareDocumentPosition(nodes[i + 1]);
            if ((relation & Node.DOCUMENT_POSITION_FOLLOWING) === 0) {
              return { ok: false, relation };
            }
          }
          return { ok: true };
        });
        expect(order.ok, `${route.label} @ ${viewport.width}px ${JSON.stringify(order)}`).toBe(
          true
        );
      }
    }
  });

  test("legacy note section hash opens the note that contains it", async ({ page }) => {
    const hash = "2-i-setting-up-databricks-free-edition-account";
    await page.goto(`/notes/#${hash}`, { waitUntil: "load" });
    const active = page.locator(".library-panel.is-active");
    await expect(active).toHaveAttribute("data-panel-id", "NOTE-2025-012");
    await expect(active.locator(`[id$="-${hash}"]`)).toHaveCount(1);
    await page.keyboard.press("Tab");
    await expect(page.locator("a.skip-link")).toBeFocused();
  });
});

test.describe("library without JavaScript", () => {
  test("systems and notes render catalogue content", async ({ browser }) => {
    test.skip(test.info().project.name === "mobile", "desktop library layout");
    for (const path of ["/systems/", "/notes/", "/credentials/"]) {
      const context = await browser.newContext({ javaScriptEnabled: false });
      const page = await context.newPage();
      await page.goto(path, { waitUntil: "domcontentloaded" });
      const panel = page.locator(".library-panel:not([hidden])").first();
      await expect(panel).toBeVisible();
      const text = await panel.locator(".library-panel-body").innerText();
      expect(text.trim().length).toBeGreaterThan(20);
      await context.close();
    }
  });

  test("notes deep link renders without a blank pane", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto("/notes/#NOTE-2026-005", { waitUntil: "domcontentloaded" });
    await expect(page.locator('.library-panel[data-panel-id="NOTE-2026-005"]')).toBeVisible();
    const text = await page
      .locator('.library-panel[data-panel-id="NOTE-2026-005"] .library-panel-body')
      .innerText();
    expect(text.trim().length).toBeGreaterThan(40);
    await context.close();
  });
});

test.describe("library boot CLS", () => {
  test.describe.configure({ mode: "serial" });

  test("notes and deep links stay under 0.1", async ({ browser }) => {
    test.setTimeout(180_000);
    test.skip(test.info().project.name === "mobile", "viewports are set per case");
    const cases = [
      { path: "/", width: 1280, height: 800 },
      { path: "/", width: 375, height: 812 },
      { path: "/notes/", width: 1280, height: 800 },
      { path: "/notes/", width: 375, height: 812 },
      { path: "/notes/#NOTE-2026-005", width: 1280, height: 800 },
      { path: "/notes/#NOTE-2026-005", width: 1024, height: 800 },
      { path: "/notes/#NOTE-2026-005", width: 775, height: 800 },
      { path: "/notes/#NOTE-2026-005", width: 769, height: 800 },
      { path: "/notes/#NOTE-2026-005", width: 900, height: 800 },
      { path: "/notes/#NOTE-2026-005", width: 784, height: 800 },
      { path: "/notes/#NOTE-2026-005", width: 375, height: 812 },
      { path: "/systems/#SYS-03", width: 1280, height: 800 },
      { path: "/systems/#SYS-03", width: 1024, height: 800 },
      { path: "/systems/#SYS-03", width: 900, height: 800 },
      { path: "/systems/#SYS-03", width: 800, height: 800 },
      { path: "/systems/#SYS-03", width: 784, height: 800 },
      { path: "/systems/#SYS-03", width: 769, height: 800 },
      { path: "/systems/#SYS-03", width: 375, height: 812 },
      { path: "/systems/#SYS-01", width: 800, height: 800 },
      { path: "/systems/#SYS-01", width: 769, height: 800 },
      { path: "/credentials/#google-cloud", width: 1024, height: 800 },
      { path: "/credentials/#additional-training-bootcamps", width: 800, height: 800 },
      { path: "/credentials/#additional-training-bootcamps", width: 769, height: 800 },
      { path: "/notes/#NOTE-2025-015", width: 800, height: 800 },
      { path: "/notes/#NOTE-2025-015", width: 769, height: 800 },
      { path: "/credentials/#google-cloud", width: 900, height: 800 },
      { path: "/credentials/#google-cloud", width: 800, height: 800 },
      { path: "/credentials/#google-cloud", width: 784, height: 800 },
      { path: "/credentials/#google-cloud", width: 769, height: 800 },
    ];
    const scores = [];
    for (const item of cases) {
      const context = await browser.newContext({
        viewport: { width: item.width, height: item.height },
      });
      await context.addInitScript(() => {
        try {
          localStorage.clear();
        } catch (e) {
          /* ignore */
        }
        window.__cls = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) window.__cls += entry.value;
          }
        }).observe({ type: "layout-shift", buffered: true });
      });
      const page = await context.newPage();
      await page.goto(item.path, { waitUntil: "load" });
      const hash = new URL(item.path, "http://localhost").hash.slice(1);
      if (hash) {
        await page
          .locator(`.library-panel[data-panel-id="${hash}"].is-active`)
          .waitFor({ state: "visible", timeout: 8000 });
      }
      await page.evaluate(() => document.fonts.ready);
      const cls = await waitForClsStable(page);
      scores.push(`${item.path} @${item.width} ${cls.toFixed(3)}`);
      expect(cls, `${item.path} @${item.width}`).toBeLessThan(0.1);
      await context.close();
    }
    console.log(scores.join("\n"));
  });
});
