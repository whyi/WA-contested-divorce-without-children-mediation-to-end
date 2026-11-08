# Spec 66: Wizard Navigation, Continue, and Signed-In Home

- **Status:** Implemented; automated tests passing
- **Related issues:** [#243 — Wizard Back returns to the start-path choice instead of the Account page](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/243), [#244 — Wizard Save and continue opens the case's attempt screen](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/244), [#245 — Casework logo opens the home page when signed in](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/245)
- **Parent issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 56: Account-Backed Wizard Intake Draft](../56-account-backed-wizard-intake/spec-56-account-backed-wizard-intake.md), [Spec 65: Direct Entry After Sign-In](../65-direct-entry-after-sign-in/spec-65-direct-entry-after-sign-in.md)
- **Superseded historical requirements:** No historical specification is edited. This spec amends Spec 65 FR-65-01 and FR-65-06 and supersedes the wizard "return" behavior and Account-area back link described there. Spec 56 requirement 7 (do not navigate after a failed save) is retained.
- **Objective:** Make the real-account wizard move forward and back sensibly, and give signed-in users a way to reach the home page.

## Requirements

- **FR-66-01 — Back to the start choice:** On a real case's guided-wizard and documents screens, the "Back to your account" link is replaced by **Back**, which opens the "How would you like to start?" choice (documents or guided wizard). Choosing the current path or cancelling closes it with no change. Choosing the other path changes the case's start path and opens that path's screen; saved case information is kept. This amends Spec 65 FR-65-06.
- **FR-66-02 — Start-path API:** `PUT /cases/{case_id}/workflow-mode` with `{"workflow_mode": "upload" | "wizard"}` changes the case's start path. It requires the authenticated case owner (404 without membership, 403 for a non-owner member), rejects unknown paths and extra fields, is refused on a closed case by the existing lifecycle check, returns a retryable 503 on database failure without partial change, and leaves every other case field untouched.
- **FR-66-03 — Continue:** When the required intake is complete (filed status answered and party role chosen), the wizard's finish button reads **Save and continue**. After a successful server save it opens the app entry, which shows the case's attempt screen. A failed save keeps the user on the wizard and shows the error. The wizard states when the button becomes available.
- **FR-66-04 — Entry for a completed wizard:** The entry decision in Spec 65 FR-65-01 opens the attempt (settlement planning) screen for a wizard case whose saved intake is complete (`filed = "yes"` and a party role), and the wizard otherwise. Cases without a start path keep opening the attempt screen. The attempt screen of a case with a start path shows **Edit case information**, which opens the wizard or documents screen.
- **FR-66-05 — No demo links in real cases:** The real-account wizard does not show the demo-only "Back to Asset Overview" link.
- **FR-66-06 — Signed-in home:** While signed in, the Casework logo opens the public home page at `/?view=home` without redirecting to the case. There, the header's account control and the home page's calls to action read "Your case" / "Open your case" and lead to `/`, the sign-up panel is hidden, and Account stays available. Signed-out visitors and demos keep the logo's `/` behavior. Sign-in and visiting `/` still follow Spec 65.

## Acceptance criteria

1. Back opens the start choice; choosing documents or wizard changes the case and opens that screen, and a later visit to `/` opens the chosen path; choosing the current path or cancelling changes nothing.
2. The start-path API enforces ownership, validation, and the closed-case rule and reports failures without navigating.
3. After the wizard's required answers, Save and continue saves, then opens the attempt screen; a later visit to `/` opens it directly and its Edit case information link returns to the wizard.
4. The logo opens the signed-in home page with the case-oriented calls to action; signed-out and demo behavior is unchanged.
5. Automated tests cover the API and the screen wiring; the flows were also exercised in a browser against PostgreSQL with object storage.

## Implementation boundary

No new wizard questions, no change to the attempt screen's content, and no change to the documents path's next step. Moving data between the two start paths is not performed.
