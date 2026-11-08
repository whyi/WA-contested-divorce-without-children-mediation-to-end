# Owner-Beta UAT Runbook

Use this runbook only against the dedicated owner-beta UAT environment with
synthetic data. It is an executable manual scenario list and evidence template,
not evidence that the environment has been deployed or tested. Follow the
[deployment instructions](README.md) first. The suite complements the broader
[release acceptance matrix](../../../specs/53-release-acceptance-matrix/spec-53-release-acceptance-matrix.md);
it does not replace production, legal, payment, AI, accessibility, or release
approval.

## Run rules

### Automated anonymous smoke (Spec 69)

The `Deployed UAT smoke` workflow is manually dispatched from GitHub Actions.
It targets only `https://0w4jgh9j9a.execute-api.us-west-2.amazonaws.com` and
accepts no credentials.

The Actions runner is pinned to Ubuntu 24.04, supported by the locked Playwright
Chromium build. Do not replace it with `ubuntu-latest` without verifying browser
installation on that release; Ubuntu 26.04 is unsupported by Playwright 1.58.2.

To run locally with Node 22 and Chromium:

```bash
cd uat
npm ci
npm run check
npx playwright install chromium
npm run smoke
```

The sanitized `uat-smoke-results` artifact maps SMOKE-01 to health, SMOKE-02 to
readiness, SMOKE-03 to anonymous dashboard/session denial, SMOKE-04 to sign-in
controls, and SMOKE-05/06 to the fictional Demo 1/2 start choices. Tests do not
submit forms or create a case. Browser writes and third-party requests are
blocked; attempted same-origin writes fail the test.

The report records the runner commit only. Record the deployed image/commit
independently under the run rules below. Screenshots, traces, videos, response
bodies, and raw errors are not retained. Use the scenario ID to reproduce a
failure in an approved local session; never attach sensitive browser data.
Missing reports or failed installation are NOT RUN, not PASS.

Authenticated scenarios remain BLOCKED until an approved synthetic owner
account and secure authentication setup exist. Smoke success is not full UAT
or evidence of wizard persistence, proposal/download gates, deletion, payments,
email delivery, infrastructure isolation, or backup restore. Follow the manual
scenarios below and Spec 69's authenticated follow-up separately.

- Record the deployed commit/image reference and UTC start time before testing.
- Confirm the AWS caller account matches Terraform state. Confirm the application
  uses the `owner_beta_uat` database, UAT-prefixed document and deletion-ledger
  buckets, the owner-beta readiness gate, and the expected owner allowlist.
- Confirm HTTPS, `/healthz`, and `/readyz`. A liveness response alone is not
  readiness or UAT sign-off.
- Confirm AI and live Stripe are not configured. Keep SES in sandbox and send
  only to an explicitly verified owner-controlled destination. Never enter
  real client information or production credentials.
- Start from the documented empty owner-case baseline. Do not run reset
  automatically or as part of ordinary tests. Export any synthetic evidence
  needed for review before the final delete/reset scenarios.
- Use `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN` for every scenario. Attach only
  redacted evidence; do not record credentials, email addresses, case facts,
  document contents, tokens, or payment details.
- Test rejected signup with a reserved `.invalid` address and verify no account
  or email was created. Do not send test messages to an address that is not
  explicitly approved and verified in SES.

## Scenarios

### UAT-00 — Environment and integration isolation

1. Compare the AWS caller account with the Terraform output and record only the
   approved environment identifier.
2. Verify HTTPS, `/healthz`, `/readyz`, owner-beta mode, and the dedicated
   database/storage identities using the operator's approved configuration
   inspection procedure.
3. Verify AI and live Stripe remain disabled. Confirm SES sandbox restrictions
   and that the only intended test recipient is verified.

**Expected:** All identities point to the dedicated UAT environment; readiness
passes; no production resource or live AI/payment credential is configured.
Stop the run on any mismatch.

### UAT-01 — Owner-only signup, authentication, and recovery

1. On the first run, register the designated owner and complete email
   verification using the approved SES sandbox destination. On later runs,
   sign in with the existing owner account.
2. Attempt signup with a reserved non-owner `.invalid` address. Verify the
   generic response, absence of an account, and absence of an outbound email.
3. Exercise owner password recovery and sign in with the resulting credential.
   Verify recovery for a non-owner address does not create or disclose an
   account.
4. If MFA or passkeys are enabled for the deployment, verify the owner path and
   non-owner denial without exposing credential existence.

**Expected:** Only the configured owner can authenticate; denied requests do
not create accounts, sessions, recovery tokens, or email. Automated coverage:
`tests/test_auth_routes.py`, `tests/test_config.py`.

### UAT-02 — Account-backed case creation and resume

1. From the empty baseline, create a case through the normal account-backed
   preparation path using synthetic facts.
2. Sign out/in or open a fresh session and resume the same case.
3. Verify the party account cannot create a second owned case and that case
   data is unavailable to an unauthenticated or unrelated user.

**Expected:** The same authorized owner can resume the saved case; unauthorized
access is denied; the owner has at most one case. Automated coverage:
`tests/test_case_lifecycle.py`, `tests/test_wizard_intake.py`,
`tests/test_auth_routes.py`.

### UAT-03 — Document-first preparation path

1. Use the guarded reset script to return to the empty baseline, following its
   exact confirmation and AWS-account check.
2. Start preparation by uploading a synthetic, supported document before
   creating a case through the ordinary case-first path.
3. Verify the resulting case belongs to the owner, appears in the fixture
   registry, and can be reopened in a new session.

**Expected:** The first-upload path creates one owner case and registers only
that UAT case. Automated coverage: `tests/test_materials.py`,
`tests/test_uat_fixtures.py`.

### UAT-04 — Upload, extraction, and quota behavior

1. Upload a synthetic PDF/DOCX within the configured size and page limits.
   Confirm upload, extraction status, and resulting document are visible to the
   owner.
2. Verify the Free case limit of five stored attachments, rejection of the
   sixth, and that deleting one attachment releases a slot. Verify the 2 MiB
   per-file limit using approved synthetic fixtures.
3. Verify unsupported, encrypted, scanned, and over-page-limit samples receive
   their documented actionable status; do not imply OCR is available.
4. For retry behavior, use the normal retry control on an eligible synthetic
   extraction failure and verify the configured retry ceiling. Do not induce a
   production-provider outage.

**Expected:** Server-side limits hold across upload entry points, failed files
remain clearly actionable, and no rejected upload is silently stored or
charged. Paid-plan limits are covered by repository tests or an explicitly
approved non-live entitlement setup; never use live payments. Automated
coverage: `tests/test_materials.py`, `tests/test_attachment_limits.py`,
`tests/test_extraction.py`, `tests/test_extraction_concurrency.py`,
`tests/test_uat_fixtures.py`.

### UAT-05 — Proposal editing, comparison, and attempt finalization

1. Enter and edit synthetic user and opposing-party offer values. Recalculate
   the comparison and confirm the user's overrides are reflected.
2. Create and review a mediator-facing proposal with manual synthetic inputs
   using the available user-controlled proposal flow. Do not invoke AI
   analysis. Download/finalize it using the explicit confirmation.
3. Verify the finalized attempt is read-only and its snapshot is retained.
   Continue only by starting a new attempt; do not send the proposal directly
   to the opposing party.

**Expected:** Values remain editable before finalization; the final snapshot is
immutable, and any later negotiation work belongs to a new attempt. Automated
coverage: `tests/test_offer_comparison.py`,
`tests/test_attempt_finalization.py`, `tests/test_counteroffer_workflow.py`.

### UAT-06 — Failure, retry, and no-charge behavior

1. Exercise a documented validation failure with a synthetic unsupported file.
   Verify it is rejected before storage and does not consume an attempt credit.
2. Upload a synthetic encrypted or scanned PDF and verify the actionable
   `needs_attention` state. Replace it with a supported, unprotected,
   text-based synthetic copy and confirm the rest of the case remains intact.
3. Verify duplicate submission does not duplicate stored material or consume
   another attachment slot. Exercise worker retry ceilings through the
   automated suite rather than inducing an outage in the hosted environment.

**Expected:** Failure is visible and actionable; the user's case remains
available, and failed processing does not silently consume work or credit. Do
not disable shared services or inject a live-provider outage. Automated
coverage: `tests/test_failure_recovery.py`, `tests/test_materials.py`,
`tests/test_extraction.py`, `tests/test_attempt_finalization.py`.

### UAT-07 — Export, closure/reopen, deletion, and reset

1. Export the synthetic case data and verify the downloaded archive opens and
   contains the expected categories without exposing another account's data.
2. Close and reopen the case; verify its work, materials, and unused credits
   remain available.
3. Verify permanent material deletion removes the material and releases its
   upload slot.
4. After saving only redacted evidence, run the guarded UAT reset as the final
   case action. Verify the account still authenticates, no case remains, and
   the permanent-deletion ledger entry is retained.

**Expected:** Export is complete and scoped; closure is reversible; explicit
deletion/reset is permanent, ledger-backed, and preserves the owner account.
Automated coverage: `tests/test_case_lifecycle.py`, `tests/test_deletion.py`,
`tests/test_uat_fixtures.py`.

### UAT-08 — Isolated backup restore and deletion reconciliation

This scenario requires a separately approved maintenance window, a disposable
isolated restore target, a known synthetic deletion, and the initialized
external deletion ledger. It is **BLOCKED** until those prerequisites exist.

1. Follow [the deletion-ledger restore procedure](../../../docs/deletion-ledger-restore.md)
   without routing user traffic to the restored database.
2. Restore a snapshot that predates a synthetic case deletion; reconcile it
   against the preserved UAT deletion ledger before starting API or workers.
3. Verify the deleted case and its stored object versions do not reappear, and
   verify reconciliation and readiness succeed.

**Expected:** No restored user traffic is served before successful
reconciliation; deleted synthetic data remains deleted. Case reset is not a
substitute for this exercise. Automated coverage:
`tests/test_deletion.py` is simulated database coverage only and does not count
as provider restore evidence.

## Run record

Copy this section for each run. Keep evidence in an approved restricted
location and put only its reference here.

```text
Environment identifier:
Deployed commit/image:
Started at (UTC):
Completed at (UTC):
Operator/reviewer role:
Evidence record reference:

UAT-00 Environment and integration isolation: NOT RUN
UAT-01 Owner-only signup, authentication, and recovery: NOT RUN
UAT-02 Account-backed case creation and resume: NOT RUN
UAT-03 Document-first preparation path: NOT RUN
UAT-04 Upload, extraction, and quota behavior: NOT RUN
UAT-05 Proposal editing, comparison, and attempt finalization: NOT RUN
UAT-06 Failure, retry, and no-charge behavior: NOT RUN
UAT-07 Export, closure/reopen, deletion, and reset: NOT RUN
UAT-08 Isolated backup restore and deletion reconciliation: BLOCKED

Follow-up issue/reference:
Owner sign-off (required before claiming UAT complete):
```

Do not mark the owner-beta UAT complete while a required scenario is `FAIL`,
`BLOCKED`, or `NOT RUN`. This runbook alone is not deployment, backup-restore,
provider, legal, or release evidence.
