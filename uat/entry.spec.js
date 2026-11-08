import { readFileSync } from "node:fs";
import { test, expect } from "@playwright/test";

const origin = "https://casework-regression.invalid";
const html = readFileSync(new URL("../src/app/static/index.html", import.meta.url), "utf8");
const caseId = "00000000-0000-4000-8000-000000000071";

const missingWizardAttempt = {
  status: "needs_information",
  attempt_exists: false,
  needs: ["A separation date."],
  report: null,
};

async function installFixtures(page, { mode = null, hasCase = true, authenticated = false, dashboardStatus = 200, intake = {}, wizardAttempt = missingWizardAttempt } = {}) {
  let signedIn = authenticated;
  const unexpected = [];
  const requests = [];
  const scriptErrors = [];
  page.on("pageerror", (error) => scriptErrors.push(error.message));
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== origin) {
      await route.abort("blockedbyclient");
      return;
    }
    const path = url.pathname;
    requests.push(`${request.method()} ${path}`);
    if (request.isNavigationRequest()) {
      await route.fulfill({ contentType: "text/html", body: html });
      return;
    }
    let status = 200;
    let body;
    if (path === "/api/auth/login" && request.method() === "POST") {
      signedIn = true;
      body = { mfa_required: false };
    } else if (request.method() !== "GET") {
      unexpected.push(`${request.method()} ${path}`);
      await route.abort("blockedbyclient");
      return;
    } else if (path === "/api/v1/dashboard/status") {
      status = signedIn ? dashboardStatus : 401;
      body = status === 200 ? {
        data: {
          has_cases: hasCase,
          case_count: hasCase ? 1 : 0,
          active_case_count: hasCase ? 1 : 0,
          cases: hasCase ? [{ id: caseId, title: "Synthetic regression case", workflow_mode: mode }] : [],
        },
      } : { detail: status === 401 ? "Sign in required." : "Regression service unavailable." };
    } else {
      const fixtures = {
        "/api/auth/providers": { google: false },
        "/api/v1/closed-cases": { cases: [] },
        "/api/v1/support/config": { contact_url: null },
        "/api/billing/packages": { packages: [] },
        "/api/billing/account/entitlement": { status: "free" },
        [`/api/billing/cases/${caseId}/purchases`]: { purchases: [] },
        [`/cases/${caseId}/settlement-planning`]: { consented: false, profile_revision: 0, settlement_revision: 0 },
        [`/cases/${caseId}/profile-facts`]: { facts: [] },
        [`/cases/${caseId}/settlement-planning/ledger-events`]: [],
        [`/cases/${caseId}/settlement-planning/disclosure`]: {
          available: false, provider: "disabled", data_sent: "No AI configured.",
        },
        [`/cases/${caseId}/settlement-planning/offer-responses`]: [],
        [`/cases/${caseId}/wizard-intake`]: { draft: intake },
        [`/cases/${caseId}/wizard-attempt`]: wizardAttempt,
      };
      if (!Object.hasOwn(fixtures, path)) {
        unexpected.push(`${request.method()} ${path}`);
        await route.abort("blockedbyclient");
        return;
      }
      body = fixtures[path];
    }
    await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  });
  return {
    requests,
    signOut: () => { signedIn = false; },
    verify: () => {
      expect(unexpected, "Unexpected API requests must not be silently mocked").toEqual([]);
      expect(scriptErrors, "Full application script must execute without errors").toEqual([]);
    },
  };
}

async function signIn(page) {
  await page.goto(origin);
  await page.locator("#login-entry").click();
  await page.locator("#login-email").fill("synthetic@example.invalid");
  await page.locator("#login-password").fill("synthetic-password-not-a-secret");
  await page.locator("#login-form button[type=submit]").click();
}

async function expectNoDetour(page) {
  await expect(page).toHaveURL(`${origin}/`);
  await expect(page.locator("#account-tools")).toBeHidden();
  await expect(page.locator("#preparation-view")).toBeHidden();
  await expect(page.locator(".hero")).toBeHidden();
  await expect(page.getByRole("heading", { name: "Active cases", exact: true })).toBeHidden();
  await expect(page.getByRole("heading", { name: "Your case workspace", exact: true, includeHidden: true })).toHaveCount(0);
  await expect(page.locator("#dashboard-header, #dashboard-title, #dashboard-intro")).toHaveCount(0);
}

test("no case: login and refresh open the start choice, not another page", async ({ page }) => {
  const fixture = await installFixtures(page, { hasCase: false });
  await signIn(page);
  for (const reload of [false, true]) {
    if (reload) await page.reload();
    await expect(page.locator("#case-create-dialog")).toBeVisible();
    await expect(page.locator("#case-start-upload")).toBeVisible();
    await expect(page.locator("#case-start-wizard")).toBeVisible();
    await expect(page.locator("#settlement-planner")).toBeHidden();
    await expectNoDetour(page);
  }
  fixture.verify();
});

for (const [label, mode, intake] of [
  ["no preparation mode", null, {}],
  ["documents preparation", "upload", {}],
  ["incomplete wizard", "wizard", { filed: "", role: "" }],
  ["unfiled wizard", "wizard", { filed: "no", role: "" }],
  ["complete wizard", "wizard", { filed: "yes", role: "petitioner" }],
]) {
  test(`active case (${label}): login and refresh go straight to attempts`, async ({ page }) => {
    const fixture = await installFixtures(page, { mode, intake });
    await signIn(page);
    for (const reload of [false, true]) {
      if (reload) await page.reload();
      await expect(page.locator("#settlement-planner")).toBeVisible();
      await expect(page.locator("#settlement-planner-status")).toContainText("Attempt workspace ready.");
      await expect(page.locator("#settlement-planner-title")).toHaveText("Negotiation attempts");
      await expect(page.locator("#settlement-attempt-progress-title")).toBeVisible();
      await expect(page.locator("#settlement-generate")).toBeVisible();
      await expect(page.locator("#case-create-dialog")).toBeHidden();
      await expect(page.locator("#settlement-ledger-json")).toBeHidden();
      await expect(page.locator("#settlement-review-information .product-boundary-disclosure")).toBeHidden();
      await expect(page.getByRole("heading", { name: "Evidence-grounded settlement planning", exact: true })).toBeHidden();
      await expectNoDetour(page);
      if (mode) {
        await expect(page.locator("#settlement-edit-intake")).toBeVisible();
        await expect(page.locator("#settlement-edit-intake")).toHaveAttribute("href", `/onboarding/${mode}?case_id=${caseId}`);
      }
    }
    expect(fixture.requests.filter((path) => path.endsWith("/wizard-intake"))).toEqual([]);
    expect(fixture.requests.filter((path) => path.startsWith("POST") && path.endsWith("/wizard-attempt"))).toEqual([]);
    expect(fixture.requests.includes(`GET /cases/${caseId}/wizard-attempt`)).toBe(mode === "wizard");
    expect(fixture.requests).toContain(`GET /cases/${caseId}/settlement-planning`);
    fixture.verify();
  });
}

test("wizard case without an attempt: reason, create action and the single edit link, no auto-creation", async ({ page }) => {
  const fixture = await installFixtures(page, { mode: "wizard" });
  await signIn(page);
  await expect(page.locator("#settlement-wizard-empty")).toBeVisible();
  await expect(page.locator("#settlement-wizard-needs")).toContainText("A separation date.");
  await expect(page.getByRole("button", { name: "Create Attempt 1 from your case information" })).toBeVisible();
  await expect(page.locator("#settlement-wizard-empty #settlement-edit-intake")).toBeVisible();
  await expect(page.getByRole("link", { name: "Edit case information" })).toHaveCount(1);
  await expect(page.locator("#settlement-wizard-attempt")).toBeHidden();
  await expect(page.locator("#settlement-generate")).toBeVisible();
  expect(fixture.requests.filter((path) => path.startsWith("POST") && path.endsWith("/wizard-attempt"))).toEqual([]);
  fixture.verify();
});

test("wizard case with Attempt 1: the entered values are listed exactly with the edit link beside them", async ({ page }) => {
  const fixture = await installFixtures(page, {
    mode: "wizard",
    wizardAttempt: {
      status: "exists",
      attempt_exists: true,
      needs: [],
      report: {
        wizard_revision: 3,
        role: "petitioner",
        included: [
          { label: "Family home", kind: "asset", amount_cents: 51234567 },
          { label: "Home loan", kind: "debt", amount_cents: 30100000 },
        ],
        excluded: [{ kind: "asset", label: "Vehicle", reason: "No amount was entered." }],
        dates: { start: "2015-06-01", start_source: "marriage", separation: "2024-02-15" },
        milestones: 4,
        terms: 2,
      },
    },
  });
  await signIn(page);
  const panel = page.locator("#settlement-wizard-attempt");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText("Asset — Family home: $512,345.67");
  await expect(panel).toContainText("Debt — Home loan: $301,000.00");
  await expect(panel).toContainText("Vehicle — No amount was entered.");
  await expect(panel).toContainText("Role: Petitioner. Marriage: 2015-06-01. Separation: 2024-02-15.");
  await expect(panel.locator("#settlement-edit-intake")).toBeVisible();
  await expect(page.locator("#settlement-wizard-empty")).toBeHidden();
  fixture.verify();
});

test("failed dashboard after login stays an explicit error, not a start or attempt", async ({ page }) => {
  const fixture = await installFixtures(page, { dashboardStatus: 503 });
  await signIn(page);
  await expect(page.locator("#dashboard-error")).toBeVisible();
  await expect(page.locator("#dashboard-error")).toContainText("Regression service unavailable.");
  await expect(page.locator("#case-create-dialog")).toBeHidden();
  await expect(page.locator("#settlement-planner")).toBeHidden();
  fixture.verify();
});

test("expired session does not show a cached attempt on refresh", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true });
  await page.goto(origin);
  await expect(page.locator("#settlement-planner-status")).toContainText("Attempt workspace ready.");
  fixture.signOut();
  await page.reload();
  await expect(page.locator("#account-dashboard")).toBeHidden();
  await expect(page.locator("#login-entry")).toBeVisible();
  await page.locator("#login-entry").click();
  await expect(page.locator("#login-tab")).toBeVisible();
  await expect(page.locator("#case-create-dialog")).toBeHidden();
  fixture.verify();
});

async function installDocumentsFixtures(page, offer, { startCase = false, creationStatuses = [200], creationGate = null } = {}) {
  const state = { ...offer };
  let hasCase = !startCase;
  const unexpected = [];
  const creations = [];
  const puts = [];
  const scriptErrors = [];
  page.on("pageerror", (error) => scriptErrors.push(error.message));
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== origin) {
      await route.abort("blockedbyclient");
      return;
    }
    if (request.isNavigationRequest()) {
      await route.fulfill({ contentType: "text/html", body: html });
      return;
    }
    const path = url.pathname;
    let body;
    if (startCase && path === "/cases" && request.method() === "POST") {
      creations.push(JSON.parse(request.postData() || "{}"));
      if (creationGate) await creationGate;
      const status = creationStatuses[Math.min(creations.length - 1, creationStatuses.length - 1)];
      if (status === 200) hasCase = true;
      await route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(status === 200 ? { id: caseId } : { detail: "Case creation unavailable. Please retry." }),
      });
      return;
    } else if (path === `/cases/${caseId}/existing-offer` && request.method() === "PUT") {
      const sent = JSON.parse(request.postData() || "{}");
      puts.push(sent);
      Object.assign(state, {
        exists: sent.exists,
        notes: sent.notes,
        document_ids: sent.document_ids || [],
      });
      body = state;
    } else if (request.method() !== "GET") {
      unexpected.push(`${request.method()} ${path}`);
      await route.abort("blockedbyclient");
      return;
    } else if (path === `/cases/${caseId}/existing-offer`) {
      body = state;
    } else {
      const fixtures = {
        "/api/auth/providers": { google: false },
        "/api/v1/closed-cases": { cases: [] },
        "/api/v1/support/config": { contact_url: null },
        "/api/billing/packages": { packages: [] },
        "/api/billing/account/entitlement": { status: "free" },
        "/api/v1/dashboard/status": {
          data: {
            has_cases: hasCase,
            case_count: hasCase ? 1 : 0,
            active_case_count: hasCase ? 1 : 0,
            cases: hasCase ? [{ id: caseId, title: "Synthetic documents case", workflow_mode: "upload" }] : [],
          },
        },
      };
      if (path.startsWith("/api/v1/materials/config")) {
        body = {
          import_enabled: true,
          max_upload_bytes: 2097152,
          supported_extensions: [".pdf", ".docx"],
          max_attachments: 5,
          attachment_count: 0,
          max_pdf_pages: 200,
        };
      } else if (Object.hasOwn(fixtures, path)) {
        body = fixtures[path];
      } else {
        unexpected.push(`${request.method()} ${path}`);
        await route.abort("blockedbyclient");
        return;
      }
    }
    await route.fulfill({ contentType: "application/json", body: JSON.stringify(body) });
  });
  return {
    puts,
    creations,
    verify: () => {
      expect(unexpected, "Unexpected API requests must not be silently mocked").toEqual([]);
      expect(scriptErrors, "Full application script must execute without errors").toEqual([]);
    },
  };
}

const noOffer = { exists: null, notes: null, document_ids: [], documents: [], assets: [], asset_terms: [] };

test("documents start: one click creates a case and opens materials without a confirmation screen", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, noOffer, { startCase: true });
  await page.goto(origin);
  await page.locator("#case-title-input").fill("Synthetic document case label");
  await page.getByRole("button", { name: "I have documents" }).click();
  await expect(page).toHaveURL(`${origin}/onboarding/upload?case_id=${caseId}`);
  await expect(page.getByRole("heading", { name: "Start with your case materials", exact: true })).toBeVisible();
  await expect(page.locator("#materials-file-input")).toBeEnabled();
  await expect(page.locator("#case-create-dialog")).toBeHidden();
  await expect(page.getByRole("button", { name: "Create case and continue to documents", includeHidden: true })).toHaveCount(0);
  await expect(page.getByRole("checkbox", { name: "The other party has already made an offer" })).not.toBeChecked();
  expect(fixture.creations).toEqual([{ case_title: "Synthetic document case label", workflow_mode: "upload" }]);
  expect(fixture.puts).toEqual([]);
  fixture.verify();
});

test("documents start: pending creation prevents duplicate clicks and workflow switching", async ({ page }) => {
  let releaseCreation;
  const creationGate = new Promise((resolve) => { releaseCreation = resolve; });
  const fixture = await installDocumentsFixtures(page, noOffer, { startCase: true, creationGate });
  await page.goto(origin);
  await page.locator("#case-start-upload").click();
  await expect(page.locator("#case-create-status")).toHaveText("Creating your case…");
  await expect(page.locator("#case-start-upload")).toBeDisabled();
  await expect(page.locator("#case-start-wizard")).toBeDisabled();
  await expect(page.locator("#case-create-cancel")).toBeDisabled();
  await expect(page.locator("#case-create-offer-intake")).toBeHidden();
  await page.keyboard.press("Escape");
  await expect(page.locator("#case-create-dialog")).toBeVisible();
  expect(fixture.creations).toHaveLength(1);
  releaseCreation();
  await expect(page).toHaveURL(`${origin}/onboarding/upload?case_id=${caseId}`);
  expect(fixture.creations).toHaveLength(1);
  fixture.verify();
});

test("documents start: failure stays on the choices and retry opens materials", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, noOffer, { startCase: true, creationStatuses: [503, 200] });
  await page.goto(origin);
  await page.locator("#case-start-upload").click();
  await expect(page.locator("#case-create-status")).toHaveText("Case creation unavailable. Please retry.");
  await expect(page).toHaveURL(`${origin}/`);
  await expect(page.locator("#case-create-offer-intake")).toBeHidden();
  await expect(page.locator("#case-start-upload")).toBeEnabled();
  await expect(page.locator("#case-start-wizard")).toBeEnabled();
  await expect(page.locator("#case-create-cancel")).toBeEnabled();
  await page.locator("#case-start-upload").click();
  await expect(page).toHaveURL(`${origin}/onboarding/upload?case_id=${caseId}`);
  await expect(page.getByRole("heading", { name: "Start with your case materials", exact: true })).toBeVisible();
  expect(fixture.creations).toEqual([
    { case_title: null, workflow_mode: "upload" },
    { case_title: null, workflow_mode: "upload" },
  ]);
  expect(fixture.puts).toEqual([]);
  fixture.verify();
});

test("wizard start: the existing offer intake and creation confirmation remain", async ({ page }) => {
  const fixture = await installFixtures(page, { hasCase: false, authenticated: true });
  await page.goto(origin);
  await page.locator("#case-start-wizard").click();
  await expect(page.locator("#case-create-choice")).toBeHidden();
  await expect(page.locator("#case-offer-question")).toBeVisible();
  await expect(page.getByRole("button", { name: "Create case and start the wizard" })).toBeVisible();
  await page.locator("#case-create-continue").click();
  await expect(page.locator("#case-create-status")).toHaveText("Answer whether the other party has already made an offer.");
  await expect(page).toHaveURL(`${origin}/`);
  expect(fixture.requests).not.toContain("POST /cases");
  fixture.verify();
});

test("documents path: upload is visible first and the offer is an optional checkbox below it", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, noOffer);
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await expect(page.locator("#materials-workflow")).toBeVisible();
  await expect(page.locator(".materials-drop")).toBeVisible();
  await expect(page.locator("#existing-offer-question")).toBeHidden();
  const toggle = page.getByRole("checkbox", { name: "The other party has already made an offer" });
  await expect(toggle).toBeVisible();
  await expect(toggle).not.toBeChecked();
  await expect(page.locator("#existing-offer-details")).toBeHidden();
  await expect(page.getByRole("button", { name: "Continue", exact: true })).toBeEnabled();
  const upload = await page.locator("#materials-import").boundingBox();
  const box = await toggle.boundingBox();
  expect(upload.y).toBeLessThan(box.y);
  fixture.verify();
});

test("documents path: checking the offer requires saved details before Continue", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, noOffer);
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  const toggle = page.getByRole("checkbox", { name: "The other party has already made an offer" });
  const next = page.getByRole("button", { name: "Continue", exact: true });
  await expect(next).toBeEnabled();
  await toggle.check();
  await expect(page.locator("#existing-offer-details")).toBeVisible();
  await expect(next).toBeDisabled();
  await expect(page.locator("#existing-offer-continue-status")).toContainText("Save offer notes or an offer document to continue.");
  await page.locator("#existing-offer-notes").fill("House to them, car to me");
  await expect(next).toBeDisabled();
  await page.getByRole("button", { name: "Save offer details" }).click();
  await expect(next).toBeEnabled();
  expect(fixture.puts).toEqual([{ exists: true, notes: "House to them, car to me", document_ids: [] }]);
  fixture.verify();
});

test("documents path: a saved offer restores the checkbox and unchecking asks before removing it", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, { ...noOffer, exists: true, notes: "Saved offer notes" });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  const toggle = page.getByRole("checkbox", { name: "The other party has already made an offer" });
  await expect(toggle).toBeChecked();
  await expect(page.locator("#existing-offer-notes")).toHaveValue("Saved offer notes");
  await expect(page.getByRole("button", { name: "Continue", exact: true })).toBeEnabled();

  page.once("dialog", (dialog) => dialog.dismiss());
  await toggle.click();
  await expect(toggle).toBeChecked();
  expect(fixture.puts).toEqual([]);

  page.once("dialog", (dialog) => dialog.accept());
  await toggle.click();
  await expect(toggle).not.toBeChecked();
  await expect(page.locator("#existing-offer-details")).toBeHidden();
  expect(fixture.puts).toEqual([{ exists: false, notes: null, document_ids: [] }]);
  fixture.verify();
});

for (const source of ["demo1", "demo2"]) {
  test(`${source}: demo start choices remain intact after workspace deletion`, async ({ page }) => {
    const fixture = await installFixtures(page);
    await page.goto(`${origin}/demo/start?source=${source}`);
    await expect(page.locator("#demo-case-choice-dialog")).toBeVisible();
    await expect(page.locator("#demo-case-documents-link")).toBeVisible();
    await expect(page.locator("#demo-case-wizard-link")).toBeVisible();
    await expect(page.locator("#demo-workspace-header")).toBeHidden();
    await expect(page.locator("#dashboard-header, #dashboard-title, #dashboard-intro")).toHaveCount(0);
    fixture.verify();
  });
}
