import { defineConfig } from "@playwright/test";
import { approvedOrigin, validateTarget } from "./safety.js";

export default defineConfig({
  testDir: ".",
  testMatch: "smoke.spec.js",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  forbidOnly: true,
  reporter: [["./report.js"]],
  outputDir: "test-results",
  use: {
    baseURL: validateTarget(process.env.UAT_BASE_URL ?? approvedOrigin),
    browserName: "chromium",
    ignoreHTTPSErrors: false,
    serviceWorkers: "block",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
});
