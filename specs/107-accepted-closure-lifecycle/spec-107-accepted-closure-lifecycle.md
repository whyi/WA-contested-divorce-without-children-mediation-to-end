# Spec 107: Accepted closure follows actual case lifecycle

Tracking issue: [#342](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/342).

## Amendment

Amends [Spec 100](../100-accepted-case-close-freezes-attempts/spec-100-accepted-case-close-freezes-attempts.md)
and [Spec 106](../106-accepted-case-timeline/spec-106-accepted-case-timeline.md).
Existing specifications remain unchanged.

## Requirements

- Determine whether a case is closed from its current server lifecycle
  (`closed_at` or finalized status), not from permanent attempt locks or an older
  response's completed flag.
- An open accepted case, including a reopened accepted case with permanently
  locked attempts, can be closed from the accepted-offer completion page after
  explicit owner confirmation.
- Re-closing must persist actual case closure before reporting success. An old
  completed flag or existing attempt lock must not produce a success-shaped
  response while leaving the case open.
- Preserve existing attempt locks, snapshots, files, credits, and accepted
  response data. Re-closing is a lifecycle operation, not permission to edit an
  accepted response or create another attempt.
- Next remains disabled for closed cases and permanently locked attempts.
  For a reopened locked case, explain that the case is open for read-only review
  and direct users to Offer Accepted to view guidance or close the case again.
- The Offer Accepted shortcut performs navigation without saving a response.
- A genuinely closed case keeps the closure action disabled with an explicit
  closed-case explanation, including when opened without `view=closed`.
- Preserve acceptance verification, owner/session/CSRF checks, confirmation,
  failure recovery, fictional demo isolation, and closed-context verification.

## Regression validation

- Exercise accept, close, reopen, and close again for both response implementations.
- Assert actual lifecycle fields, retained lock timestamp, unchanged snapshots,
  and rejected attempt mutation after reopening and re-closing.
- Browser tests cover reopened locked attempts with disabled Next and a usable
  Offer Accepted shortcut, enabled closure for an actually open case, explicit
  closed-state messaging, stale completed flags, and failure recovery.
