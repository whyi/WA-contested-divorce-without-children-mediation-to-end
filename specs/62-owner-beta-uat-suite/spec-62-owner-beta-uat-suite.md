# Spec 62: Owner-Beta Repeatable UAT Suite

- **Status:** UAT runbook and evidence template implemented; deployment and execution are pending
- **Related issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related pull requests:** [#216 — Add AWS infrastructure for owner-only UAT](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/216), [#219 — Add guarded owner-beta UAT case reset](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/219)
- **Related specifications:** [Spec 53: Release Acceptance Matrix](../53-release-acceptance-matrix/spec-53-release-acceptance-matrix.md), [Spec 57: Owner-Beta Environment Boundaries](../57-owner-beta-environment-boundaries/spec-57-owner-beta-environment-boundaries.md), [Spec 58: Owner-Only Authentication](../58-owner-only-authentication/spec-58-owner-only-authentication.md), [Spec 59: Owner-Beta Deployment Readiness](../59-owner-beta-deployment-readiness/spec-59-owner-beta-deployment-readiness.md), [Spec 60: Owner-Beta AWS Infrastructure](../60-owner-beta-aws-infrastructure/spec-60-owner-beta-aws-infrastructure.md), [Spec 61: Synthetic UAT Case Reset](../61-owner-beta-synthetic-uat-reset/spec-61-owner-beta-synthetic-uat-reset.md)
- **Objective:** Provide a repeatable, evidence-based owner UAT procedure without treating automated unit tests, reset capability, or infrastructure code as proof of a deployed end-to-end pass.

## Requirements

1. The UAT runbook identifies preflight checks, ordered manual scenarios, expected results, reset points, evidence requirements, and blocked/not-run handling.
2. The scenarios cover environment isolation, owner-only access, account recovery, both supported case-preparation paths, uploads and extraction, proposal editing and finalization, failure handling, Free-plan limits, export, closure/reopen, permanent deletion, and backup restore/deletion reconciliation.
3. Use only synthetic names, facts, offers, and documents. Do not copy production data or place secrets, personal data, case contents, or payment details in the run record.
4. AI analysis and live payments stay disabled. Verify that an unauthorized signup attempt creates no account and sends no email. Verify email delivery only to an explicitly verified owner-controlled destination in the SES sandbox.
5. Paid entitlements are verified using automated tests or an approved non-live test setup; the UAT operator must not enable live payments or manually bypass server-side entitlement checks.
6. Case deletion and reset are destructive. Run those scenarios only after exporting needed synthetic evidence, confirming the UAT target, and following the exact confirmations in the deletion/reset tools.
7. Backup restore is distinct from case reset. Do not mark recovery as passed until an approved isolated snapshot restore has been reconciled against the initialized external deletion ledger and the result is recorded.
8. Every scenario has an explicit `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN` outcome. Missing evidence is not a pass, and a blocked backup/restore check prevents claiming full UAT sign-off.

## Acceptance criteria

- A new operator can execute the ordered scenarios in the [owner-beta UAT runbook](../../deploy/aws/owner-beta/uat-runbook.md) from the documented no-active-case baseline.
- Each scenario states a verifiable expected result and points to relevant automated repository coverage where available.
- The run record captures only environment identifier, deployed commit/image reference, timestamp, scenario status, reviewer, redacted evidence reference, and follow-up.
- The runbook distinguishes app-level permanent deletion/reset from database snapshot restore and requires external-ledger reconciliation before restored data is exposed.
- The owner-beta README links the runbook and does not claim that deployment, provider verification, recovery, or a UAT run has occurred.

## Out of scope

Provisioning AWS resources, sending real email outside the verified SES sandbox, enabling AI or live payments, restoring a database, performing destructive UAT actions, or claiming UAT/release sign-off.
