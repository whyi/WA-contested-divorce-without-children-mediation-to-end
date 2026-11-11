import { defineConfig } from "@playwright/test";
import { approvedOrigin, validateTarget } from "./safety.js";

export default defineConfig({
  testDir: ".",
  testMatch: "smoke.spec.js",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  forbidOnly: true,
  reporter: [["./report.js"]],
  outputDir: "test-results",
  use: {
    baseURL: validateTarget(process.env.UAT_BASE_URL ?? approvedOrigin),
    browserName: "chromium",
    navigationTimeout: 60_000,
    ignoreHTTPSErrors: false,
    serviceWorkers: "block",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
});
