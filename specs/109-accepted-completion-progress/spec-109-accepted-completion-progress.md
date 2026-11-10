# Spec 109: Progress navigation on Offer Accepted completion

Tracking issue: [#346](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/346).

## Amendment

Amends [Spec 106](../106-accepted-case-timeline/spec-106-accepted-case-timeline.md)
and [Spec 108](../108-closed-accepted-account-entry/spec-108-closed-accepted-account-entry.md).
Existing specifications remain unchanged.

## Requirements

- Show the shared case navigation and negotiation progress circles above the
  Offer Accepted completion content.
- On completion, Offer Accepted is the single selected progress step. Reuse its
  green circle and the existing selected-step outline, including accessible
  `aria-current="step"`. The selected button does not reload the same page.
- Show actual attempts before Offer Accepted with muted past-attempt styling,
  without selecting an attempt or adding unused future attempt placeholders.
- Preserve available historical/current attempt navigation and file navigation.
  Closed cases retain `view=closed` when navigating back to saved work.
- Support asset-attempt and selection-based accepted cases, open, closed and
  reopened lifecycle states, and both fictional demos. Demo navigation remains
  local and must not mutate real cases.
- For real cases, show progress only after lifecycle and accepted-response
  verification succeeds. Preserve explicit errors, closure confirmation,
  permanent locks and completion guidance.
- Reuse shared rendering and styles rather than maintaining a second timeline.
  Keep the completion layout usable on desktop and narrow mobile screens.

## Regression validation

- Assert the progress navigation is visible above completion content.
- Assert Offer Accepted is green, outlined and the only selected step; actual
  attempts use past styling and unused future placeholders are absent.
- Cover both acceptance implementations, desktop/mobile, first/later attempts,
  open/closed/reopened cases, reloads and both demos.
- Verify available attempt/file navigation preserves closed context, invalid
  acceptance exposes no completion progress, and viewing makes no mutations.
