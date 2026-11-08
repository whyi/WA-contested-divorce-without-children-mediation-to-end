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

async function installFixtures(page, { mode = null, hasCase = true, authenticated = false, dashboardStatus = 200, intake = {}, wizardAttempt = missingWizardAttempt, extraReads = {}, mutationHandler = null } = {}) {
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
    } else if (request.method() !== "GET" && mutationHandler) {
      const result = await mutationHandler(request);
      if (!result) {
        unexpected.push(`${request.method()} ${path}`);
        await route.abort("blockedbyclient");
        return;
      }
      await route.fulfill({ status: result.status || 200, contentType: result.contentType || "application/json", body: typeof result.body === "string" ? result.body : JSON.stringify(result.body) });
      return;
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
        [`/cases/${caseId}/wizard-intake`]: { revision: 1, draft: intake },
        [`/cases/${caseId}/existing-offer`]: { exists: false, notes: null, document_ids: [], documents: [], assets: [], asset_terms: [] },
        [`/cases/${caseId}/wizard-attempt`]: wizardAttempt,
        ...extraReads,
      };
      if (path.startsWith("/api/v1/materials/config")) {
        body = { import_enabled: true, max_upload_bytes: 2097152, supported_extensions: [".pdf", ".docx"], max_attachments: 5, attachment_count: 0, max_pdf_pages: 200 };
        await route.fulfill({ contentType: "application/json", body: JSON.stringify(body) });
        return;
      }
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
  test(`active case (${label}): login and refresh never open the deleted planner`, async ({ page }) => {
    const fixture = await installFixtures(page, { mode, intake });
    await signIn(page);
    for (const reload of [false, true]) {
      if (reload) await page.reload();
      await expect(page.locator("#settlement-planner, #settlement-generate, #settlement-ledger-json")).toHaveCount(0);
      await expect(page.locator("#case-create-dialog")).toBeHidden();
      if (mode) {
        await expect(page).toHaveURL(`${origin}/onboarding/${mode}?case_id=${caseId}`);
        await expect(page.locator("#preparation-view")).toBeVisible();
        if (mode === "upload") await expect(page.locator("#materials-file-input")).toBeEnabled();
      } else {
        await expect(page.locator("#start-path-dialog")).toBeVisible();
        await expect(page).toHaveURL(`${origin}/`);
      }
    }
    expect(fixture.requests.filter((path) => path.startsWith("POST") && path.endsWith("/wizard-attempt"))).toEqual([]);
    expect(fixture.requests.filter((path) => /settlement-planning|profile-facts|wizard-attempt/.test(path))).toEqual([]);
    fixture.verify();
  });
}

test("failed dashboard after login stays an explicit error, not a start or attempt", async ({ page }) => {
  const fixture = await installFixtures(page, { dashboardStatus: 503 });
  await signIn(page);
  await expect(page.locator("#dashboard-error")).toBeVisible();
  await expect(page.locator("#dashboard-error")).toContainText("Regression service unavailable.");
  await expect(page.locator("#case-create-dialog")).toBeHidden();
  await expect(page.locator("#settlement-planner")).toBeHidden();
  fixture.verify();
});

test("expired session does not show cached case materials on refresh", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true, mode: "upload" });
  await page.goto(origin);
  await expect(page.locator("#materials-workflow")).toBeVisible();
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
  await expect(page.getByRole("button", { name: "Save offer choice", exact: true })).toBeEnabled();
  const upload = await page.locator("#materials-import").boundingBox();
  const box = await toggle.boundingBox();
  expect(upload.y).toBeLessThan(box.y);
  fixture.verify();
});

test("documents path: checking the offer requires saved details before Continue", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, noOffer);
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  const toggle = page.getByRole("checkbox", { name: "The other party has already made an offer" });
  const next = page.getByRole("button", { name: "Save offer choice", exact: true });
  await expect(next).toBeEnabled();
  await toggle.check();
  await expect(page.locator("#existing-offer-details")).toBeVisible();
  await expect(next).toBeDisabled();
  await expect(page.locator("#existing-offer-continue-status")).toContainText("Save offer notes or an offer document before saving this choice.");
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
  await expect(page.getByRole("button", { name: "Save offer choice", exact: true })).toBeEnabled();

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

test("documents save stays on materials and never calls the removed planner", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, noOffer);
  const url = `${origin}/onboarding/upload?case_id=${caseId}`;
  await page.goto(url);
  await page.getByRole("button", { name: "Save offer choice", exact: true }).click();
  await expect(page.locator("#existing-offer-status")).toHaveText("Your offer choice is saved.");
  await expect(page).toHaveURL(url);
  await expect(page.locator("#materials-file-input")).toBeEnabled();
  expect(fixture.puts).toEqual([{ exists: false, notes: null, document_ids: [] }]);
  fixture.verify();
});

for (const success of [true, false]) {
  test(`wizard save ${success ? "success" : "failure"} stays on its preparation screen`, async ({ page }) => {
    const fixture = await installFixtures(page, {
      authenticated: true,
      mode: "wizard",
      intake: { filed: "yes", role: "petitioner", dates: {}, finances: [], issues: [], agreements: [] },
      mutationHandler: async (request) => {
        if (new URL(request.url()).pathname !== `/cases/${caseId}/wizard-intake` || request.method() !== "PUT") return null;
        const sent = request.postDataJSON();
        return success
          ? { body: { revision: sent.expected_revision + 1, draft: sent.draft } }
          : { status: 503, body: { detail: "Synthetic wizard save unavailable." } };
      },
    });
    const url = `${origin}/onboarding/wizard?case_id=${caseId}`;
    await page.goto(url);
    await expect(page.locator("#wizard-finish")).toBeEnabled();
    await page.getByRole("button", { name: "Save case information", exact: true }).click();
    await expect(page.locator("#wizard-save-status")).toContainText(success ? "Your case information is saved." : "Synthetic wizard save unavailable.");
    await expect(page).toHaveURL(url);
    expect(fixture.requests).toContain(`PUT /cases/${caseId}/wizard-intake`);
    expect(fixture.requests.filter((request) => /wizard-attempt|settlement-planning/.test(request))).toEqual([]);
    fixture.verify();
  });
}

test("Account retains active-case export, closure and deletion with explicit failure recovery", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated: true,
    mode: "upload",
    extraReads: { [`/cases/${caseId}/export`]: {} },
    mutationHandler: async (request) => {
      const path = new URL(request.url()).pathname;
      if ([`/cases/${caseId}/close`, `/cases/${caseId}/permanent-deletion`].includes(path)) {
        return { status: 503, body: { detail: "Synthetic case action unavailable." } };
      }
      return null;
    },
  });
  await page.goto(`${origin}/?view=account`);
  const actions = page.locator("#active-case-actions");
  await expect(actions).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await actions.getByRole("button", { name: "Export all case data" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe(`case-${caseId}-export.zip`);
  page.once("dialog", (dialog) => dialog.accept());
  await actions.getByRole("button", { name: "Close case", exact: true }).click();
  await expect(page.locator("#settlement-case-action-status")).toHaveText("Synthetic case action unavailable.");
  await expect(page.locator("#settlement-case-close")).toBeEnabled();
  page.once("dialog", (dialog) => dialog.accept("DELETE CASE"));
  await actions.getByRole("button", { name: "Permanently delete case", exact: true }).click();
  await expect(page.locator("#settlement-case-delete")).toBeEnabled();
  expect(fixture.requests).toContain(`POST /cases/${caseId}/close`);
  expect(fixture.requests).toContain(`DELETE /cases/${caseId}/permanent-deletion`);
  fixture.verify();
});

for (const accepted of [true, false]) {
  test(`existing completion ${accepted ? "accepted" : "unconfirmed"} is independent of the deleted planner`, async ({ page }) => {
    const selectionId = "00000000-0000-4000-8000-000000000076";
    const fixture = await installFixtures(page, {
      extraReads: {
        [`/cases/${caseId}/settlement-planning/selections/${selectionId}/offer-response`]: {
          outcome: accepted ? "accepted" : null,
          sent_confirmed: accepted,
          sent_documents_complete: accepted,
          attachments: [],
          frozen: true,
        },
      },
      mutationHandler: async (request) => {
        if (new URL(request.url()).pathname.endsWith("/offer-response/attachments/accepted_offer") && request.method() === "POST") return { body: {} };
        return null;
      },
    });
    await page.goto(`${origin}/settlement-completion?case_id=${caseId}&selection_id=${selectionId}`);
    if (accepted) {
      await expect(page.locator("#settlement-response-checklist")).toBeVisible();
      await expect(page.locator("#settlement-completion-finalize")).toBeEnabled();
      await page.locator("#settlement-response-accepted-file").setInputFiles({
        name: "synthetic-accepted-offer.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("Synthetic regression attachment"),
      });
      await expect(page.locator("#settlement-response-accepted-status")).toContainText("was securely attached");
    } else {
      await expect(page.locator("#settlement-completion-status")).toHaveText("This completion page is only available for an accepted, confirmed offer.");
      await expect(page.locator("#settlement-response-checklist")).toBeHidden();
      await expect(page.locator("#settlement-completion-finalize")).toBeDisabled();
    }
    await expect(page.locator("#settlement-planner")).toHaveCount(0);
    fixture.verify();
  });
}

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

  test(`${source}: fictional asset scenarios and completion survive planner removal`, async ({ page }) => {
    const fixture = await installFixtures(page);
    await page.goto(`${origin}/demo/start?source=${source}`);
    await page.locator("#demo-case-documents-link").click();
    const query = new URL(page.url()).search;
    await page.goto(`${origin}/demo${query}`);
    await expect(page.locator("#asset-analysis-view")).toBeVisible();
    await expect(page.locator("#settlement-scenario-results")).toBeVisible();
    await page.goto(`${origin}/demo/settlement-completion${query}`);
    await expect(page.locator("#settlement-completion-status")).toContainText("Fictional demo only");
    await expect(page.locator("#settlement-completion-finalize")).toBeEnabled();
    fixture.verify();
  });
}
