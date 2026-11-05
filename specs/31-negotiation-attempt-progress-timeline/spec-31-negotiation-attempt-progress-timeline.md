# Spec 31: Negotiation Attempt Progress Timeline

- **Status:** Implemented
- **Related issue:** [#109 — Show clickable negotiation attempt progress on mediation page](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/109)
- **Implementation PR:** [#111 — Show negotiation attempt progress timeline](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/111)
- **Related specifications:** [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 23: Explicit Sent Confirmation Freeze](../23-explicit-sent-confirmation-freeze/spec-23-explicit-sent-confirmation-freeze.md), [Spec 28: Rejection Continuation and Negotiation Attempt Limits](../28-negotiation-attempt-limits/spec-28-negotiation-attempt-limits.md)
- **Objective:** Keep an accessible, clickable summary of negotiation attempts visible while a user prepares or reviews an offer, so they can identify its status and revisit earlier attempts.
- **Scope:** The authenticated mediation and settlement-offer workflow. Attempt creation, response recording, attempt limits, and existing attempt details remain governed by their existing workflows.

## Functional requirements

- **FR-31-01 — Persistent progression:** Display attempts in ordinal order in the mediation/offer workflow. Keep the compact progression visible while the user moves through that workflow, including on narrow screens.
- **FR-31-02 — Recorded status:** Derive each attempt's displayed status from saved attempt and offer-response history. Show a recorded counteroffer, rejection, or acceptance when present; otherwise show a prepared, editable attempt as working and a sent-confirmed attempt as pending until an outcome is recorded.
- **FR-31-03 — Current attempt:** Identify the attempt whose existing details are currently open. Update the highlight and accessible current-step indication whenever the user opens a different attempt.
- **FR-31-04 — Attempt navigation:** Make every saved attempt selectable by pointer and keyboard. Selecting one opens its existing attempt page/details without creating or changing an attempt.
- **FR-31-05 — Attempt limits and behavior:** Preserve existing attempt limits and all existing creation, freeze, response, and continuation rules. The timeline is a read-only navigation and status surface; it does not infer a response or mutate negotiation state.
- **FR-31-06 — Accessible and responsive presentation:** Use ordered-list semantics, descriptive accessible names, a programmatic current-step indication, visible keyboard focus, and a live status message for the current attempt. Keep attempt labels and statuses readable on mobile.
- **FR-31-07 — Empty and loading states:** Communicate loading and the absence of saved attempts without suggesting that an attempt exists before scenario selection.

## Acceptance criteria

1. A user can identify the currently open attempt and its state at a glance throughout the mediation/offer workflow.
2. A prepared, editable attempt is shown as working; after sent confirmation it is shown as pending until the recorded outcome changes the displayed state.
3. Recorded counteroffer, rejection, and acceptance states match the saved response history.
4. Selecting any prior attempt opens its existing details and moves the current-attempt highlight.
5. The progression remains usable at narrow viewport widths and with keyboard-only navigation, with a visible focus indicator and screen-reader status.
6. Attempt limits and the existing negotiation lifecycle are unchanged; viewing the timeline does not write data.

## Implementation status

- Implemented in PR #111 as a sticky, responsive timeline in the settlement planner.
- The timeline uses saved offer-response history, shows working/pending/recorded outcomes, highlights the currently viewed attempt, and reopens attempts through the existing history navigation.
- Existing attempt limits and negotiation transitions remain unchanged; no schema or migration changes are required.
