import { test, expect } from "@playwright/test";

// Visual regression baseline. Screenshots are compared against committed
// PNGs in this file's __snapshots__ directory (Playwright's default
// location); a diff beyond the default threshold fails the build.
//
// IMPORTANT — one-time setup required before this gate is active:
// baseline images are NOT included yet. On a machine with the Playwright
// browsers installed, run once against a known-good build:
//
//   python scripts/build.py
//   npx playwright test tests/e2e/visual.spec.mjs --update-snapshots
//
// then commit the generated __snapshots__ directory. Until that's done,
// this spec will fail every run (no baseline to compare against) — keep it
// out of the required CI gate (see .github/workflows/ci.yml comment) until
// baselines exist, then move it into the required path.
const ROUTES = ["/", "/about/", "/portfolio/", "/credentials/"];

function slugFor(route) {
  const trimmed = route.replace(/^\/|\/$/g, "");
  return trimmed === "" ? "home" : trimmed.replace(/\//g, "-");
}

test.describe("visual regression", () => {
  for (const route of ROUTES) {
    test(`${route} matches baseline`, async ({ page }) => {
      await page.goto(route, { waitUntil: "networkidle" });
      // Freeze CSS animations/transitions (e.g. the `rise` entrance) to
      // their end state so a timing difference doesn't register as a
      // false-positive visual diff.
      await expect(page).toHaveScreenshot(`${slugFor(route)}.png`, {
        fullPage: true,
        animations: "disabled",
      });
    });
  }
});
