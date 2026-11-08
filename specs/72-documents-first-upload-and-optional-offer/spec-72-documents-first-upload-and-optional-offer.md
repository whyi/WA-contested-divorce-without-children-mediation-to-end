# Spec 72: Documents-First Upload with an Optional Offer

- **Status:** Specified; implementation and tests in the same pull request
- **Related issue:** [#260 — Documents path: show the upload first and make the offer an optional checkbox below it](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/260)
- **Parent issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 33: Existing Offer Intake](../33-existing-offer-intake/spec-33-existing-offer-intake.md), [Spec 66: Wizard Navigation, Continue, and Signed-In Home](../66-wizard-navigation-and-home/spec-66-wizard-navigation-and-home.md), [Spec 71: Executable Signed-In Entry Contract](../71-signed-in-entry-regressions/spec-71-signed-in-entry-regressions.md)
- **Superseded historical requirements:** No historical specification is edited. For the real-account **documents** path only, this spec supersedes the requirement in Spec 33 and in the issue #175 behavior that the "Has the other party already made an offer?" question is answered and saved before any onboarding content opens. The guided-wizard path keeps that gate.
- **Objective:** Let the user upload documents immediately. The existing offer becomes an optional checkbox below the upload that only requires input when it is checked.

## Requirements

- **FR-72-01 — Upload first:** On the real documents screen (`/onboarding/upload?case_id=…`) the case-materials upload is shown as soon as the screen loads. No offer question, answer, or saved offer state hides or delays it.
- **FR-72-02 — Offer checkbox below the upload:** Below the upload and its import actions there is one checkbox, "The other party has already made an offer", unchecked by default. The radio question "Has the other party already made an offer?" is not shown on this screen. The checkbox is checked on load only when the saved offer state says an offer exists.
- **FR-72-03 — Unchecked:** With the checkbox unchecked, no offer information is required. The **Continue** action is enabled; pressing it records "no offer" (`exists = false`) when the saved state is not already that, then opens the case's attempt workspace (`/`).
- **FR-72-04 — Checked:** Checking the box shows the existing offer fields (notes and/or an offer document). **Continue** stays disabled until offer details are saved with at least notes or an offer document, and the screen says what is missing. Existing validation, upload retry, and recovery behavior for the offer are unchanged.
- **FR-72-05 — Unchecking:** Unchecking hides the offer fields and enables **Continue**. If an offer was already saved, unchecking asks for confirmation that the saved offer details will be removed, and keeps the box checked if the user declines. No stale offer is left after continuing.
- **FR-72-06 — Not a gate:** Upload, import, analysis, and review are never blocked by the offer state. Only **Continue** depends on it.
- **FR-72-07 — Create dialog:** The documents path of the new-case dialog no longer asks the offer question; it creates the case immediately with no offer answer recorded. The wizard path of the dialog is unchanged.
- **FR-72-08 — Server contract unchanged:** The existing offer API is reused as is (`GET`/`PUT /cases/{case_id}/existing-offer`); the server never requires an offer answer for other actions, and the server remains the source of truth after reload.
- **FR-72-09 — Failures and accessibility:** A failed save keeps the user on the screen with the error and does not navigate. The checkbox has a visible label, the offer fields are announced when they appear, the missing-input message is announced politely, and keyboard order is upload, offer checkbox, offer fields, Continue.
- **FR-72-10 — Unchanged surfaces:** The guided-wizard screen and its offer gate, the demos, entry routing (Spec 71), and the offer-to-asset terms feature are unchanged.

## Acceptance criteria

1. A documents-path case opens with the upload visible and the offer checkbox below it; no radio question or gate is present.
2. Unchecked: Continue is enabled and, when pressed, records no offer and opens the attempt workspace.
3. Checked: Continue is disabled until notes or an offer document are saved; then it is enabled.
4. Unchecking a saved offer confirms removal; confirming leaves no stale offer, declining restores the checkbox.
5. A reload restores the checkbox and fields from the server state.
6. The new-case dialog's documents path creates the case without asking the offer question; the wizard path is unchanged.
7. Automated tests cover the states above, and the flow was exercised in a browser against PostgreSQL.

## Implementation boundary

Client-side change only; no API, schema, or migration change. The offer panel is reused with its existing identifiers; the documents screen drives the existing saved-answer logic through the checkbox.
