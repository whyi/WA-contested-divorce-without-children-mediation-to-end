# Spec 106: Accepted-case review and completion navigation

Tracking issue: [#340](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/340).

## Amendment

This specification amends
[Spec 100](../100-accepted-case-close-freezes-attempts/spec-100-accepted-case-close-freezes-attempts.md),
[Spec 105](../105-view-closed-cases-read-only/spec-105-view-closed-cases-read-only.md),
and [Spec 31](../31-negotiation-attempt-progress-timeline/spec-31-negotiation-attempt-progress-timeline.md).
Existing specifications remain unchanged. Closed-case review must not tell users
to continue the completed workflow through Next.

## Requirements

- On the last accepted attempt of a closed case, show exactly:
  **The offer was accepted. You are viewing a closed case.**
- Its Next button remains visible but disabled. Clicking or dispatching an event
  must not save a response, reopen the case, or navigate to another workflow step.
- When the latest actual attempt has a confirmed accepted offer, append one
  circular **Offer Accepted** step after that attempt in the top attempt timeline.
  Keep all saved attempts; omit unused future attempt placeholders after acceptance.
- The step opens the existing accepted-offer completion page for the correct case
  and accepted attempt. Support both asset-mediation and selection-based offers.
  Navigation is read-only and never saves the response.
- The step remains available while reviewing earlier attempts and case files.
  Keyboard activation and an accessible name identify **Offer Accepted**.
- Do not add the step for pending, unconfirmed, counteroffer, rejected, or stopped
  workflows. A closed status or query parameter alone does not prove acceptance.
- Closed-case navigation carries `view=closed` to completion and back to the
  accepted attempt. Verify the owner-accessible closed-case record before showing
  completion guidance; keep the close action disabled and preserve closure locks.
- Open accepted cases retain their existing editable/Next behavior and close
  action. Fictional accepted demos get the same timeline shortcut, but never call
  real-case endpoints.

## Regression validation

- Verify exact closed-case copy, disabled Next, and no mutations or reopening.
- Cover Free and paid cases, first and later accepted attempts, historical
  snapshots, files, reload, keyboard activation, and desktop/mobile widths.
- Verify accepted target URLs for both response implementations, including
  closed-context round trips and rejected/unconfirmed/stale access errors.
- Verify the workspace response derives acceptance from saved server state,
  not merely lifecycle status, without modifying case data.
- Verify both demos show the step only for a saved accepted response, including
  after reload, and existing open-case Next behavior remains intact.
