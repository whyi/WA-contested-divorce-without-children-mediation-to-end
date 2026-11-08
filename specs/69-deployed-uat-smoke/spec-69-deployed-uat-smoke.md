# Spec 69: Deployed Owner-Beta UAT Smoke Automation

- **Related issue:** [#252](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/252)
- **Amends:** Spec 62 requirements 1 and 8 by adding automated, deployed smoke evidence alongside its manual scenarios. All other Spec 62 requirements remain unchanged. No historical specification is edited.
- **References:** Specs 57-61 govern isolation and destructive operations; Specs 64-67 govern account ownership and navigation; Spec 32 (live proposal draft sync) governs download and confirmation gates.

## Requirements

- **FR-69-01:** Run serial Chromium Playwright checks against only the approved HTTPS origin `https://0w4jgh9j9a.execute-api.us-west-2.amazonaws.com`. Reject alternate origins, credentials, paths, queries, fragments, and insecure URLs before network activity.
- **FR-69-02:** Check `/healthz` and `/readyz` status and response shapes, denial of anonymous account-dashboard/session access, visible sign-in controls without submitting credentials, and both fictional demo entry choices without creating a case. Each test uses a fresh anonymous browser context.
- **FR-69-03:** Restrict browser network traffic to approved-origin GET/HEAD reads and block third-party requests. Record attempted same-origin writes as test failures. API checks do not follow redirects; redirecting status/auth responses cannot count as passes.
- **FR-69-04:** Never register an account, send email, access account materials, upload files, invoke AI, charge payments, or perform reset/deletion. No credentials or authenticated browser state are accepted by this first phase.
- **FR-69-05:** A manual GitHub Actions workflow installs locked test dependencies and Chromium, validates the suite configuration, and runs deployed smoke checks. It does not run on every source push or alter the deployment.
- **FR-69-06:** Publish a minimal JSON report containing run time, approved origin, runner commit (not claimed as deployed commit), static scenario IDs, PASS/FAIL outcomes, and authenticated-UAT status BLOCKED. A failed/interrupted run exits unsuccessfully. Do not publish DOM, response bodies, credentials, cookies, screenshots, traces, video, or raw exception text.
- **FR-69-07:** Anonymous smoke success is not full UAT sign-off. Until an approved synthetic owner account and secure credential handling exist, authenticated navigation, wizard persistence, download/confirmation gates, and case resume remain BLOCKED.

## Acceptance

1. Unit checks reject unsafe targets and verify sanitized reporting and failure outcomes.
2. Anonymous browser/API checks execute against the deployment with recorded outcomes.
3. Manual workflow retains only sanitized results, even when smoke checks fail.
4. The UAT runbook describes local and Actions execution and explicitly distinguishes runner revision from independently recorded deployment revision.
5. Existing specs and product behavior remain unchanged.

## Follow-up authenticated phase

Implement separately after owner-controlled account verification and synthetic-data approval: sign-in to new-case choice or the existing case (never an Active cases list), wizard back/continue and persistence, account plan display, single-case ownership, scenario selection before downloads, both current downloads before confirmation, proposal edits and regenerated files, and frozen attempts after confirmation. Use secure credentials and serial cases. Destructive reset, recovery email, payments, and backup restore require separate operator approval and remain outside ordinary smoke runs.
