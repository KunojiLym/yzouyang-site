import { test, expect } from "@playwright/test";

async function setTheme(page, theme) {
  await page.addInitScript((value) => {
    localStorage.setItem("yz-theme", value);
  }, theme);
}

function contrastOf(fg, bg) {
  const parse = (value) => {
    const match = value.match(/rgba?\(([^)]+)\)/i);
    if (!match) return null;
    const parts = match[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    return parts.slice(0, 3);
  };
  const channel = (c) => {
    const x = c / 255;
    return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
  };
  const lum = (rgb) => 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2]);
  const fgRgb = parse(fg);
  const bgRgb = parse(bg);
  if (!fgRgb || !bgRgb) return 0;
  const lighter = Math.max(lum(fgRgb), lum(bgRgb));
  const darker = Math.min(lum(fgRgb), lum(bgRgb));
  return (lighter + 0.05) / (darker + 0.05);
}

test.describe("design system contract", () => {
  for (const theme of ["dark", "light"]) {
    test(`record-domains contrast is at least 4.5 on Systems (${theme})`, async ({ page }) => {
      await setTheme(page, theme);
      await page.goto("/systems/#SYS-01", { waitUntil: "load" });
      await page.locator(".library-panel.is-active .record-domains").first().waitFor({ state: "visible" });
      const measured = await page.evaluate(() => {
        const nodes = [...document.querySelectorAll(".record-domains")];
        const visible = nodes.find((node) => {
          const style = getComputedStyle(node);
          const rect = node.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        });
        if (!visible) return { error: "no visible .record-domains" };
        const color = getComputedStyle(visible).color;
        let background = "transparent";
        let node = visible;
        while (node) {
          const bg = getComputedStyle(node).backgroundColor;
          const match = bg.match(/rgba?\(([^)]+)\)/i);
          if (match) {
            const parts = match[1].split(/[,\s/]+/).filter(Boolean).map(Number);
            const alpha = parts.length > 3 ? parts[3] : 1;
            if (alpha >= 0.99) {
              background = bg;
              break;
            }
          }
          node = node.parentElement;
        }
        return { color, background };
      });
      expect(measured.error, JSON.stringify(measured)).toBeUndefined();
      const ratio = contrastOf(measured.color, measured.background);
      expect(ratio, `${theme} ${measured.color} on ${measured.background}`).toBeGreaterThanOrEqual(4.5);
    });

    test(`primary border matches the main mix (${theme})`, async ({ page }) => {
      await setTheme(page, theme);
      await page.goto("/", { waitUntil: "domcontentloaded" });
      const borders = await page.evaluate((activeTheme) => {
        const primary = document.querySelector(".entrance-action--primary");
        if (!primary) return { error: "missing primary" };
        const probe = document.createElement("div");
        const historical = activeTheme === "light"
          ? "color-mix(in srgb, #c49a5a 40%, #6b4f10)"
          : "color-mix(in srgb, #c49a5a 55%, rgb(74 92 78 / 28%))";
        probe.style.borderTop = `1px solid ${historical}`;
        document.body.appendChild(probe);
        return {
          actual: getComputedStyle(primary).borderTopColor,
          expected: getComputedStyle(probe).borderTopColor,
        };
      }, theme);
      expect(borders.error).toBeUndefined();
      expect(borders.actual).toBe(borders.expected);
    });
  }
});
