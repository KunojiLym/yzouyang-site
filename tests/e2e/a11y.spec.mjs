import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Automated accessibility gate. This does not replace the manual contrast
// review already recorded in docs/design-system.md, but it makes sure a
// future change (new component, new page) can't silently regress contrast,
// landmarks, or ARIA wiring without a human noticing.
const ROUTES = ["/", "/systems/", "/notes/", "/credentials/"];

// Pagefind's third-party markup on Systems/Notes/Credentials has known upstream
// a11y quirks outside this repo's control; scoped out rather than ignored
// so a real regression elsewhere on those pages still fails the build.
const KNOWN_THIRD_PARTY_EXCLUDES = ["#search"];

test.describe("automated accessibility (axe-core, WCAG2A/AA)", () => {
  for (const route of ROUTES) {
    test(`${route} has no axe violations`, async ({ page }, testInfo) => {
      await page.goto(route, { waitUntil: "networkidle" });

      const builder = new AxeBuilder({ page })
        .options({ iframes: false })
        .withTags(["wcag2a", "wcag2aa"])
        .exclude(KNOWN_THIRD_PARTY_EXCLUDES);

      const results = await builder.analyze();

      // Drop violations that only affect nodes inside the Figma embed's
      // iframe — upstream/third-party markup outside this repo's control.
      // axe reports a node's location as a target path, e.g.
      // ["iframe", ".some-figma-class"]; target[0] === "iframe" means the
      // node lives inside that embed rather than in first-party markup.
      const violations = results.violations
        .map((violation) => ({
          ...violation,
          nodes: violation.nodes.filter((node) => node.target[0] !== "iframe"),
        }))
        .filter((violation) => violation.nodes.length > 0);

      if (violations.length) {
        const summary = violations
          .map(
            (v) =>
              `${v.id} (${v.impact}): ${v.help} — ${v.nodes.length} node(s)\n  ${v.helpUrl}`
          )
          .join("\n");
        await testInfo.attach("axe-violations.json", {
          body: JSON.stringify(violations, null, 2),
          contentType: "application/json",
        });
        expect(violations, `axe violations on ${route}:\n${summary}`).toEqual([]);
      }
    });
  }
});
