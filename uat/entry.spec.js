import { readFileSync } from "node:fs";
import { test, expect } from "@playwright/test";

const origin = "https://casework-regression.invalid";
const html = readFileSync(new URL("../src/app/static/index.html", import.meta.url), "utf8");
const caseId = "00000000-0000-4000-8000-000000000071";
const workspace = {
  case: {
    id: caseId, status: "draft", metadata_json: { case_title: "Synthetic regression case" },
    property_assets: [], relationship_milestones: {}, asset_liability_inventory: {},
  },
  intake: { finances: [], dates: {} },
  attempts: [],
  documents: [],
  asset_overview: { revision: 0, overview: { snapshots: [], milestones: [] } },
};

const missingWizardAttempt = {
  status: "needs_information",
  attempt_exists: false,
  needs: ["A separation date."],
  report: null,
};

async function installFixtures(page, { mode = null, hasCase = true, authenticated = false, dashboardStatus = 200, workspaceStarted = false, intake = {}, wizardAttempt = missingWizardAttempt, extraReads = {}, mutationHandler = null } = {}) {
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
    } else if (path === `/cases/${caseId}/workspace-entry` && request.method() === "POST") {
      workspaceStarted = true;
      body = { workspace_started: true };
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
          cases: hasCase ? [{ id: caseId, title: "Synthetic regression case", workflow_mode: mode, workspace_started: workspaceStarted }] : [],
        },
      } : { detail: status === 401 ? "Sign in required." : "Regression service unavailable." };
    } else {
      const fixtures = {
        [`/cases/${caseId}/workspace`]: { ...workspace, intake: { ...workspace.intake, ...intake } },
        "/api/auth/providers": { google: false },
        "/api/auth/account": { email: "synthetic@example.invalid", first_name: "Synthetic", last_name: "User" },
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
        [`/cases/${caseId}/onboarding-state`]: { workflow_mode: mode, has_work: false, reset_pending: false },
        [`/cases/${caseId}/wizard-attempt`]: wizardAttempt,
        ...extraReads,
      };
      if (path.startsWith("/api/v1/materials/config")) {
        body = { import_enabled: true, max_upload_bytes: 2097152, supported_extensions: [".pdf", ".docx"], max_attachments: 5, attachment_count: 0, max_pdf_pages: 200 };
        await route.fulfill({ contentType: "application/json", body: JSON.stringify(body) });
        return;
      }
      if (/\/asset-mediation\/\d+$/.test(path) && !Object.hasOwn(fixtures, path)) {
        const ordinal = Number(path.split("/").at(-1));
        body = { revision:0, attempt_ordinal:ordinal, attempt_limit:1, sent:false,
          outcome:null, notes:"", document_ids:[], sent_filenames:[], selection:null,
          downloaded_formats:[], stopped:false, completed:false, accepted_document_ids:[] };
        await route.fulfill({ contentType:"application/json", body:JSON.stringify(body) });
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
    signIn: () => { signedIn = true; },
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
  await page.locator("#entry-email").fill("synthetic@example.invalid");
  await page.locator("#email-entry-form button[type=submit]").click();
  await page.locator("#login-password").fill("synthetic-password-not-a-secret");
  await page.locator("#login-form button[type=submit]").click();
}

test("login entry shows only email-first entry and Google, without old tabs or preview copy", async ({ page }) => {
  const fixture = await installFixtures(page);
  await page.goto(`${origin}/?auth=login`);
  await expect(page.locator("#account-title")).toHaveText("Log in or sign up for free");
  await expect(page.locator("#email-entry-form")).toBeVisible();
  await expect(page.locator("#google-signin")).toBeVisible();
  await expect(page.locator("#signup-form")).toBeHidden();
  await expect(page.locator("#login-form")).toBeHidden();
  await expect(page.locator("#verify-form")).toBeHidden();
  for (const selector of [".preview-bar", ".topbar", ".theme-status", "footer"]) {
    await expect(page.locator(selector)).toBeHidden();
  }
  await expect(page.locator("#account")).toBeVisible();
  await expect(page.locator("#signup-tab, #login-tab, #verify-tab, .account-copy")).toHaveCount(0);
  await expect(page.locator("#logout-button")).toBeHidden();
  for (const width of [390, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  fixture.verify();
});

test("Google consent refusal never starts authentication, sends personal data, or links an account", async ({ page }) => {
  const fixture = await installFixtures(page, { extraReads: { "/api/auth/providers": { google: true } } });
  await page.goto(`${origin}/?auth=login`);
  await page.locator("#google-signin").click();
  await expect(page.locator("#google-consent")).toBeVisible();
  await expect(page.locator("#email-entry-form button")).toBeDisabled();
  await page.locator("#google-consent-cancel").click();
  await expect(page.locator("#google-consent")).toBeHidden();
  await expect(page.locator("#google-signin")).toBeVisible();
  await expect(page.locator("#email-entry-form button")).toBeEnabled();
  expect(fixture.requests.filter(value => value.startsWith("POST "))).toEqual([]);
  expect(page.url()).toBe(`${origin}/?auth=login`);
  fixture.verify();
});

test("Google only starts after explicit agreement", async ({ page }) => {
  const posted = [];
  const fixture = await installFixtures(page, {
    extraReads: { "/api/auth/providers": { google: true } },
    mutationHandler: async request => {
      posted.push({ path: new URL(request.url()).pathname, body: request.postDataJSON() });
      return { status: 503, body: { detail: "Synthetic provider unavailable." } };
    },
  });
  await page.goto(`${origin}/?auth=login`);
  await page.locator("#google-signin").click();
  expect(posted).toEqual([]);
  await page.locator("#google-consent-agree").click();
  await expect(page.locator("#account-status")).toHaveText("Synthetic provider unavailable.");
  expect(posted).toEqual([{ path: "/api/auth/oidc/google/start", body: { terms_accepted: true } }]);
  await expect(page.locator("#google-consent-cancel")).toBeEnabled();
  fixture.verify();
});

test("email signup requires verified five-minute token and all fields, then opens Account", async ({ page }) => {
  const posted = [];
  const fixture = await installFixtures(page, {
    mutationHandler: async request => {
      const path = new URL(request.url()).pathname;
      const body = request.postDataJSON();
      posted.push({ path, body });
      if (path === "/api/auth/signup/email/start") return { body: { challenge_id: "synthetic-challenge", expires_in: 300 } };
      if (path === "/api/auth/signup/email/verify") return body.token === "synthetic-correct-token"
        ? { body: { verification_token: "synthetic-verified-proof", expires_at: new Date(Date.now() + 300000).toISOString() } }
        : { status: 400, body: { detail: "Verification token is invalid or expired." } };
      if (path === "/api/auth/signup") return { status: 503, body: { detail: "Synthetic signup response." } };
      return null;
    },
  });
  await page.goto(`${origin}/?auth=signup`);
  await page.locator("#entry-email").fill("new@example.com");
  await page.locator("#email-entry-form button").click();
  await expect(page.locator("#signup-form")).toBeVisible();
  await expect(page.locator("#signup-email")).toHaveValue("new@example.com");
  await page.locator("#signup-first-name").fill("Synthetic");
  await page.locator("#signup-last-name").fill("User");
  await page.locator("#signup-password").fill("synthetic-password-not-a-secret");
  await expect(page.locator("#signup-submit")).toBeDisabled();
  await page.locator("#signup-verify-email").click();
  await expect(page.locator("#signup-verification")).toContainText("expires in 5 minutes");
  await page.locator("#signup-token").fill("wrong-token");
  await page.locator("#signup-confirm-token").click();
  await expect(page.locator("#account-status")).toContainText("invalid or expired");
  await expect(page.locator("#signup-submit")).toBeDisabled();
  await page.locator("#signup-token").fill("synthetic-correct-token");
  await page.locator("#signup-confirm-token").click();
  await expect(page.locator("#signup-submit")).toBeEnabled();
  await page.locator("#signup-first-name").fill("  ");
  await expect(page.locator("#signup-submit")).toBeDisabled();
  await page.locator("#signup-first-name").fill("Synthetic");
  await page.locator("#signup-submit").click();
  await expect(page.locator("#account-status")).toHaveText("Synthetic signup response.");
  expect(posted.at(-1)).toEqual({ path: "/api/auth/signup", body: {
    email: "new@example.com", first_name: "Synthetic", last_name: "User",
    password: "synthetic-password-not-a-secret", challenge_id: "synthetic-challenge",
    verification_token: "synthetic-verified-proof", terms_accepted: true,
  } });
  await page.route("**/api/auth/signup", async route => {
    fixture.signIn();
    await route.fulfill({ contentType:"application/json", body:JSON.stringify({ session_id:"synthetic" }) });
  });
  await page.locator("#signup-submit").click();
  await expect(page).toHaveURL(`${origin}/?view=account`);
  await expect(page.locator("#account-tools")).toBeVisible();
  fixture.verify();
});

test("changing verified email or waiting past expiry disables signup again", async ({ page }) => {
  const fixture = await installFixtures(page, {
    mutationHandler: async request => {
      const path = new URL(request.url()).pathname;
      if (path.endsWith("/start")) return { body: { challenge_id: "synthetic-challenge", expires_in: 300 } };
      if (path.endsWith("/verify")) return { body: { verification_token: "synthetic-proof", expires_at: new Date(Date.now() + 300000).toISOString() } };
      return null;
    },
  });
  await page.clock.install();
  await page.goto(`${origin}/?auth=signup`);
  await page.locator("#entry-email").fill("new@example.com");
  await page.locator("#email-entry-form button").click();
  await page.locator("#signup-first-name").fill("Test");
  await page.locator("#signup-last-name").fill("User");
  await page.locator("#signup-password").fill("synthetic-password-not-a-secret");
  const verify = async () => {
    await page.locator("#signup-verify-email").click();
    await page.locator("#signup-token").fill("synthetic-correct-token");
    await page.locator("#signup-confirm-token").click();
    await expect(page.locator("#signup-submit")).toBeEnabled();
  };
  await verify();
  await page.locator("#signup-email").fill("changed@example.com");
  await expect(page.locator("#signup-submit")).toBeDisabled();
  await verify();
  await page.clock.fastForward(300001);
  await expect(page.locator("#signup-submit")).toBeDisabled();
  await expect(page.locator("#signup-verification-status")).toContainText("expired");
  fixture.verify();
});

test("top navigation logout revokes session with CSRF and returns to signed-out home", async ({ page }) => {
  let fixture;
  const posted = [];
  fixture = await installFixtures(page, {
    authenticated: true,
    mutationHandler: async request => {
      if (new URL(request.url()).pathname !== "/api/auth/logout") return null;
      posted.push(request.headers()["x-csrf-token"]);
      fixture.signOut();
      return { status: 204, body: "" };
    },
  });
  await page.context().addCookies([{ name:"auth_csrf", value:"synthetic-csrf", url:origin }]);
  await page.goto(`${origin}/?view=home`);
  await expect(page.locator("#account-tools-link")).toBeVisible();
  await expect(page.locator("#logout-button")).toBeVisible();
  await expect(page.locator("#login-entry")).toBeHidden();
  await page.locator("#logout-button").click();
  await expect(page).toHaveURL(`${origin}/`);
  await expect(page.locator("#login-entry")).toBeVisible();
  await expect(page.locator("#logout-button")).toBeHidden();
  expect(posted).toEqual(["synthetic-csrf"]);
  fixture.verify();
});

test("Account shows the signed-in email and names and labels paid entitlement Essential", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated: true,
    extraReads: {
      "/api/auth/account": { email: "essential@example.invalid", first_name: "Essential", last_name: "Tester" },
      "/api/billing/account/entitlement": { status: "paid" },
    },
  });
  await page.goto(`${origin}/?view=account`);
  await expect(page.locator("#account-profile")).toBeVisible();
  await expect(page.locator("#account-profile-email")).toHaveText("essential@example.invalid");
  await expect(page.locator("#account-profile-first-name")).toHaveText("Essential");
  await expect(page.locator("#account-profile-last-name")).toHaveText("Tester");
  await expect(page.locator("#plan-name")).toHaveText("Essential plan");
  await expect(page.locator("#plan-name")).not.toHaveText("Free plan");
  fixture.verify();
});

for (const path of [
  `/settlement-completion?case_id=${caseId}&asset_attempt=1`,
  `/rejection-completion?case_id=${caseId}`,
  `/case/assets?case_id=${caseId}`, `/case/files?case_id=${caseId}`,
  `/onboarding/upload?case_id=${caseId}`, `/onboarding/wizard?case_id=${caseId}`,
]) {
  test(`anonymous direct working URL returns to bare home: ${path.split("?")[0]}`, async ({ page }) => {
    const fixture = await installFixtures(page);
    await page.goto(`${origin}${path}`);
    await expect(page).toHaveURL(`${origin}/`);
    await expect(page.locator(".hero")).toBeVisible();
    expect(fixture.requests.filter(request => request.startsWith("GET /cases/"))).toEqual([]);
    await expect(page.locator("#settlement-completion-page")).toBeHidden();
    await expect(page.locator("#rejection-completion-page")).toBeHidden();
    await fixture.verify();
  });
}

test("restored working page rechecks a signed-out session before showing its saved content", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated:true, extraReads:{
    [`/cases/${caseId}/asset-mediation/1`]:{ revision:1, attempt_ordinal:1, sent:true, outcome:"accepted", completed:false },
  } });
  await page.goto(`${origin}/settlement-completion?case_id=${caseId}&asset_attempt=1`);
  await expect(page.locator("#settlement-completion-demo-content")).toBeVisible();
  fixture.signOut();
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted:true })));
  await expect(page).toHaveURL(`${origin}/`);
  await expect(page.locator(".hero")).toBeVisible();
  await fixture.verify();
});

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
    await expect(page.locator("#case-create-page")).toBeVisible();
    await expect(page.locator("#case-start-upload")).toBeVisible();
    await expect(page.locator("#case-start-wizard")).toBeVisible();
    await expect(page.locator("#case-create-page")).toHaveJSProperty("tagName", "SECTION");
    await expect(page.getByRole("heading", { name: "Choose your starting point", exact: true })).toBeVisible();
    await expect(page.locator("#case-create-cancel, #case-create-dialog")).toHaveCount(0);
    expect(await page.locator("dialog:modal").count()).toBe(0);
    await expect(page.locator("#settlement-planner")).toBeHidden();
    await expectNoDetour(page);
  }
  fixture.verify();
});

test("starting-point page uses the document heading style without inner or outer cards", async ({ page }) => {
  const fixture = await installFixtures(page, { hasCase: false, authenticated: true });
  for (const width of [1280, 480]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(`${origin}/demo/documents?source=demo1`);
    const heading = await page.locator("#documents-demo h1").evaluate(element => {
      const style = getComputedStyle(element);
      return [style.fontSize, style.lineHeight, style.fontFamily];
    });
    await page.goto(origin);
    await expect(page.locator("#case-create-page")).toBeVisible();
    expect(await page.locator("#case-create-title").evaluate(element => {
      const style = getComputedStyle(element);
      return [style.fontSize, style.lineHeight, style.fontFamily];
    })).toEqual(heading);
    for (const selector of ["#case-create-page", "#account-dashboard .dashboard-panel"]) {
      const style = await page.locator(selector).evaluate(element => {
        const computed = getComputedStyle(element);
        return [computed.borderTopWidth, computed.backgroundColor, computed.boxShadow];
      });
      expect(style).toEqual(["0px", "rgba(0, 0, 0, 0)", "none"]);
    }
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
      await expect(page.locator("#case-create-page")).toBeHidden();
      if (mode) {
        await expect(page).toHaveURL(`${origin}/onboarding/${mode}?case_id=${caseId}`);
        await expect(page.locator(mode === "upload" ? "#case-documents-layout" : "#preparation-view")).toBeVisible();
        if (mode === "upload") await expect(page.locator("#demo-file-input-case")).toBeEnabled();
      } else {
        await expect(page.locator("#start-path-page")).toBeVisible();
        await expect(page.locator("#start-path-page")).toHaveJSProperty("tagName", "SECTION");
        await expect(page.locator("#start-path-cancel")).toHaveCount(0);
        expect(await page.locator("dialog:modal").count()).toBe(0);
        await page.reload();
        await expect(page.locator("#start-path-page")).toBeVisible();
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
  await expect(page.locator("#case-create-page")).toBeHidden();
  await expect(page.locator("#settlement-planner")).toBeHidden();
  fixture.verify();
});

test("expired session does not show cached case materials on refresh", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true, mode: "upload" });
  await page.goto(origin);
  await expect(page.locator("#case-documents-layout")).toBeVisible();
  await expect(page.locator("#account-dashboard")).toBeHidden();
  fixture.signOut();
  await page.reload();
  await expect(page.locator("#account-dashboard")).toBeHidden();
  await expect(page.locator("#login-entry")).toBeVisible();
  await page.locator("#login-entry").click();
  await expect(page.locator("#email-entry-form")).toBeVisible();
  await expect(page.locator("#login-form")).toBeHidden();
  await expect(page.locator("#case-create-page")).toBeHidden();
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
        [`/cases/${caseId}/workspace`]: workspace,
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
  await expect(page.locator("#case-title-input")).toHaveCount(0);
  await page.getByRole("button", { name: "I have documents" }).click();
  await expect(page).toHaveURL(`${origin}/onboarding/upload?case_id=${caseId}`);
  await expect(page.getByRole("heading", { name: "I have all documents", exact: true })).toBeVisible();
  await expect(page.locator("#demo-file-input-case")).toBeEnabled();
  await expect(page.locator("#case-create-page")).toBeHidden();
  await expect(page.getByRole("button", { name: "Create case and continue to documents", includeHidden: true })).toHaveCount(0);
  await expect(page.locator("#existing-offer-toggle")).toHaveCount(0);
  expect(fixture.creations).toEqual([{ workflow_mode: "upload" }]);
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
  await expect(page.locator("#case-create-cancel")).toHaveCount(0);
  await expect(page.locator("#case-create-offer-intake")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(page.locator("#case-create-page")).toBeVisible();
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
  await expect(page.locator("#case-create-offer-intake")).toHaveCount(0);
  await expect(page.locator("#case-start-upload")).toBeEnabled();
  await expect(page.locator("#case-start-wizard")).toBeEnabled();
  await expect(page.locator("#case-create-cancel")).toHaveCount(0);
  await page.locator("#case-start-upload").click();
  await expect(page).toHaveURL(`${origin}/onboarding/upload?case_id=${caseId}`);
  await expect(page.getByRole("heading", { name: "I have all documents", exact: true })).toBeVisible();
  expect(fixture.creations).toEqual([
    { workflow_mode: "upload" },
    { workflow_mode: "upload" },
  ]);
  expect(fixture.puts).toEqual([]);
  fixture.verify();
});

test("wizard start: one click creates the case and shows the wizard without an offer answer", async ({ page }) => {
  const creations = [];
  const fixture = await installFixtures(page, {
    hasCase: false,
    authenticated: true,
    extraReads: { [`/cases/${caseId}/existing-offer`]: noOffer },
    mutationHandler: async (request) => {
      if (new URL(request.url()).pathname !== "/cases") return null;
      creations.push(request.postDataJSON());
      return { body: { id: caseId } };
    },
  });
  await page.goto(origin);
  await page.locator("#case-start-wizard").click();
  await expect(page).toHaveURL(`${origin}/onboarding/wizard?case_id=${caseId}`);
  await expect(page.locator("#wizard-demo")).toBeVisible();
  await expect(page.locator("#wizard-filed-question")).toBeVisible();
  await expect(page.locator("#account-dashboard")).toBeHidden();
  await expect(page.locator("#demo-case-navigation")).toBeHidden();
  await expect(page.locator("#preparation-eyebrow, #preparation-title, #preparation-description, #preparation-note")).toHaveCount(0);
  expect(fixture.requests.filter(request => request.endsWith("/workspace"))).toEqual([]);
  const wizardBounds = await page.locator("#wizard-demo").boundingBox();
  const offerBounds = await page.locator("#existing-offer-panel").boundingBox();
  expect(wizardBounds.y).toBeLessThan(offerBounds.y);
  await expect(page.locator("#case-create-offer-intake, #case-offer-question")).toHaveCount(0);
  expect(creations).toEqual([{ workflow_mode: "wizard" }]);
  await page.reload();
  await expect(page.locator("#wizard-demo")).toBeVisible();
  fixture.verify();
});

test("wizard start: pending creation blocks switching and failure is retryable", async ({ page }) => {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  const creations = [];
  const fixture = await installFixtures(page, {
    hasCase: false,
    authenticated: true,
    extraReads: { [`/cases/${caseId}/existing-offer`]: noOffer },
    mutationHandler: async (request) => {
      if (new URL(request.url()).pathname !== "/cases") return null;
      creations.push(request.postDataJSON());
      if (creations.length === 1) {
        await gate;
        return { status: 503, body: { detail: "Case creation unavailable. Please retry." } };
      }
      return { body: { id: caseId } };
    },
  });
  await page.goto(origin);
  await page.locator("#case-start-wizard").click();
  await expect(page.locator("#case-start-upload")).toBeDisabled();
  await expect(page.locator("#case-start-wizard")).toBeDisabled();
  await expect(page.locator("#case-create-cancel")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(page.locator("#case-create-page")).toBeVisible();
  expect(creations).toHaveLength(1);
  release();
  await expect(page.locator("#case-create-status")).toHaveText("Case creation unavailable. Please retry.");
  await expect(page.locator("#case-start-wizard")).toBeEnabled();
  await expect(page.locator("#case-start-upload")).toBeEnabled();
  await expect(page.locator("#case-create-cancel")).toHaveCount(0);
  await page.locator("#case-start-wizard").click();
  await expect(page).toHaveURL(`${origin}/onboarding/wizard?case_id=${caseId}`);
  await expect(page.locator("#wizard-filed-question")).toBeVisible();
  expect(creations).toEqual([{ workflow_mode: "wizard" }, { workflow_mode: "wizard" }]);
  fixture.verify();
});

test("real case navigation uses saved assets and files, never fictional demo figures", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "wizard",
    extraReads: {
      [`/cases/${caseId}/workspace`]: {
        ...workspace,
        case: {
          ...workspace.case,
          property_assets: [{ name: "<Saved property>", title_status: "individual", acquisition_date: "2019-02-03" }],
          asset_liability_inventory: { loans: { car: 7500 } },
        },
        intake: {
          dates: { marriage: { date: "2020-04-05" } },
          finances: [
            { kind: "asset", description: "Saved retirement balance", amount: "1234.56", owners: "User" },
            { kind: "debt", description: "Unknown loan", amount: null },
          ],
        },
        documents: [{ id: caseId, extension: "pdf", size_bytes: 1024, created_at: "2026-01-01T00:00:00Z" }],
      },
    },
  });
  await page.goto(`${origin}/onboarding/wizard?case_id=${caseId}`);
  await expect(page.getByRole("navigation", { name: "Case navigation", exact: true })).toBeHidden();
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.getByRole("navigation", { name: "Case navigation", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "1st Attempt, current", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "1st Attempt, current", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "2nd Attempt, future", exact: true })).toHaveCount(0);
  await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.locator("#case-assets-view")).toBeVisible();
  await expect(page.locator("#asset-table-rows-case")).toContainText("Unavailable");
  await expect(page.locator("#case-assets-rows, #case-assets-context, #case-information-link")).toHaveCount(0);
  await expect(page.locator("#case-assets-view")).not.toContainText("$1,234.56");
  await expect(page.locator("#demo-attempt-progress-status")).toHaveText("1st Attempt is current.");
  await expect(page.locator("#asset-analysis-view")).toBeHidden();
  await expect(page.getByRole("link", { name: "Asset Overview", exact: true })).toHaveAttribute("aria-current", "page");
  await page.reload();
  await expect(page.locator("#asset-table-rows-case")).toContainText("Unavailable");
  await page.getByRole("link", { name: "Case file management", exact: true }).click();
  await expect(page).toHaveURL(`${origin}/case/files?case_id=${caseId}`);
  await expect(page.getByRole("heading", { name: "Case file management", exact: true })).toBeVisible();
  await expect(page.locator("#case-saved-files-list")).toContainText("PDF");
  await expect(page.locator("#case-saved-files-list a")).toHaveAttribute("href", `/documents/${caseId}/download`);
  await expect(page.locator("#case-file-layout input[type=file]").first()).toBeEnabled();
  await expect(page.locator("#demo-file-manager")).toBeHidden();
  fixture.verify();
});

test("documents entry reuses the demo selection panel and never mounts the removed upload screen", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true, mode: "upload" });
  const structure = async selector => page.locator(selector).evaluate(panel =>
    [...panel.querySelectorAll("*")].filter(element =>
      !element.closest("#existing-offer-panel, .case-counteroffer-choice, #case-counteroffer-status, #case-counteroffer-retry"))
      .map(element => [element.tagName, element.className]));
  await page.goto(`${origin}/demo/documents?source=demo1`);
  const demo = await structure("#documents-demo .demo-flow-panel");
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await expect(page.locator("#case-documents-layout")).toBeVisible();
  const actual = await structure("#case-documents-layout .demo-flow-panel");
  expect(actual.filter(([tag, className]) => className !== "demo-flow-actions" && !className.includes("button"))).toEqual(
    demo.filter(([tag, className]) => className !== "demo-flow-actions" && !className.includes("button")));
  await expect(page.getByRole("heading", { name: "Select documents", exact: true })).toBeVisible();
  await expect(page.locator("#demo-files-next-case")).toBeDisabled();
  await expect(page.locator("#demo-documents-back-case")).toHaveText("Back");
  await expect(page.locator("#demo-documents-back-case")).toHaveJSProperty("tagName", "BUTTON");
  const actions = page.locator("#case-documents-layout .demo-flow-actions button");
  await expect(actions.nth(0)).toHaveText("Back");
  await expect(actions.nth(1)).toHaveText("Next →");
  expect(await page.locator("#demo-files-next-case").evaluate(button => getComputedStyle(button).cursor)).toBe("pointer");
  await expect(page.locator("#materials-workflow, #analysis-controls, #existing-offer-toggle, #materials-back")).toHaveCount(0);
  await expect(page.locator("#demo-case-navigation")).toBeHidden();
  await expect(page.locator("#case-attempt-banner, #settlement-demo-attempt-status")).toHaveCount(0);
  for (const width of [1280, 800, 480, 350]) {
    await page.setViewportSize({ width, height: 900 });
    const box = await page.locator("#case-documents-layout .demo-flow-panel").boundingBox();
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(width);
  }
  fixture.verify();
});

test("documents counteroffer checkbox reveals text and file input only when checked and preserves unsaved notes", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, noOffer);
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  const toggle = page.locator("#case-counteroffer-toggle");
  await expect(toggle).toBeEnabled();
  await expect(toggle).not.toBeChecked();
  await expect(page.locator("#existing-offer-panel")).toBeHidden();
  await expect(page.locator("#existing-offer-save")).toHaveCount(0);
  await toggle.check();
  await expect(page.locator("#existing-offer-notes")).toBeVisible();
  await expect(page.locator("#existing-offer-file")).toBeVisible();
  await expect(page.locator("#existing-offer-save")).toHaveCount(0);
  const heading = await page.locator("#case-documents-layout h1").boundingBox();
  const checkbox = await toggle.boundingBox();
  const files = await page.locator("#case-documents-layout .demo-flow-panel").boundingBox();
  expect(checkbox.y).toBeGreaterThan(heading.y + heading.height);
  const selection = await page.locator("#demo-file-input-case").boundingBox();
  expect(checkbox.y).toBeGreaterThan(selection.y + selection.height);
  expect(checkbox.y).toBeLessThan(files.y + files.height);
  await page.locator("#existing-offer-notes").fill("Synthetic counteroffer notes");
  await toggle.uncheck();
  await expect(page.locator("#existing-offer-panel")).toBeHidden();
  await toggle.check();
  await expect(page.locator("#existing-offer-notes")).toHaveValue("Synthetic counteroffer notes");
  fixture.verify();
});

test("documents Back returns to the existing case mode selection and never creates or deletes a case", async ({ page }) => {
  const changes = [];
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "upload",
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.endsWith("/workflow-mode")) return null;
      changes.push(request.postDataJSON());
      return { body: workspace.case };
    },
  });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await expect(page).toHaveURL(`${origin}/?start_path=1`);
  await expect(page.locator("#start-path-page")).toBeVisible();
  await expect(page.locator("#start-path-page")).toHaveJSProperty("tagName", "SECTION");
  await expect(page.locator("#start-path-cancel")).toHaveCount(0);
  expect(await page.locator("dialog:modal").count()).toBe(0);
  await page.reload();
  await expect(page.locator("#start-path-page")).toBeVisible();
  await page.locator('#start-path-page [data-path-mode="wizard"]').click();
  await expect(page).toHaveURL(`${origin}/onboarding/wizard?case_id=${caseId}`);
  expect(changes).toEqual([{ workflow_mode: "wizard" }]);
  expect(fixture.requests.filter(request => request === "POST /cases" || request.startsWith("DELETE"))).toEqual([]);
  fixture.verify();
});

  for (const initialMode of ["upload", "wizard"]) {
    test(`${initialMode}: history return resumes work, No preserves it and Yes discards before switching modes`, async ({ page }) => {
      const state = { workflow_mode: initialMode, has_work: false, reset_pending: false };
      const intake = { revision: 1, draft: {} };
      let resets = 0;
      let offer = { exists: false, notes: null, document_ids: [], documents: [], assets: [], asset_terms: [] };
      const fixture = await installFixtures(page, {
        authenticated: true, mode: initialMode,
        extraReads: {
          [`/cases/${caseId}/onboarding-state`]: state,
          [`/cases/${caseId}/wizard-intake`]: intake,
        },
        mutationHandler: async request => {
          const path = new URL(request.url()).pathname;
          const data = request.postDataJSON();
          if (path.endsWith("/wizard-intake")) {
            intake.revision = data.expected_revision + 1;
            intake.draft = data.draft;
            state.has_work = true;
            return { body: intake };
          }
          if (path.endsWith("/existing-offer")) {
            offer = { ...offer, ...data };
            state.has_work = true;
            return { body: offer };
          }
          if (path.endsWith("/onboarding-reset")) {
            resets += 1;
            expect(data.confirmation).toBe("DISCARD ONBOARDING");
            state.workflow_mode = data.workflow_mode;
            state.has_work = false;
            intake.revision += 1;
            intake.draft = {};
            offer = { ...offer, exists: false, notes: null, document_ids: [] };
            return { body: state };
          }
          return null;
        },
      });
      await page.route(`**/cases/${caseId}/existing-offer`, async route => {
        if (route.request().method() !== "GET") return route.fallback();
        await route.fulfill({ contentType: "application/json", body: JSON.stringify(offer) });
      });
      await page.goto(`${origin}/?start_path=1`);
      const workingButton = page.locator(`[data-path-mode="${initialMode}"]`);
      const otherMode = initialMode === "upload" ? "wizard" : "upload";
      const otherButton = page.locator(`[data-path-mode="${otherMode}"]`);
      await workingButton.click();
      if (initialMode === "upload") {
        await page.locator("#demo-file-input-case").setInputFiles(
          { name: "keep.pdf", mimeType: "application/pdf", buffer: Buffer.from("Synthetic local file") });
        await page.locator("#case-counteroffer-toggle").check();
        await page.locator("#existing-offer-notes").fill("Keep my offer draft");
        await expect(page.locator("#existing-offer-status")).toHaveText("Offer details saved.");
      } else {
        await expect(page.locator("#wizard-back")).toBeVisible();
        await expect(page.locator("#demo-back-to-account, #demo-wizard-back")).toHaveCount(0);
        const bounds = await page.locator("#wizard-back").boundingBox();
        expect(bounds.x).toBeLessThan((await page.locator("#wizard-finish").boundingBox()).x);
        await page.locator('[name="wizard-filed"][value="yes"]').check();
        await page.locator('[name="wizard-role"][value="petitioner"]').check();
        await page.locator("#wizard-date-marriage").fill("2020-01-01");
        await expect(page.locator("#wizard-save-status")).toContainText("Saved to your case");
      }
      await page.goBack();
      await expect(page.locator("#start-path-page")).toBeVisible();
      await expect(workingButton).toBeEnabled();
      await expect(workingButton).toContainText("* You have work in progress");
      await workingButton.evaluate(button => { button.disabled = true; });
      await page.evaluate(() => {
        const event = new Event("pageshow");
        Object.defineProperty(event, "persisted", { value: true });
        window.dispatchEvent(event);
      });
      await expect(workingButton).toBeEnabled();
      await otherButton.click();
      await expect(page.locator("#mode-discard-dialog")).toBeVisible();
      await expect(page.locator("#mode-discard-description")).toContainText(initialMode === "upload" ? "I have all documents" : "Guide me step by step");
      await page.locator("#mode-discard-no").click();
      expect(resets).toBe(0);
      await expect(workingButton).toBeEnabled();
      await workingButton.click();
      if (initialMode === "upload") {
        await expect(page.locator("#demo-file-list-case")).toContainText("keep.pdf");
        await expect(page.locator("#existing-offer-notes")).toHaveValue("Keep my offer draft");
        await page.locator("#demo-documents-back-case").click();
      } else {
        await expect(page.locator("#wizard-date-marriage")).toHaveValue("2020-01-01");
        await page.locator("#wizard-back").click();
      }
      await expect(workingButton).toBeEnabled();
      await otherButton.click();
      await page.locator("#mode-discard-yes").click();
      await expect(page).toHaveURL(`${origin}/onboarding/${otherMode}?case_id=${caseId}`);
      expect(resets).toBe(1);
      if (otherMode === "upload") {
        await expect(page.locator("#demo-file-list-case li")).toHaveCount(0);
        await expect(page.locator("#case-counteroffer-toggle")).not.toBeChecked();
      } else {
        await expect(page.locator("#wizard-date-marriage")).toHaveValue("");
        await expect(page.locator('[name="wizard-filed"][value="yes"]')).not.toBeChecked();
      }
      fixture.verify();
    });
  }
test("mouse Back preserves a just-edited wizard date before its debounce saves", async ({ page }) => {
  const intake = { revision: 1, draft: { filed: "yes", role: "petitioner", dates: {} } };
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "wizard",
    extraReads: { [`/cases/${caseId}/wizard-intake`]: intake },
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.endsWith("/wizard-intake")) return null;
      const data = request.postDataJSON();
      intake.revision = data.expected_revision + 1;
      intake.draft = data.draft;
      return { body: intake };
    },
  });
  await page.goto(`${origin}/?start_path=1`);
  await page.locator('[data-path-mode="wizard"]').click();
  await expect(page.locator("#wizard-save-status")).toContainText("Restored");
  await page.locator("#wizard-date-marriage").evaluate(input => {
    input.value = "2021-02-03";
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await page.goBack();
  await expect(page.locator('[data-path-mode="wizard"]')).toBeEnabled();
  await page.locator('[data-path-mode="wizard"]').click();
  await expect(page.locator("#wizard-date-marriage")).toHaveValue("2021-02-03");
  await expect(page.locator("#wizard-save-status")).toContainText("Saved to your case");
  fixture.verify();
});

test("Next refuses to navigate or upload while a checked counteroffer has invalid or unsaved details", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "upload",
    mutationHandler: async request => {
      if (new URL(request.url()).pathname.endsWith("/existing-offer")) {
        return { status: 503, body: { detail: "Synthetic offer write failed." } };
      }
      return null;
    },
  });
  const url = `${origin}/onboarding/upload?case_id=${caseId}`;
  await page.goto(url);
  await expect(page.locator("#case-counteroffer-toggle")).toBeEnabled();
  await page.locator("#case-counteroffer-toggle").check();
  await page.locator("#demo-file-input-case").setInputFiles({
    name: "synthetic.pdf", mimeType: "application/pdf", buffer: Buffer.from("Synthetic selection"),
  });
  await page.locator("#demo-files-next-case").click();
  await expect(page.locator("#existing-offer-status")).toHaveText("Add notes about the offer or provide an offer document.");
  await expect(page).toHaveURL(url);
  await page.locator("#existing-offer-notes").fill("Synthetic counteroffer draft");
  await page.locator("#demo-files-next-case").click();
  await expect(page.locator("#existing-offer-status")).toHaveText("Synthetic offer write failed.");
  await expect(page.locator("#existing-offer-notes")).toHaveValue("Synthetic counteroffer draft");
  await expect(page).toHaveURL(url);
  expect(fixture.requests.filter(request => request.startsWith("POST"))).toEqual([]);
  fixture.verify();
});

test("documents counteroffer text saves, reloads and confirms removal without deleting uploaded files", async ({ page }) => {
  const fixture = await installDocumentsFixtures(page, noOffer);
  const url = `${origin}/onboarding/upload?case_id=${caseId}`;
  await page.goto(url);
  const toggle = page.locator("#case-counteroffer-toggle");
  await expect(toggle).toBeEnabled();
  await toggle.check();
  await page.locator("#existing-offer-notes").dispatchEvent("input");
  await expect(page.locator("#existing-offer-status")).toHaveText("Enter offer text or attach a file to save automatically.");
  expect(fixture.puts).toHaveLength(0);
  await page.locator("#existing-offer-notes").fill("Synthetic opposing offer");
  await page.locator("#existing-offer-notes").dispatchEvent("input");
  await expect(page.locator("#existing-offer-status")).toHaveText("Offer details saved.");
  expect(fixture.puts).toEqual([{ exists: true, notes: "Synthetic opposing offer", document_ids: [], expected_workflow_mode: "upload" }]);
  await page.reload();
  await expect(toggle).toBeChecked();
  await expect(page.locator("#existing-offer-notes")).toHaveValue("Synthetic opposing offer");
  page.once("dialog", dialog => dialog.dismiss());
  await toggle.click();
  await expect(toggle).toBeChecked();
  await expect(page.locator("#existing-offer-panel")).toBeVisible();
  page.once("dialog", dialog => dialog.accept());
  await toggle.uncheck();
  await expect(page.locator("#existing-offer-panel")).toBeHidden();
  expect(fixture.puts.at(-1)).toEqual({ exists: false, notes: null, document_ids: [], expected_workflow_mode: "upload" });
  await page.reload();
  await expect(toggle).not.toBeChecked();
  fixture.verify();
});

test("offer autosave preserves newer typing during a delayed request without a save button", async ({ page }) => {
  let release;
  const pending = new Promise(resolve => { release = resolve; });
  const writes = [];
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "upload",
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.endsWith("/existing-offer")) return null;
      const data = request.postDataJSON();
      writes.push(data);
      if (writes.length === 1) await pending;
      return { body: { ...data, documents: [], assets: [], asset_terms: [] } };
    },
  });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await page.locator("#case-counteroffer-toggle").check();
  const notes = page.locator("#existing-offer-notes");
  await notes.fill("First draft");
  await expect.poll(() => writes.length).toBe(1);
  await expect(notes).toBeEnabled();
  await notes.fill("Latest edited draft");
  release();
  await expect(notes).toHaveValue("Latest edited draft");
  await expect.poll(() => writes.at(-1)?.notes).toBe("Latest edited draft");
  await expect(page.locator("#existing-offer-status")).toHaveText("Offer details saved.");
  await expect(page.locator("#existing-offer-save")).toHaveCount(0);
  fixture.verify();
});

test("incomplete mode discard blocks old-mode resume and retries the confirmed target", async ({ page }) => {
  const state = { workflow_mode: "upload", has_work: true, reset_pending: false, reset_target: null };
  let resets = 0;
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "upload",
    extraReads: { [`/cases/${caseId}/onboarding-state`]: state },
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.endsWith("/onboarding-reset")) return null;
      resets += 1;
      state.reset_pending = resets === 1;
      state.reset_target = resets === 1 ? "wizard" : null;
      return resets === 1
        ? { status: 503, body: { detail: "Material deletion is incomplete. Please retry to finish cleanup." } }
        : { body: { workflow_mode: "wizard", has_work: false, reset_pending: false } };
    },
  });
  await page.goto(`${origin}/?start_path=1`);
  const wizard = page.locator('[data-path-mode="wizard"]');
  await wizard.click();
  await page.locator("#mode-discard-yes").click();
  await expect(page.locator("#start-path-status")).toContainText("Material deletion is incomplete.");
  await expect(page.locator('[data-path-mode="upload"]')).toBeDisabled();
  await page.reload();
  await expect(page.locator('[data-path-mode="upload"]')).toBeDisabled();
  await wizard.click();
  await page.locator("#mode-discard-yes").click();
  await expect(page).toHaveURL(`${origin}/onboarding/wizard?case_id=${caseId}`);
  expect(resets).toBe(2);
  fixture.verify();
});

test("documents counteroffer accepts a file without notes and failure keeps a retryable draft", async ({ page }) => {
  const state = { ...noOffer };
  let puts = 0;
  let uploads = 0;
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "upload",
    extraReads: { [`/cases/${caseId}/existing-offer`]: state },
    mutationHandler: async request => {
      const path = new URL(request.url()).pathname;
      if (path.startsWith("/api/v1/materials/imports/")) {
        uploads++;
        return { status: 201, body: { document: { id: caseId } } };
      }
      if (path === `/cases/${caseId}/existing-offer`) {
        puts++;
        if (puts === 1) return { status: 503, body: { detail: "Synthetic offer save unavailable." } };
        Object.assign(state, request.postDataJSON());
        return { body: state };
      }
      return null;
    },
  });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  const toggle = page.locator("#case-counteroffer-toggle");
  await expect(toggle).toBeEnabled();
  await toggle.check();
  await page.locator("#existing-offer-file").setInputFiles({
    name: "synthetic-offer.pdf", mimeType: "application/pdf", buffer: Buffer.from("Synthetic offer"),
  });
  await page.locator("#existing-offer-file").dispatchEvent("change");
  await expect(page.locator("#existing-offer-status")).toHaveText("Synthetic offer save unavailable.");
  await expect(toggle).toBeChecked();
  await expect(page.locator("#existing-offer-save")).toHaveCount(0);
  await page.locator("#existing-offer-file").dispatchEvent("change");
  await expect(page.locator("#existing-offer-status")).toHaveText("Offer details saved.");
  expect(uploads).toBe(1);
  expect(state.document_ids).toEqual([caseId]);
  expect(state.notes).toBeNull();
  fixture.verify();
});

test("documents offer-load failure remains visible while panel is hidden and blocks Next until retry", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true, mode: "upload" });
  let reads = 0;
  await page.route(`**/cases/${caseId}/existing-offer`, route => {
    reads++;
    return route.fulfill({
      status: reads === 1 ? 503 : 200, contentType: "application/json",
      body: JSON.stringify(reads === 1 ? { detail: "Synthetic offer load failed." } : noOffer),
    });
  });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await expect(page.locator("#case-counteroffer-status")).toHaveText("Synthetic offer load failed.");
  await expect(page.locator("#case-counteroffer-toggle")).toBeDisabled();
  await page.locator("#demo-file-input-case").setInputFiles({
    name: "synthetic.pdf", mimeType: "application/pdf", buffer: Buffer.from("Synthetic selection"),
  });
  await expect(page.locator("#demo-files-next-case")).toBeDisabled();
  await page.locator("#case-counteroffer-retry").click();
  await expect(page.locator("#case-counteroffer-toggle")).toBeEnabled();
  await expect(page.locator("#demo-files-next-case")).toBeEnabled();
  fixture.verify();
});

test("document selection stays local until Next, supports removal, then imports to the existing case", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "upload",
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.startsWith("/api/v1/materials/imports/")) return null;
      expect(request.method()).toBe("POST");
      expect(request.postData()).toContain(caseId);
      return { status: 201, body: { document: { id: caseId }, case_id: caseId, status: "success" } };
    },
  });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await page.locator("#demo-file-input-case").setInputFiles([
    { name: "synthetic.pdf", mimeType: "application/pdf", buffer: Buffer.from("Synthetic file") },
    { name: "remove.docx", mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document", buffer: Buffer.from("Synthetic file") },
  ]);
  await expect(page.locator("#demo-file-list-case li")).toHaveCount(2);
  await page.locator("#demo-file-list-case li").last().getByRole("button", { name: "Remove" }).click();
  await expect(page.locator("#demo-file-list-case li")).toHaveCount(1);
  expect(fixture.requests.filter(request => request.startsWith("POST"))).toEqual([]);
  await page.locator("#demo-files-next-case").click();
  await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
  expect(fixture.requests.filter(request => request.startsWith("POST"))).toHaveLength(2);
  expect(fixture.requests.filter(request => /analysis|profile-facts/.test(request))).toEqual([]);
  await page.getByRole("link", { name: "Casework home", exact: true }).click();
  await expect(page).toHaveURL(`${origin}/?view=home`);
  await page.locator("#account-entry").click();
  await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.locator("#case-assets-view")).toBeVisible();
  await page.reload();
  await expect(page.locator("#case-assets-view")).toBeVisible();
  await page.goto(origin);
  await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
  await page.goto(`${origin}/?start_path=1`);
  await expect(page.locator("#start-path-page")).toBeVisible();
  expect(fixture.requests.filter(request => request === "POST /cases")).toEqual([]);
  fixture.verify();
});

test("saved attempt resumes at Asset Overview after login even without a saved starting mode", async ({ page }) => {
  const fixture = await installFixtures(page, { workspaceStarted: true });
  await signIn(page);
  await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.locator("#case-assets-view")).toBeVisible();
  fixture.verify();
});

test("failed progress save retains uploaded files and retries without importing twice", async ({ page }) => {
  let uploads = 0;
  let saves = 0;
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "upload",
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.startsWith("/api/v1/materials/imports/")) return null;
      uploads += 1;
      return { status: 201, body: { document: { id: caseId }, case_id: caseId } };
    },
  });
  await page.route(`**/cases/${caseId}/workspace-entry`, async route => {
    saves += 1;
    if (saves > 1) return route.fallback();
    await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Case progress was not saved. Please retry." }) });
  });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await page.locator("#demo-file-input-case").setInputFiles(
    { name: "synthetic.pdf", mimeType: "application/pdf", buffer: Buffer.from("Synthetic file") });
  await page.locator("#demo-files-next-case").click();
  await expect(page.locator("#demo-file-status-case")).toContainText("Case progress was not saved.");
  await expect(page.locator("#demo-file-list-case li")).toHaveCount(1);
  await page.locator("#demo-files-next-case").click();
  await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
  expect(uploads).toBe(1);
  expect(saves).toBe(2);
  fixture.verify();
});

test("a partially failed document import retains selection and retries only the failed idempotent item", async ({ page }) => {
  const writes = [];
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "upload",
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.startsWith("/api/v1/materials/imports/")) return null;
      writes.push(new URL(request.url()).pathname);
      return writes.length === 2
        ? { status: 503, body: { detail: "Synthetic upload unavailable. Retry." } }
        : { status: 201, body: { document: { id: caseId }, case_id: caseId } };
    },
  });
  await page.route("**/api/v1/materials/imports/*", async route => {
    if (route.request().method() !== "GET") return route.fallback();
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ items: [] }) });
  });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await page.locator("#demo-file-input-case").setInputFiles([
    { name: "first.pdf", mimeType: "application/pdf", buffer: Buffer.from("First synthetic") },
    { name: "second.pdf", mimeType: "application/pdf", buffer: Buffer.from("Second synthetic") },
  ]);
  await page.locator("#demo-files-next-case").click();
  await expect(page.locator("#demo-file-status-case")).toHaveText("Synthetic upload unavailable. Retry.");
  await expect(page.locator("#demo-file-list-case li")).toHaveCount(2);
  await expect(page.locator("#demo-files-next-case")).toBeEnabled();
  await page.locator("#demo-files-next-case").click();
  await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
  expect(writes).toHaveLength(3);
  expect(writes[2]).toBe(writes[1]);
  fixture.verify();
});

test("Free has one attempt and paid has the Demo 2 presentation allowance", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true });
  for (const [status, count] of [["free", 1], ["paid", 3]]) {
    await page.route("**/api/billing/account/entitlement", route =>
      route.fulfill({ contentType: "application/json", body: JSON.stringify({ status }) }));
    await page.goto(`${origin}/case/assets?case_id=${caseId}`);
    await expect(page.locator("#asset-year-status-case")).not.toContainText("fictional");
    await expect(page.locator("#settlement-scenario-status-case")).not.toContainText("sample");
    await expect(page.locator("#demo-attempt-progress button")).toHaveCount(count);
  }
  fixture.verify();
});

test("actual Asset Overview edits persist, failure keeps the draft, and reload uses only saved values", async ({ page }) => {
  const overview = { revision: 0, overview: { snapshots: [], milestones: [] } };
  let failed = false;
  const fixture = await installFixtures(page, {
    authenticated: true,
    extraReads: { [`/cases/${caseId}/workspace`]: { ...workspace, asset_overview: overview } },
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.endsWith("/asset-overview")) return null;
      const sent = request.postDataJSON();
      expect(sent.expected_revision).toBe(overview.revision);
      if (!failed) {
        failed = true;
        return { status: 503, body: { detail: "Synthetic save failed." } };
      }
      Object.assign(overview, { revision: overview.revision + 1, overview: sent.overview });
      return { body: overview };
    },
  });
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.locator("#asset-table-rows-case")).toContainText("Unavailable");
  await expect(page.locator("#settlement-start-date-case")).toHaveValue("");
  await page.locator("#asset-edit-start-case").click();
  await expect(page.locator("#case-snapshot-date")).toHaveCount(0);
  const inputs = page.locator("#asset-table-rows-case input");
  for (let i = 0; i < await inputs.count(); i++) await inputs.nth(i).fill(i === 0 ? "123.45" : "0");
  await page.locator("#asset-edit-save-case").click();
  await expect(page.locator("#asset-edit-error-case")).toHaveText("Synthetic save failed.");
  await expect(inputs.first()).toHaveValue("123.45");
  await page.locator("#asset-edit-save-case").click();
  await expect(page.locator("#asset-table-total-case")).toContainText("$123.45");
  await expect(page.locator("#asset-chart-lines-case polyline")).toHaveCount(3);
  await expect(page.locator("#asset-edit-start-case")).toBeVisible();
  await page.reload();
  await expect(page.locator("#asset-table-total-case")).toContainText("$123.45");
  expect(overview.overview.snapshots[0].balances[0].you_cents).toBe(12345);
  fixture.verify();
});

test("actual Asset Trend selects start/end dates by mouse and recalculates three saved-data scenarios", async ({ page }) => {
  const categories = ["Home equity", "Retirement accounts", "Cash and savings", "Vehicles", "Debt"];
  const snapshot = (date, you, other) => ({
    date, balances: categories.map((category, index) => ({
      category, you_cents: index === 0 ? you : 0, other_cents: index === 0 ? other : 0,
    })),
  });
  const fixture = await installFixtures(page, {
    authenticated: true,
    extraReads: { [`/cases/${caseId}/workspace`]: {
      ...workspace, asset_overview: { revision: 1, overview: {
        snapshots: [
          snapshot("2020-01-01", 10000, 20000),
          snapshot("2021-01-01", 20000, 30000),
          snapshot("2022-01-01", 30000, 40000),
          snapshot("2023-01-01", 40000, 50000),
        ], milestones: [],
      } },
    } },
  });
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  const start = page.locator("#settlement-start-date-case");
  const end = page.locator("#settlement-end-date-case");
  const cards = page.locator("#settlement-scenario-results-case .settlement-scenario-card");
  await expect(start).toHaveValue("2020-01-01");
  await expect(end).toHaveValue("2023-01-01");
  await expect(cards).toHaveCount(3);
  await expect(cards.nth(1)).toContainText("Illustrative net to you: $400");
  await expect(cards.nth(1)).toContainText("Illustrative net to other party: $500");
  const position = async date => page.locator("#asset-timeline-chart-case").evaluate((chart, date) => {
    const fraction = (Date.parse(date) - Date.parse("2020-01-01")) / (Date.parse("2023-01-01") - Date.parse("2020-01-01"));
    const point = new DOMPoint(76 + fraction * 624, 60).matrixTransform(chart.getScreenCTM());
    return { x: point.x, y: point.y };
  }, date);
  await page.locator("#asset-timeline-chart-case").scrollIntoViewIfNeeded();
  let point = await position("2021-01-01");
  await page.mouse.click(point.x, point.y);
  await expect(start).toHaveValue("2021-01-01");
  point = await position("2023-01-01");
  await page.mouse.move(point.x, point.y);
  await page.mouse.down();
  point = await position("2022-01-01");
  await page.mouse.move(point.x, point.y, { steps: 5 });
  await page.mouse.up();
  await expect(end).toHaveValue("2022-01-01");
  await expect(cards.nth(1)).toContainText("Illustrative net to you: $300");
  await expect(cards.nth(1)).toContainText("Illustrative net to other party: $400");
  await expect(cards.nth(0)).toContainText("Illustrative net to you: $310");
  await expect(cards.nth(2)).toContainText("Illustrative net to you: $290");
  await expect(page.locator("#settlement-date-range-overlay-case .settlement-date-line")).toHaveCount(2);
  await cards.nth(0).locator("input").check();
  await expect(cards.nth(0)).toHaveAttribute("data-selected", "true");
  await page.locator("#asset-timeline-chart-case").scrollIntoViewIfNeeded();
  point = await position("2021-01-01");
  await page.mouse.move(point.x, point.y);
  await page.mouse.down();
  point = await position("2020-01-01");
  await page.mouse.move(point.x, point.y, { steps: 5 });
  await page.mouse.up();
  await expect(start).toHaveValue("2020-01-01");
  await expect(cards.nth(0).locator("input")).toBeChecked();
  await start.fill("2020-06-01");
  await start.dispatchEvent("change");
  await expect(cards).toHaveCount(3);
  await expect(cards.nth(0)).toContainText("Unavailable");
  await expect(cards.locator("input:disabled")).toHaveCount(3);
  expect(fixture.requests.filter(request => request.startsWith("PUT") || request.startsWith("POST"))).toEqual([]);
  fixture.verify();
});

test("actual scenarios show unavailable cards instead of a blank panel when no dated balances exist", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true });
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  const cards = page.locator("#settlement-scenario-results-case .settlement-scenario-card");
  await expect(cards).toHaveCount(3);
  await expect(cards.locator("input:disabled")).toHaveCount(3);
  await expect(cards.nth(0)).toContainText("Higher proposed share");
  await expect(cards.nth(1)).toContainText("Unavailable");
  await expect(page.locator("#settlement-scenario-status-case")).toContainText("complete saved balances");
  await expect(page.getByRole("button", { name: "Download CR 2A Word draft", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Download property schedule Excel", exact: true })).toBeDisabled();
  await expect(page.locator("#settlement-start-date-case")).toBeDisabled();
  fixture.verify();
});

test("actual scenario selection enables demo-style Word and Excel downloads with real dates and retryable errors", async ({ page }) => {
  const categories = ["Home equity", "Retirement accounts", "Cash and savings", "Vehicles", "Debt"];
  const dated = (date, you, other) => ({
    date, balances: categories.map((category, index) => ({
      category, you_cents:index ? 0 : you, other_cents:index ? 0 : other,
    })),
  });
  const exports = [];
  const fixture = await installFixtures(page, {
    authenticated:true,
    extraReads:{ [`/cases/${caseId}/workspace`]: {
      ...workspace, asset_overview:{ revision:3, overview:{
        snapshots:[dated("2020-01-01", 10000, 20000), dated("2023-01-01", 40000, 50000)],
        milestones:[],
      } },
    } },
    mutationHandler:request => {
      if (!request.url().includes(`/cases/${caseId}/asset-overview/exports/`)) return null;
      exports.push({ format:request.url().split("/").at(-1), ...request.postDataJSON() });
      if (exports.length === 1) return { status:503, body:{ detail:"Draft download failed. Your work is unchanged; retry." } };
      return { body:"PK-synthetic-download", contentType:"application/octet-stream" };
    },
  });
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  await page.locator('#settlement-scenario-results-case input[value="4500"]').check();
  const word = page.getByRole("button", { name:"Download CR 2A Word draft", exact:true });
  const excel = page.getByRole("button", { name:"Download property schedule Excel", exact:true });
  await expect(word).toBeVisible();
  await expect(excel).toBeVisible();
  await expect(word).toBeEnabled();
  await word.click();
  await expect(page.locator("#settlement-demo-export-status-case")).toContainText("Your work is unchanged; retry.");
  await expect(word).toBeEnabled();
  for (const [button, filename] of [[word, "cr2a-proposal-draft.docx"], [excel, "property-schedule-draft.xlsx"]]) {
    const downloaded = page.waitForEvent("download");
    await button.click();
    const file = await downloaded;
    expect(file.suggestedFilename()).toBe(filename);
    expect(await file.failure()).toBeNull();
    await expect(page.locator("#settlement-demo-export-status-case")).toContainText("Your attempt remains editable");
  }
  expect(exports.map(item => item.format)).toEqual(["docx", "docx", "xlsx"]);
  for (const { format, ...payload } of exports) {
    expect(payload).toEqual({
      expected_revision:3, attempt_ordinal:1, start_date:"2020-01-01",
      end_date:"2023-01-01", community_share_bps:4500,
    });
  }
  expect(fixture.requests.some(request => request.startsWith("POST /demo/exports/"))).toBe(false);
  await fixture.verify();
});

for (const outcome of ["accepted", "rejected"]) {
  test(`actual demo-aligned sent confirmation, counteroffer autosave and ${outcome} completion persist`, async ({ page }) => {
    const categories = ["Home equity", "Retirement accounts", "Cash and savings", "Vehicles", "Debt"];
    const saved = { revision:1, overview:{ snapshots:[
      { date:"2020-01-01", balances:categories.map(category => ({ category, you_cents:10000, other_cents:20000 })) },
      { date:"2023-01-01", balances:categories.map(category => ({ category, you_cents:20000, other_cents:30000 })) },
    ], milestones:[] } };
    const currentWorkspace = { ...workspace, asset_overview:saved, attempts:[], documents:[] };
    const state = { revision:0, attempt_ordinal:1, attempt_limit:1, sent:false, outcome:null,
      notes:"", document_ids:[], sent_filenames:[], selection:null, downloaded_formats:[],
      stopped:false, completed:false, accepted_document_ids:[] };
    const closed = { cases:[] };
    const mutations = [];
    let failedResponse = false;
    const fixture = await installFixtures(page, {
      authenticated:true,
      extraReads:{
        [`/cases/${caseId}/workspace`]:currentWorkspace,
        [`/cases/${caseId}/asset-mediation/1`]:state,
        "/api/v1/closed-cases":closed,
      },
      mutationHandler:request => {
        if (request.url().includes("/asset-overview/exports/")) {
          state.selection = request.postDataJSON();
          state.downloaded_formats.push(request.url().split("/").at(-1));
          state.revision++;
          return { body:"PK-test-document", contentType:"application/octet-stream" };
        }
        if (!request.url().endsWith("/asset-mediation")) return null;
        const payload = request.postDataJSON();
        mutations.push(payload);
        expect(payload.expected_revision).toBe(state.revision);
        if (payload.action === "sent") {
          expect(payload.confirm).toBe(true);
          expect(payload.selection).toEqual(state.selection);
          expect(new Set(state.downloaded_formats)).toEqual(new Set(["docx", "xlsx"]));
          state.sent = true;
          state.sent_filenames = ["cr2a-proposal-draft.docx", "property-schedule-draft.xlsx"];
          currentWorkspace.attempts.push({ ordinal:1, frozen:true, profile:{ metadata:{ asset_overview:saved } } });
        } else if (payload.action === "response") {
          if (!failedResponse) {
            failedResponse = true;
            return { status:503, body:{ detail:"Mediation response was not saved. Retry." } };
          }
          state.outcome = payload.outcome;
          state.notes = payload.notes;
        } else if (payload.action === "stop") {
          expect(state.outcome).toBe("rejected");
          state.stopped = true;
          closed.cases.push({ id:caseId, closed_reason:"stopped" });
        } else if (payload.action === "complete") {
          expect(state.outcome).toBe("accepted");
          state.completed = true;
        }
        state.revision++;
        return { body:state };
      },
    });
    await page.goto(`${origin}/case/assets?case_id=${caseId}`);
    const sent = page.getByRole("button", { name:"I reviewed and sent the final documents", exact:true });
    await expect(sent).toBeVisible();
    await expect(sent).toBeDisabled();
    await expect(page.locator("#settlement-demo-response-preview-case")).not.toContainText("fictional");
    for (const name of ["Download CR 2A Word draft", "Download property schedule Excel"]) {
      const downloading = page.waitForEvent("download");
      await page.getByRole("button", { name, exact:true }).click();
      await downloading;
    }
    await expect(sent).toBeEnabled();
    page.once("dialog", dialog => dialog.accept());
    await sent.click();
    await expect(page.locator("#settlement-demo-response-files-case")).toBeVisible();
    await expect(sent).toBeDisabled();
    await expect(page.locator("#settlement-start-date-case")).toBeDisabled();
    await expect(page.locator('#settlement-scenario-results-case input[value="5000"]')).toBeDisabled();
    const counteroffer = page.locator('#settlement-demo-response-files-case input[value="counteroffer"]');
    await counteroffer.click();
    await expect(page.locator("#settlement-demo-response-status-case")).toContainText("not saved");
    await counteroffer.check();
    await expect(page.locator("#settlement-demo-counteroffer-panel-case")).toBeVisible();
    await expect(page.locator("#settlement-demo-counteroffer-limit-case")).toContainText("Free");
    const counterofferNext = page.locator("#settlement-demo-add-counteroffer-case");
    await expect(counterofferNext).toBeVisible();
    await expect(counterofferNext).toHaveAttribute("aria-disabled", "true");
    await expect(page.locator("#settlement-demo-response-status-case")).toHaveText("");
    const mutationCount = mutations.length;
    const nextUrl = page.url();
    page.once("dialog", dialog => {
      expect(dialog.type()).toBe("alert");
      expect(dialog.message()).toContain("Upgrade your plan");
      void dialog.accept();
    });
    await counterofferNext.scrollIntoViewIfNeeded();
    const nextBounds = await counterofferNext.boundingBox();
    expect(nextBounds).not.toBeNull();
    await page.mouse.click(nextBounds.x + nextBounds.width / 2, nextBounds.y + nextBounds.height / 2);
    page.once("dialog", dialog => {
      expect(dialog.message()).toContain("Upgrade your plan");
      void dialog.accept();
    });
    await counterofferNext.focus();
    await page.keyboard.press("Enter");
    expect(mutations).toHaveLength(mutationCount);
    expect(page.url()).toBe(nextUrl);
    await page.locator("#settlement-demo-counteroffer-notes-case").fill("Actual received counteroffer notes");
    await expect.poll(() => state.notes).toBe("Actual received counteroffer notes");
    await page.reload();
    await expect(page.locator("#settlement-demo-counteroffer-notes-case")).toHaveValue("Actual received counteroffer notes");
    await expect(counterofferNext).toBeVisible();
    await expect(counterofferNext).toHaveAttribute("aria-disabled", "true");
    await expect(sent).toBeDisabled();
    await page.locator(`#settlement-demo-response-files-case input[value="${outcome}"]`).check();
    if (outcome === "accepted") {
      await page.locator("#settlement-demo-response-next-case").click();
      await expect(page).toHaveURL(new RegExp("/settlement-completion\\?case_id="));
      await expect(page.locator("#settlement-completion-demo-content")).toBeVisible();
      await expect(page.locator("#settlement-completion-status")).toContainText("Your accepted offer is confirmed");
      await expect(page.locator("#settlement-completion-page input[type=file]")).toHaveCount(0);
      await expect(page.locator("#settlement-completion-page .settlement-completion-actions > *")).toHaveCount(1);
      await page.getByRole("link", { name:"Back to your case", exact:true }).click();
      await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
      expect(state.completed).toBe(false);
    } else {
      await expect(page.locator("#settlement-demo-next-attempt-case")).toBeDisabled();
      page.once("dialog", dialog => dialog.accept());
      await page.locator("#settlement-demo-stop-case").click();
      await expect(page).toHaveURL(new RegExp("/rejection-completion\\?case_id="));
      await expect(page.locator("#rejection-completion-status")).toContainText("history and credits remain preserved");
    }
    expect(mutations.some(item => item.action === "continue")).toBe(false);
    await fixture.verify();
  });
}

test("paid actual response uploads an XLSX with original-name overwrite confirmation and opens the next attempt", async ({ page }) => {
  const categories = ["Home equity", "Retirement accounts", "Cash and savings", "Vehicles", "Debt"];
  const saved = { revision:1, overview:{ snapshots:[
    { date:"2020-01-01", balances:categories.map(category => ({ category, you_cents:10000, other_cents:20000 })) },
    { date:"2023-01-01", balances:categories.map(category => ({ category, you_cents:20000, other_cents:30000 })) },
  ], milestones:[] } };
  const selection = { expected_revision:1, attempt_ordinal:1, start_date:"2020-01-01", end_date:"2023-01-01", community_share_bps:5000 };
  const state = { revision:1, attempt_ordinal:1, attempt_limit:3, sent:true, outcome:"counteroffer",
    notes:"Received proposal", document_ids:[], sent_filenames:["cr2a-proposal-draft.docx", "property-schedule-draft.xlsx"],
    selection, downloaded_formats:["docx", "xlsx"], stopped:false, completed:false, accepted_document_ids:[] };
  const nextState = { ...state, revision:0, attempt_ordinal:2, sent:false, outcome:null,
    sent_filenames:[], selection:null, downloaded_formats:[] };
  const currentWorkspace = { ...workspace, asset_overview:saved,
    attempts:[{ ordinal:1, frozen:true, profile:{ metadata:{ asset_overview:saved } } }], documents:[] };
  const fileId = "00000000-0000-4000-8000-000000000099";
  const filename = "Other Party 제안.xlsx";
  const uploads = [];
  const fixture = await installFixtures(page, {
    authenticated:true,
    extraReads:{
      "/api/billing/account/entitlement":{ status:"paid" },
      [`/cases/${caseId}/workspace`]:currentWorkspace,
      [`/cases/${caseId}/asset-mediation/1`]:state,
      [`/cases/${caseId}/asset-mediation/2`]:nextState,
    },
    mutationHandler:request => {
      if (request.url().includes("/asset-mediation/1/files/")) {
        uploads.push(request.postData());
        if (!request.postData().includes("overwrite_document_id")) return {
          status:409, body:{ detail:{ code:"filename_conflict", filename, document_id:fileId } },
        };
        const newId = request.url().split("/").at(-1);
        state.document_ids = [newId];
        state.revision++;
        currentWorkspace.documents = [{ id:newId, original_filename:filename, extension:"xlsx", size_bytes:10 }];
        return { status:201, body:{ id:newId, original_filename:filename, state } };
      }
      if (request.url().endsWith("/asset-mediation")) {
        const payload = request.postDataJSON();
        expect(payload.expected_revision).toBe(state.revision);
        if (payload.action === "response") {
          state.notes = payload.notes;
          state.revision++;
          return { body:state };
        }
        if (payload.action === "continue") {
          nextState.notes = state.notes;
          nextState.document_ids = [...state.document_ids];
          currentWorkspace.attempts.push({ ordinal:2, frozen:false, profile:{ metadata:{ asset_overview:saved } } });
          return { body:nextState };
        }
      }
      return null;
    },
  });
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.locator("#settlement-demo-add-counteroffer-case")).toBeVisible();
  await expect(page.locator("#settlement-demo-add-counteroffer-case")).toHaveAttribute("aria-disabled", "false");
  page.once("dialog", dialog => { expect(dialog.message()).toContain(filename); void dialog.accept(); });
  await page.locator("#settlement-demo-counteroffer-file-case").setInputFiles({
    name:filename, mimeType:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", buffer:Buffer.from("PK-test-xlsx"),
  });
  await expect(page.locator("#settlement-demo-counteroffer-file-status-case a")).toHaveText(filename);
  expect(uploads).toHaveLength(2);
  expect(uploads[1]).toContain(fileId);
  await page.locator("#settlement-demo-add-counteroffer-case").click();
  await expect(page.locator('#demo-attempt-progress-list button[aria-current="step"]')).toContainText("2nd Attempt");
  await expect(page.locator("#settlement-demo-mark-sent-case")).toBeDisabled();
  await expect(page.locator("#asset-edit-start-case")).toBeEnabled();
  await expect(page.locator("#settlement-start-date-case")).toBeEnabled();
  await expect(page.locator("#settlement-demo-response-files-case")).toBeHidden();
  await fixture.verify();
});

test("case milestone add, edit and removal persist without resetting saved balances", async ({ page }) => {
  const overview = { revision: 0, overview: { snapshots: [], milestones: [] } };
  const fixture = await installFixtures(page, {
    authenticated: true,
    extraReads: { [`/cases/${caseId}/workspace`]: { ...workspace, asset_overview: overview } },
    mutationHandler: async request => {
      if (!new URL(request.url()).pathname.endsWith("/asset-overview")) return null;
      const sent = request.postDataJSON();
      Object.assign(overview, { revision: overview.revision + 1, overview: sent.overview });
      return { body: overview };
    },
  });
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  await page.locator("#milestone-manager-case summary").click();
  await page.locator("#custom-milestone-label-case").fill("Synthetic milestone");
  await page.locator("#custom-milestone-date-case").fill("2024-01-01");
  await page.locator("#custom-milestone-form-case button[type=submit]").click();
  const list = page.locator("#standard-milestone-list-case");
  await expect(list).toContainText("Synthetic milestone");
  await list.getByRole("button", { name: "Edit", exact: true }).click();
  await list.getByLabel("Milestone date").fill("2024-02-01");
  await list.getByRole("button", { name: "Save date", exact: true }).click();
  await expect(list).toContainText("2024-02-01");
  await page.reload();
  await page.locator("#milestone-manager-case summary").click();
  await expect(list).toContainText("2024-02-01");
  await list.getByRole("button", { name: "Remove", exact: true }).click();
  await expect(list.locator("li")).toHaveCount(0);
  expect(overview.revision).toBe(3);
  expect(overview.overview.snapshots).toEqual([]);
  fixture.verify();
});

test("same-name upload requires confirmation and retries overwrite cleanup without duplicate files", async ({ page }) => {
  const newId = "00000000-0000-4000-8000-000000000072";
  const filename = "Original 이름.pdf";
  const files = [{ id: caseId, original_filename: filename, extension: "pdf", size_bytes: 100, created_at: "2026-01-01T00:00:00Z" }];
  const posts = [];
  const fixture = await installFixtures(page, {
    authenticated: true,
    extraReads: { [`/cases/${caseId}/workspace`]: { ...workspace, documents: files } },
    mutationHandler: async request => {
      const path = new URL(request.url()).pathname;
      if (path.startsWith("/api/v1/materials/imports/") && request.method() === "POST") {
        posts.push(path);
        if (!request.postData().includes("overwrite_document_id")) return {
          status:409, body:{ detail:{ code:"filename_conflict", filename, document_id:caseId } },
        };
        expect(request.postData()).toContain(caseId);
        if (!files.some(file => file.id === newId)) {
          files.push({ id:newId, original_filename:filename, extension:"pdf", size_bytes:200, created_at:"2026-01-02T00:00:00Z" });
          return { status:503, body:{ detail:"Overwrite cleanup is incomplete. Retry the same upload." } };
        }
        files.splice(0, 1);
        return { status:201, body:{ document:{ id:newId, original_filename:filename }, case_id:caseId } };
      }
      return null;
    },
  });
  await page.route("**/api/v1/materials/imports/*", async route => {
    if (route.request().method() !== "GET") return route.fallback();
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ items: [] }) });
  });
  await page.goto(`${origin}/case/files?case_id=${caseId}`);
  await expect(page.locator("#case-saved-files-list h2")).toHaveText(filename);
  await expect(page.getByRole("button", { name:"Replace", exact:true })).toHaveCount(0);
  await expect(page.locator("#case-saved-files-refresh")).toHaveCount(0);
  page.once("dialog", dialog => { expect(dialog.message()).toContain("Overwrite it?"); void dialog.dismiss(); });
  await page.locator("#demo-case-files-input-case").setInputFiles({
    name: filename, mimeType: "application/pdf", buffer: Buffer.from("New file contents"),
  });
  await expect(page.locator("#case-saved-files-status")).toContainText("Upload cancelled:");
  expect(files).toHaveLength(1);
  page.once("dialog", dialog => dialog.accept());
  await page.locator("#case-files-retry").click();
  await expect(page.locator("#case-saved-files-status")).toContainText("Overwrite cleanup is incomplete.");
  await expect(page.locator("#case-saved-files-list .demo-case-file-item")).toHaveCount(2);
  await page.locator("#case-files-retry").click();
  await expect(page.locator("#case-saved-files-status")).toHaveText("1 file(s) saved to your case.");
  await expect(page.locator("#case-saved-files-list .demo-case-file-item")).toHaveCount(1);
  expect(posts).toHaveLength(4);
  expect(new Set(posts).size).toBe(1);
  await page.reload();
  await expect(page.locator("#case-saved-files-list h2")).toHaveText(filename);
  await expect(page.locator("#case-saved-files-list a")).toHaveAttribute("href", `/documents/${newId}/download`);
  fixture.verify();
});

test("over-quota selection fails before any file is imported and keeps all selected names", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true, mode: "upload" });
  await page.goto(`${origin}/onboarding/upload?case_id=${caseId}`);
  await page.locator("#demo-file-input-case").setInputFiles(Array.from({ length: 6 }, (_, index) => ({
    name: `synthetic-${index}.pdf`, mimeType: "application/pdf", buffer: Buffer.from("Synthetic file"),
  })));
  await page.locator("#demo-files-next-case").click();
  await expect(page.locator("#demo-file-status-case")).toContainText("Your account allows 5 saved files.");
  await expect(page.locator("#demo-file-list-case li")).toHaveCount(6);
  expect(fixture.requests.filter(request => request.startsWith("POST"))).toEqual([]);
  fixture.verify();
});

test("older real attempts show only their saved profile and never current wizard balances", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated: true,
    extraReads: {
      [`/cases/${caseId}/workspace`]: {
        ...workspace,
        asset_overview: { revision: 1, overview: {
          snapshots: [{ date: "2025-01-01", balances: [{ category: "Current saved balance", you_cents: 22200, other_cents: 0 }] }],
          milestones: [],
        } },
        intake: { dates: {}, finances: [{ description: "Current confidential balance", amount: "999.00" }] },
        attempts: [
          { ordinal: 1, frozen: true, profile: {
            property_assets: [{ name: "Historical property" }],
            metadata: { asset_overview: { revision: 1, overview: {
              snapshots: [{ date: "2024-01-01", balances: [{ category: "Historical saved balance", you_cents: 11100, other_cents: 0 }] }],
              milestones: [],
            } } },
          } },
          { ordinal: 2, frozen: false, profile: {} },
        ],
      },
    },
  });
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.locator("#asset-edit-start-case")).toBeEnabled();
  await expect(page.locator("#asset-table-rows-case")).toContainText("Current saved balance");
  await expect(page.getByRole("button", { name: "2nd Attempt, current", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "1st Attempt, read-only", exact: true }).click();
  await expect(page.locator("#asset-edit-status-case")).toContainText("read-only");
  await expect(page.locator("#asset-edit-start-case")).toBeDisabled();
  await expect(page.locator("#case-snapshot-date")).toHaveCount(0);
  await expect(page.locator("#case-assets-view")).not.toContainText("Current confidential balance");
  await expect(page.locator("#asset-table-rows-case")).toContainText("Historical saved balance");
  await expect(page.locator("#asset-table-rows-case")).not.toContainText("Current saved balance");
  await page.reload();
  await expect(page.locator("#asset-edit-start-case")).toBeDisabled();
  await expect(page.locator("#asset-table-rows-case")).toContainText("$111");
  await page.getByRole("button", { name: "2nd Attempt, current", exact: true }).click();
  await expect(page.locator("#asset-edit-start-case")).toBeEnabled();
  await expect(page.getByRole("button", { name: "2nd Attempt, current", exact: true })).toBeDisabled();
  fixture.verify();
});

test("latest finalized attempt also remains read-only instead of showing live case changes", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated: true,
    extraReads: {
      [`/cases/${caseId}/workspace`]: {
        ...workspace,
        case: { ...workspace.case, property_assets: [{ name: "Later case change" }] },
        attempts: [{ ordinal: 1, frozen: true, profile: { property_assets: [{ name: "Finalized property" }] } }],
      },
    },
  });
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.locator("#asset-edit-status-case")).toContainText("read-only");
  await expect(page.locator("#asset-edit-start-case")).toBeDisabled();
  await expect(page.locator("#case-assets-view")).not.toContainText("Later case change");
  fixture.verify();
});

test("unavailable workspace and invalid attempt remain explicit errors", async ({ page }) => {
  const fixture = await installFixtures(page, { authenticated: true });
  await page.goto(`${origin}/case/assets?case_id=${caseId}&attempt=8`);
  await expect(page.locator("#dashboard-error")).toContainText("The requested attempt is unavailable.");
  await expect(page.locator("#case-assets-view")).toBeHidden();
  await expect(page.locator("#demo-case-navigation")).toBeHidden();
  await page.route(`**/cases/${caseId}/workspace`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Workspace unavailable. Retry." }),
  }));
  await page.goto(`${origin}/case/assets?case_id=${caseId}`);
  await expect(page.locator("#dashboard-error")).toContainText("Workspace unavailable. Retry.");
  await expect(page.locator("#case-assets-view")).toBeHidden();
  fixture.verify();
});

test("real saved file deletion confirms, preserves failed files and refreshes after success", async ({ page }) => {
  const files = [{ id: caseId, extension: "pdf", size_bytes: 100, created_at: "2026-01-01T00:00:00Z" }];
  let deletions = 0;
  const fixture = await installFixtures(page, {
    authenticated: true,
    extraReads: { [`/cases/${caseId}/workspace`]: { ...workspace, documents: files } },
    mutationHandler: async (request) => {
      if (new URL(request.url()).pathname !== `/cases/${caseId}/materials/${caseId}/permanent-deletion`) return null;
      expect(request.method()).toBe("DELETE");
      expect(request.postDataJSON()).toEqual({ confirmation: "DELETE MATERIAL" });
      deletions += 1;
      if (deletions === 1) return { status: 503, body: { detail: "Deletion unavailable. Please retry." } };
      files.splice(0);
      return { status: 204, body: "" };
    },
  });
  await page.goto(`${origin}/case/files?case_id=${caseId}`);
  const remove = page.locator("#case-saved-files-list").getByRole("button", { name: "Delete", exact: true });
  await expect(remove).toBeVisible();
  page.once("dialog", dialog => dialog.dismiss());
  await remove.click();
  expect(deletions).toBe(0);
  page.once("dialog", dialog => dialog.accept());
  await remove.click();
  await expect(page.locator("#case-saved-files-status")).toContainText("Deletion unavailable. Please retry.");
  await expect(remove).toBeEnabled();
  page.once("dialog", dialog => dialog.accept());
  await remove.click();
  await expect(page.locator("#case-saved-files-list .demo-case-file-item")).toHaveCount(0);
  await expect(page.locator("#case-saved-files-status")).toHaveText("No files have been saved yet.");
  await page.reload();
  await expect(page.locator("#case-saved-files-list .demo-case-file-item")).toHaveCount(0);
  fixture.verify();
});











for (const mode of ["real", "demo"]) {
  test(`${mode} wizard completion reacts to required dates and asset or debt input and restores on reload`, async ({ page }) => {
    const savedIntake = { revision: 1, draft: {} };
    const fixture = await installFixtures(page, {
      authenticated: mode === "real",
      mode: "wizard",
      extraReads: { [`/cases/${caseId}/wizard-intake`]: savedIntake },
      mutationHandler: async request => {
        if (new URL(request.url()).pathname !== `/cases/${caseId}/wizard-intake`) return null;
        const sent = request.postDataJSON();
        savedIntake.revision = sent.expected_revision + 1;
        savedIntake.draft = sent.draft;
        return { body: savedIntake };
      },
    });
    const url = mode === "real"
      ? `${origin}/onboarding/wizard?case_id=${caseId}`
      : `${origin}/demo/start?source=demo1`;
    await page.goto(url);
    if (mode === "demo") await page.locator("#demo-case-wizard-link").click();
    await expect(page.locator("#wizard-save-status")).not.toContainText("Loading");
    const finish = page.locator("#wizard-finish");
    await expect(page.locator("#wizard-finish-hint")).toHaveCount(0);
    await page.locator('[name="wizard-filed"][value="yes"]').check();
    await page.locator('[name="wizard-role"][value="respondent"]').check();
    await expect(finish).toBeDisabled();
    await page.locator("#wizard-date-marriage").fill("2020-01-01");
    await page.locator("#wizard-date-petition").fill("2024-01-01");
    await expect(finish).toBeDisabled();
    await page.locator('[data-wizard-add="finance"]').click();
    await expect(finish).toBeDisabled();
    const description = page.locator('[data-wizard-field="description"]').first();
    await description.fill("Premarital savings");
    await expect(finish).toBeEnabled();
    await description.fill("   ");
    await expect(finish).toBeDisabled();
    await page.locator('[data-wizard-field="category"]').first().fill("Bank account");
    await expect(finish).toBeEnabled();
    await page.locator('[data-wizard-field="kind"]').first().selectOption("debt");
    await expect(finish).toBeEnabled();
    await page.locator('[data-wizard-unknown="marriage"]').check();
    await expect(finish).toBeDisabled();
    await page.locator('[data-wizard-unknown="marriage"]').uncheck();
    await page.locator("#wizard-date-marriage").fill("2020-01-01");
    await expect(finish).toBeEnabled();
    await page.locator("#wizard-date-petition").fill("");
    await expect(finish).toBeDisabled();
    await page.locator("#wizard-date-petition").fill("2024-01-01");
    await expect(finish).toBeEnabled();
    await page.locator('[data-wizard-remove-entry="finances"]').click();
    await expect(finish).toBeDisabled();
    await page.locator('[data-wizard-add="finance"]').click();
    await page.locator('[data-wizard-field="description"]').first().fill("Loan balance");
    await expect(finish).toBeEnabled();
    await expect(page.locator("#wizard-save-status")).toContainText(
      mode === "demo" ? "Saved in this browser" : "Saved to your case");
    await page.reload();
    await expect(finish).toBeEnabled();
    await expect(page.locator('[data-wizard-field="description"]').first()).toHaveValue("Loan balance");
    if (mode === "demo") {
      await finish.click();
      await expect(page).toHaveURL(/\/demo\?source=demo1/);
    } else {
      await finish.click();
      await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
    }
    fixture.verify();
  });
}

test("real wizard cannot finish when its saved draft failed to load even with complete browser-local data", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated: true, mode: "wizard",
  });
  await page.route(`**/cases/${caseId}/wizard-intake`, route =>
    route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Draft storage unavailable." }) }));
  await page.goto(`${origin}/onboarding/wizard?case_id=${caseId}`);
  await expect(page.locator("#wizard-save-status")).toContainText("Draft storage unavailable.");
  await page.locator('[name="wizard-filed"][value="yes"]').check();
  await page.locator('[name="wizard-role"][value="petitioner"]').check();
  await page.locator("#wizard-date-marriage").fill("2020-01-01");
  await page.locator("#wizard-date-petition").fill("2024-01-01");
  await page.locator('[data-wizard-add="finance"]').click();
  await page.locator('[data-wizard-field="description"]').first().fill("Loan");
  await expect(page.locator("#wizard-finish")).toBeDisabled();
  fixture.verify();
});

for (const success of [true, false]) {
  test(`wizard Next ${success ? "opens assets" : "preserves its editable draft on failure"}`, async ({ page }) => {
    const fixture = await installFixtures(page, {
      authenticated: true,
      mode: "wizard",
      intake: {
        filed: "yes", role: "petitioner",
        dates: { marriage: { date: "2020-01-01", unknown: false }, petition: { date: "2024-01-01", unknown: false } },
        finances: [{ id: caseId, kind: "asset", category: "Savings", description: "", amount: null }],
        issues: [], agreements: [],
      },
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
    await page.locator("#wizard-finish").click();
    if (success) await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
    else {
      await expect(page.locator("#wizard-save-status")).toContainText("Synthetic wizard save unavailable.");
      await expect(page).toHaveURL(url);
    }
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
      authenticated:true,
      extraReads: {
        [`/cases/${caseId}/settlement-planning/selections/${selectionId}/offer-response`]: {
          outcome: accepted ? "accepted" : null,
          sent_confirmed: accepted,
          sent_documents_complete: accepted,
          attachments: [],
          frozen: true,
        },
      },
    });
    await page.goto(`${origin}/settlement-completion?case_id=${caseId}&selection_id=${selectionId}`);
    if (accepted) {
      await expect(page.locator("#settlement-completion-demo-content")).toBeVisible();
      await expect(page.locator("#settlement-completion-page input[type=file]")).toHaveCount(0);
      await expect(page.locator("#settlement-completion-page .settlement-completion-actions > *")).toHaveCount(1);
      await expect(page.locator("#settlement-completion-page")).toHaveCSS("margin-top", "0px");
      await expect(page.getByRole("link", { name:"Back to your case", exact:true })).toHaveAttribute("href", `/case/assets?case_id=${caseId}`);
    } else {
      await expect(page.locator("#settlement-completion-status")).toHaveText("This completion page is only available for an accepted, confirmed offer.");
      await expect(page.locator("#settlement-completion-demo-content")).toBeHidden();
    }
    await expect(page.locator("#settlement-planner")).toHaveCount(0);
    fixture.verify();
  });
}

test("accepted real page uses the exact demo guidance and only returns to its case without mutation", async ({ page }) => {
  const fixture = await installFixtures(page, {
    authenticated:true,
    extraReads:{ [`/cases/${caseId}/asset-mediation/1`]:{
      revision:1, attempt_ordinal:1, sent:true, outcome:"accepted", completed:false,
    } },
  });
  const guidance = () => page.locator("#settlement-completion-demo-content").evaluate(section => {
    const copy = section.cloneNode(true);
    copy.querySelector("#settlement-completion-demo-notice").remove();
    return copy.innerHTML;
  });
  await page.goto(`${origin}/demo/start?source=demo1`);
  await page.locator("#demo-case-documents-link").click();
  const demoQuery = new URL(page.url()).search;
  await page.goto(`${origin}/demo/settlement-completion${demoQuery}`);
  await expect(page.locator("#settlement-completion-demo-content")).toBeVisible();
  const demoGuidance = await guidance();
  await page.goto(`${origin}/settlement-completion?case_id=${caseId}&asset_attempt=1`);
  await expect(page.locator("#settlement-completion-demo-content")).toBeVisible();
  expect(await guidance()).toBe(demoGuidance);
  await expect(page.locator("#settlement-completion-demo-notice")).toBeHidden();
  await expect(page.locator("#settlement-completion-page input[type=file]")).toHaveCount(0);
  await expect(page.getByRole("link", { name:"Back to mediation", exact:true })).toHaveCount(0);
  await expect(page.locator("#settlement-completion-page .settlement-completion-actions > *")).toHaveCount(1);
  await page.getByRole("link", { name:"Back to your case", exact:true }).click();
  await expect(page).toHaveURL(`${origin}/case/assets?case_id=${caseId}`);
  expect(fixture.requests.filter(request => request.startsWith("POST "))).toEqual([]);
  fixture.verify();
});

for (const source of ["demo1", "demo2"]) {
  test(`${source}: real attempt design matches demo at desktop, tablet and mobile widths`, async ({ page }) => {
    const fixture = await installFixtures(page, { authenticated: true, extraReads: { "/api/billing/account/entitlement": { status: source === "demo1" ? "free" : "paid" } } });
    await page.goto(`${origin}/demo/start?source=${source}`);
    await page.locator("#demo-case-documents-link").click();
    const query = new URL(page.url()).search;
    const styles = async () => {
      const selectors = [
        "body", "#demo-case-navigation", ".demo-case-nav-links",
        "#demo-attempt-progress", ".demo-attempt-progress button",
        ".demo-attempt-circle", ".demo-attempt-progress-label",
      ];
      const result = [];
      for (const selector of selectors) {
        result.push(await page.locator(selector).first().evaluate(element => {
          const style = getComputedStyle(element);
          return Object.fromEntries([
            "position", "paddingTop", "paddingBottom", "paddingLeft", "paddingRight",
            "minHeight", "fontSize", "fontWeight", "color", "backgroundColor",
            "borderRadius", "boxShadow", "gap", "gridTemplateColumns", "gridColumn",
          ].map(property => [property, style[property]]));
        }));
      }
      return result;
    };
    for (const width of [1280, 880, 800, 600, 480, 350]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`${origin}/demo${query}`);
      const demoCurrent = page.getByRole("button", { name: "1st Attempt, current", exact: true });
      await expect(demoCurrent).toBeDisabled();
      expect(await demoCurrent.evaluate(element => getComputedStyle(element).cursor)).toBe("default");
      await demoCurrent.dispatchEvent("click");
      await expect(page).toHaveURL(`${origin}/demo${query}`);
      await expect(page.locator("#settlement-demo-attempt-status")).toHaveCount(0);
      const demoStyles = await styles();
      await page.goto(`${origin}/case/assets?case_id=${caseId}`);
      await expect(page.locator("#case-attempt-banner")).toHaveCount(0);
      const actual = await styles();
      // Track widths depend on the number of attempts; compare the shared placement, not content width.
      demoStyles[1].gridTemplateColumns = demoStyles[1].gridTemplateColumns.split(" ").length;
      actual[1].gridTemplateColumns = actual[1].gridTemplateColumns.split(" ").length;
      expect(actual, `Shared attempt design at ${width}px`).toEqual(demoStyles);
      expect(actual[0].paddingTop).toBe("0px");
    }
    fixture.verify();
  });

  test(`${source}: demo start choices remain intact after workspace deletion`, async ({ page }) => {
    const fixture = await installFixtures(page);
    await page.goto(`${origin}/demo/start?source=${source}`);
    await expect(page.locator("#demo-case-choice-page")).toBeVisible();
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
    await expect(page.locator("#settlement-completion-page .settlement-completion-actions > *")).toHaveCount(1);
    await expect(page.getByRole("link", { name:"Back to your case", exact:true })).toHaveAttribute("href", new RegExp("/demo\\?"));
    fixture.verify();
  });
}
