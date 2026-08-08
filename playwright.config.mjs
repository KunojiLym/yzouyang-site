import { defineConfig } from "@playwright/test";

const PORT = Number(process.env.E2E_PORT || 8765);
const HOST = process.env.E2E_HOST || "127.0.0.1";
const BASE = process.env.E2E_BASE_URL || `http://${HOST}:${PORT}`;

export default defineConfig({
  testDir: "tests/e2e",
  globalSetup: "./tests/e2e/global-setup.mjs",
  globalTeardown: "./tests/e2e/global-teardown.mjs",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? undefined : 4,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: BASE,
    trace: "on-first-retry",
    colorScheme: "dark",
  },
  projects: [
    {
      name: "desktop",
      use: { browserName: "chromium", viewport: { width: 1440, height: 900 } },
    },
    {
      name: "mobile",
      use: {
        browserName: "chromium",
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
});
