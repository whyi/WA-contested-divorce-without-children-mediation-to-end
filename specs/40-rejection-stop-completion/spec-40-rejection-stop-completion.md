# Spec 40: Neutral Rejection-Stop Completion

- **Status:** Implemented; focused and full-suite verification recorded below
- **Related issue:** [#131 — Add a neutral stop-after-rejection completion path](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/131)
- **Related issues:** [#123 — Mediator-only iterative offer and outcome workflow](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/123), [#126 — Reopenable case closure and complete data export](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/126), [#127 — Product legal boundaries and counsel-reviewed disclosures](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/127), [#82 — Accepted-offer completion page](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/82), and [#108 — Settlement completion actions](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/108)
- **Related specifications:** [Spec 25: Accepted Offer Completion Page](../25-accepted-offer-completion-page/spec-25-accepted-offer-completion-page.md), [Spec 28: Rejection Continuation and Negotiation Attempt Limits](../28-negotiation-attempt-limits/spec-28-negotiation-attempt-limits.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), [Spec 36: Attempt Credit Packages](../36-attempt-credit-packages/spec-36-attempt-credit-packages.md), and [Spec 37: Mediator Offer Outcome Workflow](../37-mediator-offer-outcome-workflow/spec-37-mediator-offer-outcome-workflow.md)
- **Superseded historical requirements:** No historical specification is edited. This spec supersedes only the interim rejection UI instruction to leave the offer-response view and close the case from the dashboard. Spec 37's explicit continue-or-stop decision remains in force; Spec 32 continues to define reversible, non-destructive product-case closure. Acceptance behavior in Specs 25 and 37 is unchanged. This spec does not claim that counsel has reviewed or approved the new copy.
- **Objective:** Let a user explicitly choose whether to prepare another attempt or stop after recording a rejected offer, and provide a neutral, dedicated completion page after stopping.
- **Scope:** Rejection choice controls, user-confirmed use of the existing case-close lifecycle, accessible authenticated and fictional-demo completion pages, and neutral process-boundary copy. Do not duplicate the existing offer outcome model, attempt creation endpoint, closure/reopen/export implementation, or accepted-offer completion behavior.

## Functional requirements

- **FR-40-01 — Explicit rejection choices:** After a rejection is recorded, display two unselected, explicit actions: prepare another attempt or stop mediation work and close the product case. The next attempt is created only after the user chooses the continue action. Preserve the existing attempt-limit checks and disclose the credit policy before any later finalization that may consume a credit.
- **FR-40-02 — Confirmed stop:** The stop action requires affirmative confirmation before sending the existing authenticated, CSRF-protected case-close request with reason `stopped`. Only after the server confirms closure may the app navigate to the rejection-stop completion page. Cancellation, authorization failure, or request failure must not navigate or imply closure.
- **FR-40-03 — Existing lifecycle and security:** Use the existing #126 close/reopen/export lifecycle. Do not add a competing closure API, bypass ownership authorization, weaken session/CSRF/revision checks, or automatically deliver a proposal. Preserve the case, event history, files, attempts, snapshots, and credits; reopening and export remain available as defined in Spec 32.
- **FR-40-04 — Dedicated authenticated completion:** After verified stopped closure, explain that mediation did not produce an accepted agreement in this workflow. State plainly that product workflow closure does not resolve or end the divorce case, file anything with a court, delete data, or change legal status. Provide a clear route back to the cases dashboard, where the closed case can be reopened.
- **FR-40-05 — Neutral possible next steps:** Explain that possible next steps depend on the case. Examples may include discussing options with the mediator, consulting qualified Washington counsel, or learning about court processes. Do not recommend litigation or another outcome, imply an outcome is required, or provide individualized legal advice.
- **FR-40-06 — Fictional demo:** If the fictional demo exposes rejection, show equivalent continue and stop choices and a corresponding informational completion page. Demo continuation may explain the sample's attempt limit; neither demo choice nor navigation may create or modify real case data.
- **FR-40-07 — Accessibility and responsive layout:** Use semantic headings, an accessible polite live status for verification and errors, keyboard-operable controls, visible focus, and responsive content/actions. Keep a return path available.

## Acceptance criteria

1. A recorded rejection presents both explicit choices; no attempt is created unless continue is chosen.
2. Stop requires explicit confirmation, uses the existing authorized close operation, and navigates only after successful closure.
3. The completion page is distinct from accepted-offer completion and is shown only after stopped closure is verified.
4. Product closure is clearly distinguished from legal resolution, court filing, deletion, and legal-status change; possible next steps remain neutral and non-prescriptive.
5. Case history and credits remain intact; existing reopen and export paths continue to work.
6. Where rejection is available in demo, both choices and its completion page are fictional and non-persistent.
7. Focused tests cover choice branches, explicit confirmation/closure ordering, lifecycle boundaries, legal/process copy, accessibility/status, and demo behavior.

## Implementation and verification

- Implementation: `src/app/static/index.html` reuses the offer outcome, case lifecycle, CSRF, and closed-case-list APIs; no migration or new closure endpoint is introduced.
- Tests: `tests/test_rejection_completion.py`, the authenticated/demo route test in `tests/test_main.py`, existing `tests/test_case_lifecycle.py`, and offer-response/counteroffer workflow tests.
- Validation: 73 focused workflow/lifecycle tests passed; the targeted authenticated/demo route test passed; inline JavaScript syntax and `git diff --check` passed. The full suite ran 439 tests with one known baseline failure: `test_main.MainWorkflowTests.test_theme_selection_persistence_and_shared_page_coverage` rejects the existing hard-coded `.preview-bar` values `color: #17241f` and `background: #d88a55` at its no-hex-color check. That failure concerns unchanged theme CSS and is unrelated to this spec.
- Limitation: this engineering work is not counsel review; issue #127's counsel-review requirement remains separate.
