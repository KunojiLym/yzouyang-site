import { test, expect } from "@playwright/test";

test.use({ video: "retain-on-failure" });

test.describe("career journey deck motion", () => {
  test("advances horizontally with active-slide animation", async ({ page }) => {
    await page.goto("/career-journey/", { waitUntil: "networkidle" });

    const rail = page.locator(".cj-slides");
    await expect(rail).toHaveClass(/cj-js/);
    await expect(page.locator(".cj-slide").first()).toHaveClass(/is-active/);
    await expect(page.locator("[data-cj-current]")).toHaveText("1");

    const motionConfig = await page.evaluate(() => {
      const slide = document.querySelector(".cj-slide");
      const child = slide?.firstElementChild;
      const slideStyle = slide ? getComputedStyle(slide) : null;
      const childStyle = child ? getComputedStyle(child) : null;
      return {
        transitionDuration: slideStyle?.transitionDuration || "",
        animationName: childStyle?.animationName || "",
        animationDuration: childStyle?.animationDuration || "",
      };
    });

    expect(motionConfig.transitionDuration).not.toBe("0s");
    expect(motionConfig.animationName).toContain("cj-active-enter");
    expect(motionConfig.animationDuration).not.toBe("0s");

    await page.locator("[data-cj-next]").click();

    const samples = [];
    for (let i = 0; i < 6; i += 1) {
      await page.waitForTimeout(80);
      samples.push(await rail.evaluate((el) => Math.round(el.scrollLeft)));
    }

    await expect(page.locator("[data-cj-current]")).toHaveText("2");
    await expect(page.locator(".cj-slide").nth(1)).toHaveClass(/is-active/);
    expect(Math.max(...samples)).toBeGreaterThan(0);
    expect(new Set(samples).size).toBeGreaterThan(1);
  });
});
