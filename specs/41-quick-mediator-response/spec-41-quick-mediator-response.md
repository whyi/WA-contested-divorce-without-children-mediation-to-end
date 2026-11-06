# Spec 41: Quick External Mediator Response Boundary

- **Status:** Implemented by existing behavior; this spec records the boundary and adds guarding tests. No product code change.
- **Related issue:** [#129 — Model mediator response as a quick external step, not a long-wait workflow](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/129)
- **Related issues:** [#109 — Attempt status and progress](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/109), [#123 — Mediator-only iterative offer and outcome workflow](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/123)
- **Related specifications:** [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), [Spec 35: Attempt Finalization Snapshot](../35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md), [Spec 37: Mediator Offer Outcome Workflow](../37-mediator-offer-outcome-workflow/spec-37-mediator-offer-outcome-workflow.md), [Spec 40: Neutral Rejection-Stop Completion](../40-rejection-stop-completion/spec-40-rejection-stop-completion.md)
- **Superseded historical requirements:** None; no historical spec is edited.
- **Objective:** State that the mediator normally responds quickly (about a day) outside the app, and that the user returns to record the result. Confirm the shipped flow already does this, so no new workflow is added.

## Functional requirements

- **FR-41-01 — Response entry follows sent confirmation:** In the authenticated and demo offer-response views, the "What response did you receive?" controls (counteroffer, rejected, accepted) are enabled as soon as the user confirms the documents were sent, and not before. No other step, delay, or elapsed time is required.
- **FR-41-02 — User-reported only:** The app does not deliver to or monitor the mediator. Delivery and response are the user's own report (Spec 37 `delivery` boundary, `externally_sent:false`).
- **FR-41-03 — No time inference:** Acceptance, rejection, or any outcome is never inferred from elapsed time; an outcome exists only when the user records it.
- **FR-41-04 — No waiting or follow-up workflow:** No reminder, scheduler, follow-up message, "waiting for mediator" state, or multi-week expectation exists or may be added as a core path without a separate request. The product sends no automatic follow-up.
- **FR-41-05 — Always viewable and reopenable:** A frozen, sent attempt stays viewable and the case remains closable/reopenable (Spec 32) while no response is recorded; a missing response never blocks the user.

## Acceptance criteria

1. The finalized (sent-confirmed) attempt shows response entry immediately; the fieldset is disabled only while sent confirmation is absent.
2. UI copy says the app does not deliver or verify the response and does not tell the user to wait or promise reminders.
3. No scheduler, reminder, or follow-up route or background mechanism exists in the application source.

## Implementation and verification

- Gap analysis: #109 (timeline) and #123 (outcome recording, Specs 35/37) already satisfy the issue; no UX gap was found, so no application code changed.
- Tests: `tests/test_quick_mediator_response.py` (contract assertions on the page and source, plus the `DELIVERY_BOUNDARY` read-model constant).
- Validation: see the pull request for focused and full-suite results, including the known baseline theme-check failure.
