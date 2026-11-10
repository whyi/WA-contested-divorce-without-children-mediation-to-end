# Spec 110: Lifecycle-specific accepted completion banner and actions

Tracking issue: [#348](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/348).

## Amendment

Amends [Spec 107](../107-accepted-closure-lifecycle/spec-107-accepted-closure-lifecycle.md),
[Spec 108](../108-closed-accepted-account-entry/spec-108-closed-accepted-account-entry.md)
and [Spec 109](../109-accepted-completion-progress/spec-109-accepted-completion-progress.md).
Existing specifications remain unchanged.

## Requirements

- On a verified closed accepted completion page, show the same **Closed case ·
  Read-only** banner, case-title explanation and Account link used on closed
  attempt pages, above progress navigation.
- A closed completion page has exactly one visible bottom action:
  **Open your case**. Do not display the old return link or disabled close action.
- Explicit activation reopens through the existing authenticated case lifecycle
  endpoint, with session and CSRF protections. Permit only this specific
  verified-case lifecycle action through the closed-view mutation guard;
  ordinary case/attempt mutations remain prohibited.
- Verify the returned case identity and open lifecycle before navigating to the
  latest actual attempt, without `view=closed`. Select that attempt in progress.
  Remove the Offer Accepted timeline circle for reopened permanently locked cases
  across attempt/file navigation and reloads. Preserve the saved accepted outcome
  and permanent locks; reopening never grants attempt edit or creation rights.
- Preserve the Offer Accepted circle and selected green completion step when
  reviewing an actually closed case. Account View still opens its completion page.
- An open accepted completion page has exactly two visible bottom actions:
  **Back to attempt #N**, using the latest actual attempt ordinal, and
  **Close your case**. The first is navigation only; the second retains existing
  explicit confirmation, completion prerequisites, persistence and failure handling.
- Display actions only after lifecycle and acceptance verification. A failed
  reopen stays on completion, announces the error and permits retry; never
  navigate as if reopening succeeded. Prevent duplicate in-flight reopening.
- Apply to both real-case acceptance implementations and all supported viewport
  sizes. Fictional demos remain isolated with their existing actions.

## Regression validation

- Assert the closed banner matches attempt-page text and appears above progress.
- Verify exactly one closed action versus two open actions, including direct
  completion without a closed-view parameter and later selection-based attempts.
- Exercise explicit reopen, success navigation, latest selected progress, absent
  accepted circle after reload/file navigation, preserved disabled attempt editing,
  failure/retry, duplicate clicks and invalid-success responses.
- Verify open return links do not mutate cases, both close implementations retain
  confirmation and persistence, invalid contexts expose no lifecycle action, and
  demos never call real lifecycle routes.
