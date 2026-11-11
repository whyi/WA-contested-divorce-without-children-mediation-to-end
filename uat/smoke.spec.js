import { test as base, expect } from "@playwright/test";
import { approvedOrigin, permittedRead } from "./safety.js";

const test = base.extend({
  page: async ({ page }, use) => {
    let writes = 0;
    let scriptErrors = 0;
    page.on("pageerror", () => { scriptErrors += 1; });
    await page.route("**/*", async (route) => {
      const request = route.request();
      if (permittedRead(request.url(), request.method())) {
        await route.continue();
      } else {
        if (new URL(request.url()).origin === approvedOrigin) writes += 1;
        await route.abort("blockedbyclient");
      }
    });
    await use(page);
    expect(writes, "Anonymous smoke must not attempt server writes").toBe(0);
    expect(scriptErrors, "No uncaught browser script errors").toBe(0);
  },
});

test("SMOKE-01", async ({ request }) => {
  const response = await request.get("/healthz", { maxRedirects: 0 });
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ status: "ok" });
});

test("SMOKE-02", async ({ request }) => {
  const response = await request.get("/readyz", { maxRedirects: 0 });
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ status: "ready" });
});

test("SMOKE-03", async ({ request }) => {
  for (const path of ["/api/v1/dashboard/status", "/api/auth/sessions"]) {
    const response = await request.get(path, { maxRedirects: 0 });
    expect([401, 403], "Anonymous account access must be denied").toContain(response.status());
  }
});

test("SMOKE-04", async ({ page }) => {
  const response = await page.goto("/");
  expect(response.status()).toBe(200);
  await expect(page).toHaveTitle(/Casework/);
  await page.locator("#login-entry").click();
  await expect(page.locator("#auth-entry-content")).toBeVisible();
  await expect(page.locator("#email-entry-form")).toBeVisible();
  await expect(page.locator("#entry-email")).toBeEditable();
  await expect(page.locator("#email-entry-form button[type=submit]")).toBeEnabled();
  await page.locator("#entry-email").fill("smoke@example.invalid");
  await expect(page.locator("#login-form")).toBeHidden();
});

for (const [id, source] of [
  ["SMOKE-05", "demo1"],
  ["SMOKE-06", "demo2"],
]) {
  test(id, async ({ page }) => {
    await page.goto(`/demo/start?source=${source}`);
    await expect(page).toHaveURL(`${approvedOrigin}/demo/start?source=${source}`);
    await expect(page.locator("#demo-case-choice-page")).toBeVisible();
    await expect(page.locator("#demo-case-documents-link")).toBeVisible();
    await expect(page.locator("#demo-case-wizard-link")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Active cases", exact: true })).toBeHidden();
    await expect(page.getByRole("heading", { name: "Your case workspace", exact: true })).toBeHidden();
  });
}
