import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: "entry.spec.js",
  workers: 1,
  retries: 0,
  forbidOnly: true,
  timeout: 15_000,
  reporter: "list",
  outputDir: "test-results",
  use: {
    browserName: "chromium",
    serviceWorkers: "block",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
});
