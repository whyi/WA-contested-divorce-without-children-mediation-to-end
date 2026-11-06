# Spec 53: Release Acceptance Matrix and Sign-Off Evidence

- **Status:** Automated repository checks recorded; production release is not approved
- **Related issue:** [#137 — Run end-to-end release acceptance and launch sign-off](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/137)
- **Related specifications:** Specs 44, 47, 49, 50, 51, and 52
- **Objective:** Track what automated tests establish separately from browser, provider, legal, operational, and product-owner release evidence.

## Evidence from this acceptance pass

- Full unit suite on `origin/main` at `fa927d68b4c4c8fcf84630e54d3fe41493c3842a` (PR #169 merged): 548 tests, 2 skipped, and 1 known unrelated failure in `test_theme_selection_persistence_and_shared_page_coverage` because its regex rejects the existing `#17241f` theme color.
- Refreshed focused release-journey modules: 279 tests run; 278 passed and 1 optional PostgreSQL test skipped because `WA_TEST_POSTGRES_URL` was not configured. Coverage included authentication routes, case delegation, materials and attachment limits, existing-offer intake, settlement routes and comparisons, attempt finalization, offer response, case lifecycle, rejection completion, permanent deletion and simulated external-ledger restore reconciliation, export, storage, billing/credit policy, AI-purpose and legal-boundary gates, readiness, failure recovery, PDF extraction, document limits, and static accessibility markup.
- Python compilation and `git diff --check` passed.
- PR #169 records limited headless Chromium checks of five fictional demo routes at 320, 375, 768, and 1280 CSS pixels, with no measured page-level horizontal overflow, plus keyboard-focus and browser-local file select/remove smoke checks. This is not a supported-browser matrix or authenticated browser-driven end-to-end test.
- This remains a set of automated unit/route tests and limited demo-preview checks, not a complete browser journey against a production-like deployment.

## Release matrix

| Area | Automated repository evidence | Manual/provider evidence | Status | Required owner/evidence |
|---|---|---|---|---|
| Sign-up, sign-in, recovery, authorization, single operator | `tests/test_auth_routes.py`, `tests/test_case_delegation.py` | Real email delivery, production identity configuration, and full browser journey not exercised | Partial | Release operator records deployment and end-to-end results |
| Wizard/materials intake, offer capture, quotas | `tests/test_materials.py`, `tests/test_attachment_limits.py`, `tests/test_existing_offer.py` | Browser and real storage-provider flow not exercised | Partial | Product/engineering records supported release path |
| Prepare/edit/compare/finalize and failed generation | `tests/test_settlement_routes.py`, `tests/test_offer_comparison.py`, `tests/test_attempt_finalization.py`, `tests/test_failure_recovery.py` | Manual review of generated files and production workflow not recorded | Partial | Product/engineering approval and scenario evidence |
| Acceptance/counteroffer/rejection and case close/reopen | `tests/test_offer_response.py`, `tests/test_case_lifecycle.py`, `tests/test_rejection_completion.py` | Browser acceptance pass not recorded | Partial | Product owner records expected outcomes and review |
| Export and permanent deletion | `tests/test_deletion.py`, `tests/test_export_delivery.py`, `tests/test_storage.py`; #167 adds external-ledger reconciliation and simulated restore tests | Production ledger initialization/IAM/versioning and real DB/object-storage restore not verified; provider-managed backups are not purged by app code | Blocked | Operations verifies ledger controls and passes a restore/deletion reconciliation exercise per Specs 44/50 |
| 5/10-credit purchase, ledger, refund | `tests/test_billing_routes.py`, `tests/test_attempt_credit_policy.py`, `tests/test_attempt_finalization.py` | Stripe test-mode transaction, webhook delivery, receipt, tax, and operational reconciliation not recorded | Blocked | Billing operator supplies evidence per Spec 49 |
| Responsive/accessibility | Static markup tests; #169 records five fictional demo routes at four widths and a keyboard-focus smoke check | No physical-device or additional-browser coverage, complete workflow keyboard pass, or screen-reader/AT test; browser/AT matrix and target remain unapproved | Partial | Product/QA approves the matrix and records complete manual findings per Spec 47 |
| Backup/restore, monitoring, alerts | `tests/test_readiness.py`, `tests/test_deletion.py`, `tests/test_storage.py`, `tests/test_failure_recovery.py`; #167 adds startup reconciliation and restore runbook | No production restore exercise, production ledger-control verification, alert-delivery test, monitoring route, or on-call owner recorded | Blocked | Operations supplies deployment evidence per Spec 50 |
| Legal boundary and AI data use | `tests/test_legal_boundaries.py`, `tests/test_ai_data_purpose.py` | Qualified counsel and current provider-term/config review not supplied | Blocked | Qualified counsel and provider/deployment owner complete Specs 51/52 evidence |

## Release decision

No product, engineering, operations, or counsel sign-off is recorded by this document. The test results establish only the listed repository behaviors; they do not prove production provider behavior, a real user journey, accessibility conformance, legal approval, or recovery capability. Do not mark the release approved while any blocking row lacks its named evidence and accountable reviewer. Issue #137 remains open until the release owner records the applicable scope, accepted limitations, sign-offs, rollback steps, and post-launch monitoring ownership.
