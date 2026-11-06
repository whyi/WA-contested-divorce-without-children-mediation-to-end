# Spec 53: Release Acceptance Matrix and Sign-Off Evidence

- **Status:** Automated repository checks recorded; production release is not approved
- **Related issue:** [#137 — Run end-to-end release acceptance and launch sign-off](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/137)
- **Related specifications:** Specs 44, 47, 49, 50, 51, and 52
- **Objective:** Track what automated tests establish separately from browser, provider, legal, operational, and product-owner release evidence.

## Evidence from this acceptance pass

- Full unit suite on `origin/main`: 528 tests, 1 skipped, 1 known unrelated failure in `test_theme_selection_persistence_and_shared_page_coverage` because its regex rejects the existing `#17241f` theme color.
- Focused release-journey modules: 263 tests passed, 1 optional PostgreSQL test skipped. Coverage included authentication routes, case delegation, materials and attachment limits, existing-offer intake, settlement routes and comparisons, attempt finalization, offer response, case lifecycle, rejection completion, permanent deletion, export, storage, billing/credit policy, AI-purpose and legal-boundary gates, readiness, failure recovery, PDF extraction, and document limits.
- Python compilation and `git diff --check` passed.
- This was a set of automated unit/route tests, not a single browser-driven end-to-end test against a production-like deployment.

## Release matrix

| Area | Automated repository evidence | Manual/provider evidence | Status | Required owner/evidence |
|---|---|---|---|---|
| Sign-up, sign-in, recovery, authorization, single operator | `tests/test_auth_routes.py`, `tests/test_case_delegation.py` | Real email delivery, production identity configuration, and full browser journey not exercised | Partial | Release operator records deployment and end-to-end results |
| Wizard/materials intake, offer capture, quotas | `tests/test_materials.py`, `tests/test_attachment_limits.py`, `tests/test_existing_offer.py` | Browser and real storage-provider flow not exercised | Partial | Product/engineering records supported release path |
| Prepare/edit/compare/finalize and failed generation | `tests/test_settlement_routes.py`, `tests/test_offer_comparison.py`, `tests/test_attempt_finalization.py`, `tests/test_failure_recovery.py` | Manual review of generated files and production workflow not recorded | Partial | Product/engineering approval and scenario evidence |
| Acceptance/counteroffer/rejection and case close/reopen | `tests/test_offer_response.py`, `tests/test_case_lifecycle.py`, `tests/test_rejection_completion.py` | Browser acceptance pass not recorded | Partial | Product owner records expected outcomes and review |
| Export and permanent deletion | `tests/test_deletion.py`, `tests/test_export_delivery.py`, `tests/test_storage.py` | Production S3 versions, DB backup restore, and deletion reconciliation not exercised; pre-deletion restore can omit later tombstones | Blocked | Operations documents backup inventory and passes restore/deletion reconciliation exercise |
| 5/10-credit purchase, ledger, refund | `tests/test_billing_routes.py`, `tests/test_attempt_credit_policy.py`, `tests/test_attempt_finalization.py` | Stripe test-mode transaction, webhook delivery, receipt, tax, and operational reconciliation not recorded | Blocked | Billing operator supplies evidence per Spec 49 |
| Responsive/accessibility | Static/UI assertions in repository tests | Viewport, keyboard, screen reader, and assistive-technology checks not completed | Blocked | Product/QA records approved matrix and manual findings per Spec 47 |
| Backup/restore, monitoring, alerts | `tests/test_readiness.py`, `tests/test_deletion.py`, `tests/test_failure_recovery.py` | No production backup restore, alert-delivery test, monitoring route, or on-call owner recorded | Blocked | Operations supplies evidence per Spec 50 |
| Legal boundary and AI data use | `tests/test_legal_boundaries.py`, `tests/test_ai_data_purpose.py` | Qualified counsel and current provider-term/config review not supplied | Blocked | Qualified counsel and provider/deployment owner complete Specs 51/52 evidence |

## Release decision

No product, engineering, operations, or counsel sign-off is recorded by this document. The test results establish only the listed repository behaviors; they do not prove production provider behavior, a real user journey, accessibility conformance, legal approval, or recovery capability. Do not mark the release approved while any blocking row lacks its named evidence and accountable reviewer. Issue #137 remains open until the release owner records the applicable scope, accepted limitations, sign-offs, rollback steps, and post-launch monitoring ownership.
