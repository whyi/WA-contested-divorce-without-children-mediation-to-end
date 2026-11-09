# Spec 79: Owner-Only UAT MVP Baseline

- **Status:** Product scope approved; implementation inventory recorded for follow-up
- **Related issue:** [#326 — Establish the owner-only UAT MVP baseline](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/326)
- **Related specification:** [Spec 57: Owner-Beta Environment Boundaries](../57-owner-beta-environment-boundaries/spec-57-owner-beta-environment-boundaries.md)
- **Amends:** [Spec 76](../76-remove-negotiation-planner-page/spec-76-remove-negotiation-planner-page.md), only where it removes real-account proposal comparison/editing/finalization UI and the corresponding entry behavior required by this MVP. Historical specifications remain unchanged.
- **Objective:** Establish one current, actionable MVP boundary for owner-only UAT and map its required user journey to the existing implementation without treating historical requirements as current scope.

## Product decision

On 2026-11-09, the product owner selected an owner-only UAT as the first release target. The MVP has one general account type; an account may own at most one case and is that case's only operator. The owner selected account and case access, documents and extraction, wizard intake, existing-offer intake, editable proposal comparison, mediator-facing proposal generation, case lifecycle and export, optional consent-based AI, and one-time credit purchases as MVP capabilities.

This specification is additive. It does not edit or delete historical specifications. Where this MVP conflicts with a prior requirement, this specification names the narrow supersession; otherwise prior requirements remain in effect.

## Required user journey

1. A user creates an account or signs in and opens the account's existing case, or starts its one allowed case.
2. The user uploads case materials or enters information through the guided wizard. Existing-offer details can be recorded without blocking material upload or review.
3. The user reviews extraction status, addresses files that need attention, and retries eligible failures.
4. The user reviews and edits the values used for both sides of a proposal comparison. Calculations are based on user-entered assumptions and are not legal classifications or predictions.
5. The user reviews and generates a mediator-facing proposal. A confirmed successful final download snapshots and locks that attempt; changed negotiation terms require a subsequent attempt.
6. The user may record what the mediator reports and decide whether to continue. The application does not send the proposal to the opposing party or verify delivery or response.
7. The user can close and reopen the same case, export its data, or separately request permanent deletion.
8. AI assistance is optional and requires the applicable consent and deployment readiness. Credit purchases use the approved one-time packages and remain subject to payment-provider readiness.

## Requirements

- **FR-79-01 — Release target and data boundary:** This MVP targets the owner-only UAT environment, not a public launch. UAT and local previews use synthetic case data only; real client, opposing-party, or other sensitive case materials are prohibited. UAT uses isolated resources, with payments disabled or in provider test mode and AI disabled until its independent legal/provider gates pass, as specified by [Spec 57](../57-owner-beta-environment-boundaries/spec-57-owner-beta-environment-boundaries.md).
- **FR-79-02 — Single account and case:** There is one general account type. Each account owns at most one case and is its only operator. Do not add a case list, multi-case ownership, professional account type, delegation, or shared operation. See [Spec 64](../64-single-general-account/spec-64-single-general-account.md) and [Spec 65](../65-direct-entry-after-sign-in/spec-65-direct-entry-after-sign-in.md).
- **FR-79-03 — Materials and extraction:** The user can upload, list, and delete case materials; see extraction status and actionable failures; and retry within the existing policy. Keep the approved format, size, page, OCR, retry, and concurrency limits in [Spec 42](../42-case-attachment-upload-limits/spec-42-case-attachment-upload-limits.md) and [Spec 46](../46-document-processing-limits/spec-46-document-processing-limits.md).
- **FR-79-04 — Wizard and existing offer:** The user can save wizard information and existing-offer details without creating an attempt as an implicit side effect. Preserve the documents-first entry and optional-offer behavior in [Spec 73](../73-documents-first-upload-and-optional-offer/spec-73-documents-first-upload-and-optional-offer.md) and [Spec 75](../75-direct-documents-entry/spec-75-direct-documents-entry.md).
- **FR-79-05 — Real-account proposal workflow:** The real-account UI exposes the existing proposal comparison and editing workflow needed to review both sides' values, calculate/select a scenario, and prepare a mediator-facing proposal. Do not replace real case data with demo data. Preserve server authorization, revision checks, explicit consent, credit rules, and immutable proposal versions.
- **FR-79-06 — Finalization and mediator boundary:** A confirmed successful final download snapshots and locks the attempt under [Spec 35](../35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md). The user, not the application, delivers a proposal to the mediator and reports any response. No route or copy may imply automatic delivery to the opposing party, verified receipt, legal advice, or a guaranteed result. Preserve [Spec 37](../37-mediator-offer-outcome-workflow/spec-37-mediator-offer-outcome-workflow.md).
- **FR-79-07 — Case lifecycle and deletion:** Closing remains reversible and preserves case materials, work, and credits; export remains available. Permanent deletion is an explicit, separate operation with the safeguards in [Spec 32](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md) and [Spec 44](../44-immediate-permanent-deletion/spec-44-immediate-permanent-deletion.md).
- **FR-79-08 — Optional AI:** AI is disabled by default where required by existing policy, is invoked only for its separately consented purpose, and never silently adopts suggestions. Analysis consent is not training consent. The production provider and qualified-counsel evidence gates in [Spec 51](../51-product-boundaries-counsel-review/spec-51-product-boundaries-counsel-review.md) and [Spec 52](../52-ai-data-purpose-provider-review/spec-52-ai-data-purpose-provider-review.md) remain mandatory.
- **FR-79-09 — One-time credits:** Preserve the approved one-time package terms and case-credit behavior in [Spec 48](../48-credit-package-pricing/spec-48-credit-package-pricing.md). Keep checkout in test mode and do not claim payment readiness until the provider verification in [Spec 49](../49-payment-provider-readiness/spec-49-payment-provider-readiness.md) is complete.
- **FR-79-10 — Explicit exclusions:** Multi-case accounts, professional accounts and delegation, OCR, application-to-opposing-party proposal delivery, legal advice, outcome guarantees, and public launch are not part of this MVP.
- **FR-79-11 — Readiness is not implied:** Selecting a capability for the MVP does not mean that production case-data use, live payments, counsel review, provider review, or public launch is approved. Each existing operational gate remains authoritative.

## Spec 76 supersession

This specification supersedes only:

1. Spec 76 removal contract item 1 and its explicit behavior change, insofar as they remove real-account scenario calculation, proposal comparison/editing/generation, or negotiation-attempt navigation needed for FR-79-05; and
2. Spec 76 removal contract items 2 and 3, only where their real-account entry and save-only behavior prevent the required proposal workflow from being reached.

The supersession requires restoring or verifying an authenticated real-account path to the existing server-backed proposal workflow. It does not require copying the demo interface or creating a second case, and it does not prescribe a visual redesign.

All other Spec 76 decisions remain unchanged, including fictional demo behavior, preservation of backend APIs and data, account controls, authorization, accepted-offer completion, and historical traceability. No historical specification is edited.

## Existing implementation map

This is a repository-evidence inventory, not a claim that every end-to-end browser flow has been revalidated. "Present" means the cited implementation or specification exists; regression and readiness work remains governed by the linked acceptance criteria.

| MVP area | Existing evidence | Baseline disposition |
|---|---|---|
| Account access and one case | [Spec 64](../64-single-general-account/spec-64-single-general-account.md), [Spec 65](../65-direct-entry-after-sign-in/spec-65-direct-entry-after-sign-in.md); `src/app/auth_routes.py`, `src/app/case_limits.py`, `src/app/case_access.py`; `tests/test_single_general_account.py`, `tests/test_direct_entry_after_sign_in.py` | Retain. Do not add multi-case or delegated access. |
| Materials and extraction | [Specs 42 and 46](../42-case-attachment-upload-limits/spec-42-case-attachment-upload-limits.md); `src/app/materials.py`, `src/app/extraction.py`, `src/app/extraction_worker.py`; `tests/test_materials.py`, `tests/test_extraction.py`, `tests/test_extraction_worker.py` | Retain existing limits and recovery behavior; verify the user journey against current browser entry tests. |
| Wizard and existing-offer intake | [Specs 56, 73, and 75](../73-documents-first-upload-and-optional-offer/spec-73-documents-first-upload-and-optional-offer.md); `src/app/wizard_intake.py`, `src/app/existing_offer.py`; `tests/test_wizard_intake.py`, `tests/test_existing_offer.py`, `tests/test_documents_first_offer_ui.py` | Retain save-only behavior and ensure it does not create an attempt implicitly. |
| Real-account proposal comparison and editor | [Spec 76](../76-remove-negotiation-planner-page/spec-76-remove-negotiation-planner-page.md) records removal of this frontend workflow; server-side behavior remains in `src/app/settlement_routes.py`, `src/app/settlement_planning.py`, `src/app/offer_comparison.py`; related tests include `tests/test_removed_negotiation_planner.py`, `tests/test_settlement_routes.py`, and `tests/test_offer_comparison.py` | Restore or verify the authenticated real-account UI entry and comparison/editor path under FR-79-05. Replace deletion-only UI assertions with the new MVP routing and interaction regressions; retain backend coverage. |
| Proposal output and negotiation outcome | [Specs 35 and 37](../35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md); `src/app/attempt_finalization.py`, `src/app/offer_response.py`; `tests/test_attempt_finalization.py`, `tests/test_offer_response.py` | Preserve finalization, immutability, user-reported mediator outcomes, and no-automatic-delivery semantics. |
| Close, export, and permanent deletion | [Specs 32 and 44](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md); `src/app/case_lifecycle.py`, `src/app/deletion.py`, `src/app/deletion_ledger.py`; `tests/test_case_lifecycle.py`, `tests/test_deletion.py` | Retain as separate lifecycle operations; closure is not deletion. |
| AI assistance | [Specs 51 and 52](../52-ai-data-purpose-provider-review/spec-52-ai-data-purpose-provider-review.md); `src/app/analysis.py`, `src/app/ai.py`, `src/app/settlement_ai.py`; `tests/test_ai_data_purpose.py`, `tests/test_settlement_ai.py` | Keep optional and consent-based. Production use remains gated on current provider and counsel evidence. |
| One-time credit purchases | [Specs 48 and 49](../48-credit-package-pricing/spec-48-credit-package-pricing.md); `src/app/billing_routes.py`, `src/app/attempt_credits.py`; `tests/test_billing_routes.py`, `tests/test_attempt_credit_policy.py` | Preserve approved package behavior. Test-mode UAT only until provider readiness is evidenced. |
| Demo workflows | [Spec 76](../76-remove-negotiation-planner-page/spec-76-remove-negotiation-planner-page.md); `src/app/demo.py`, demo routes and demo handlers in `src/app/static/index.html` | Preserve as fictional demos; do not use demo state as a real-account substitute. |

## Acceptance criteria

1. This specification is the current summary of MVP audience, required journey, exclusions, and operational gates.
2. Each required journey area has linked repository evidence and an explicit retain, restore/verify, or gated disposition.
3. Before the MVP is declared ready, an authenticated owner can reach the server-backed real-account proposal workflow; browser acceptance covers both values being editable, calculation/selection, proposal generation, and finalization without using demo state.
4. Attempts finalized under Spec 35 remain immutable; delivery and outcomes remain user-reported under Spec 37.
5. One account cannot operate multiple cases, and no professional/delegated account behavior is added.
6. AI, payment, counsel, provider, and data-use gates remain in force; this spec alone does not enable them.
7. Historical specifications remain unchanged, and the only Spec 76 supersession is the real-account proposal workflow and the entry behavior necessary to reach it.
8. A PR that only establishes this baseline may be documentation-only. Such a PR does not claim that functional criteria, including item 3, have been implemented or verified.

## Implementation boundary

This specification establishes the product baseline and repository map. It does not itself restore frontend behavior, change API or database contracts, authorize live payments or production case-data processing, remove historical specifications, or declare launch readiness.
