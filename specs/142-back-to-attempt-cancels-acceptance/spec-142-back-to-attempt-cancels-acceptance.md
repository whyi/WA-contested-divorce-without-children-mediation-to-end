# Spec 142: Back to Attempt Cancels Acceptance

- **Issue:** [#431](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/431)
- **Amends:** Specs 106, 109, 136, and 141 for the explicit bottom return action.
  Preserve prior specifications and ordinary timeline navigation.

## Requirements

1. On an open real case's Offer Accepted page, the bottom **Back to attempt #N**
   action clears the latest saved Accepted response before navigating to that
   attempt. After navigation and reload, no outcome is selected and the Offer
   Accepted shortcut is absent.
2. Apply this to both asset-mediation and selection-based accepted responses.
   The existing shared attempt workspace must allow choosing a response again.
3. This also applies after reopening, but never clears permanent attempt locks
   or proposal freezes. Retain the existing response-only editing boundary.
4. Preserve confirmed delivery, proposal values, snapshots, files, notes,
   attempt ordinals, credits, and closure history. Do not create a new attempt.
5. Numbered timeline steps remain read-only navigation and do not clear
   acceptance. Preserve closed-case review and the separate explicit reopening
   action. Fictional demo return navigation remains unchanged.
6. Require authorized case access, the latest attempt, an accepted confirmed
   response, an open case, and the expected revision. Serialize cancellation
   against case writes. A successful retry must not clear a newer decision.
7. Disable duplicate submissions and conflicting close actions while saving.
   Navigate only after the response confirms an unset outcome for the expected
   attempt and retains any permanent locks. On errors, remain on completion,
   report the failure, and restore the controls.

## Regression verification

- Cover both offer implementations, open/reopened states, and desktop/mobile.
- Verify one mutation despite repeated clicks, no navigation before save,
  the selected attempt's green circle, unselected enabled response choices,
  missing accepted shortcut after reload, and retained locks and snapshots.
- Exercise rejected stale requests, historical/closed attempts, proposal-field
  tampering, database failures, invalid success responses, and safe retries.
- Preserve existing completion, closed-case, and timeline-only regressions.
