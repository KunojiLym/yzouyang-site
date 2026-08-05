import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Automated accessibility gate. This does not replace the manual contrast
// review already recorded in docs/design-system.md, but it makes sure a
// future change (new component, new page) can't silently regress contrast,
// landmarks, or ARIA wiring without a human noticing.
const ROUTES = ["/", "/about/", "/portfolio/", "/credentials/"];

// Pagefind's third-party markup on Portfolio/Credentials has known upstream
// a11y quirks outside this repo's control; scoped out rather than ignored
// so a real regression elsewhere on those pages still fails the build.
const KNOWN_THIRD_PARTY_EXCLUDES = ["#search"];

test.describe("automated accessibility (axe-core, WCAG2A/AA)", () => {
  for (const route of ROUTES) {
    test(`${route} has no axe violations`, async ({ page }, testInfo) => {
      await page.goto(route, { waitUntil: "networkidle" });

      const builder = new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa"])
        .exclude(KNOWN_THIRD_PARTY_EXCLUDES);

      const results = await builder.analyze();

      if (results.violations.length) {
        const summary = results.violations
          .map(
            (v) =>
              `${v.id} (${v.impact}): ${v.help} — ${v.nodes.length} node(s)\n  ${v.helpUrl}`
          )
          .join("\n");
        await testInfo.attach("axe-violations.json", {
          body: JSON.stringify(results.violations, null, 2),
          contentType: "application/json",
        });
        expect(results.violations, `axe violations on ${route}:\n${summary}`).toEqual([]);
      }
    });
  }
});
