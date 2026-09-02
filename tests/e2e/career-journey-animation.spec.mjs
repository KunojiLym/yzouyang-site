import { test, expect } from "@playwright/test";

test.use({ video: "retain-on-failure" });

function parseMaxSeconds(duration) {
  return Math.max(
    0,
    ...String(duration || "0s")
      .split(",")
      .map((part) => {
        const trimmed = part.trim();
        if (trimmed.endsWith("ms")) return Number.parseFloat(trimmed) / 1000;
        return Number.parseFloat(trimmed);
      })
      .filter((n) => Number.isFinite(n)),
  );
}

test.describe("career journey deck motion", () => {
  test("advances horizontally with opacity-only active fade", async ({ page }) => {
    await page.goto("/career-journey/", { waitUntil: "networkidle" });

    const rail = page.locator(".cj-slides");
    await expect(rail).toHaveClass(/cj-js/);
    await expect(page.locator(".cj-slide").first()).toHaveClass(/is-active/);
    await expect(page.locator("[data-cj-current]")).toHaveText(/^Slide 1 of/);

    const motionConfig = await page.evaluate(() => {
      const slide = document.querySelector(".cj-slide");
      const inactive = document.querySelector(".cj-slide:not(.is-active)");
      const child = slide?.firstElementChild;
      const slideStyle = slide ? getComputedStyle(slide) : null;
      const inactiveStyle = inactive ? getComputedStyle(inactive) : null;
      const childStyle = child ? getComputedStyle(child) : null;
      return {
        transitionDuration: slideStyle?.transitionDuration || "",
        transitionProperty: slideStyle?.transitionProperty || "",
        transform: slideStyle?.transform || "",
        inactiveTransform: inactiveStyle?.transform || "",
        animationName: childStyle?.animationName || "",
      };
    });

    expect(parseMaxSeconds(motionConfig.transitionDuration)).toBeLessThanOrEqual(0.25);
    expect(motionConfig.transitionProperty).toMatch(/opacity/);
    expect(motionConfig.transitionProperty).not.toMatch(/transform/);
    expect(["none", "matrix(1, 0, 0, 1, 0, 0)"]).toContain(motionConfig.transform);
    expect(["none", "matrix(1, 0, 0, 1, 0, 0)"]).toContain(motionConfig.inactiveTransform);
    expect(motionConfig.animationName === "none" || !motionConfig.animationName.includes("cj-active-enter")).toBeTruthy();

    await page.locator("[data-cj-next]").click();

    const samples = [];
    for (let i = 0; i < 6; i += 1) {
      await page.waitForTimeout(80);
      samples.push(await rail.evaluate((el) => Math.round(el.scrollLeft)));
    }

    await expect(page.locator("[data-cj-current]")).toHaveText(/^Slide 2 of/);
    await expect(page.locator(".cj-slide").nth(1)).toHaveClass(/is-active/);
    expect(Math.max(...samples)).toBeGreaterThan(0);
    expect(new Set(samples).size).toBeGreaterThan(1);
  });

  test("prefers-reduced-motion shows every slide and data-step", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/career-journey/", { waitUntil: "networkidle" });

    const state = await page.evaluate(() => {
      const slides = [...document.querySelectorAll(".cj-slide")];
      return slides.map((slide) => {
        const style = getComputedStyle(slide);
        const steps = [...slide.querySelectorAll("[data-step]")].map((el) => {
          const cs = getComputedStyle(el);
          return {
            opacity: Number.parseFloat(cs.opacity),
            transform: cs.transform,
            revealed: el.classList.contains("is-revealed"),
          };
        });
        return {
          opacity: Number.parseFloat(style.opacity),
          transform: style.transform,
          steps,
        };
      });
    });

    expect(state.length).toBeGreaterThan(1);
    expect(state.reduce((n, slide) => n + slide.steps.length, 0)).toBeGreaterThan(0);
    for (const slide of state) {
      expect(slide.opacity).toBe(1);
      expect(["none", "matrix(1, 0, 0, 1, 0, 0)"]).toContain(slide.transform);
      for (const step of slide.steps) {
        expect(step.opacity).toBe(1);
        expect(["none", "matrix(1, 0, 0, 1, 0, 0)"]).toContain(step.transform);
        expect(step.revealed).toBe(true);
      }
    }
  });
});
