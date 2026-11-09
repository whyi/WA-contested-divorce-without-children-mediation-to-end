# Spec 77: Direct guided-wizard entry

## Amendment

This additive specification supersedes Spec 33 FR-33-09's guided-start offer gate, amends FR-33-01 to collect an offer only after entering the wizard, and extends Spec 75's direct-entry behavior to the guided wizard. Spec 33's server-side offer-source validation and Spec 73's documents-first behavior remain unchanged. Prior specifications remain historical records.

## Requirements

- Selecting the guided-wizard option creates the account's case with `workflow_mode: wizard` and immediately opens `/onboarding/wizard?case_id=...`.
- No offer-answer, offer-upload, or case-creation confirmation interstitial precedes the wizard. Remove its markup, state, listeners, and dedicated copy rather than hiding it.
- Display the guided case-information questionnaire even when no offer answer is saved. Refresh and returning to an existing wizard case must behave identically.
- Existing offer editing and source validation remain available, but do not block entering or working in the wizard.
- Keep the documents path's immediate creation and upload-screen behavior.
- During creation, prevent duplicate clicks, switching paths, and cancellation. Failures remain visible on the start choice and allow retry; preserve the successfully created case for an in-page continuation retry.
- Local validation may use a separately configured, persistent fictional account and isolated database. Do not enable case APIs in demo mode, weaken secure cookies, seed production users, call AI providers, or change deployed authentication defaults.

## Verification

Browser tests cover one-click wizard entry with an unanswered offer, refresh, pending creation, failure/retry, and preserved document entry. Local integration verifies authenticated creation and persistence using HTTPS and the isolated test account.
