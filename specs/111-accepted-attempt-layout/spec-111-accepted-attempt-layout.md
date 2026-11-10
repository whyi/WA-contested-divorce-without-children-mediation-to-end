# Spec 111: Offer Accepted uses the attempt workspace layout

Tracking issue: [#350](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/350).

## Amendment

Amends [Spec 109](../109-accepted-completion-progress/spec-109-accepted-completion-progress.md)
and [Spec 110](../110-completion-lifecycle-actions/spec-110-completion-lifecycle-actions.md).
Existing specifications remain unchanged.

## Requirements

- Use the same dashboard section and panel shell as attempt pages: width,
  responsive padding, surface, border, radius, shadow and top spacing.
- Place the closed-case banner and shared case/progress/file navigation inside
  that shell, in the same order and responsive grid as attempt pages. Preserve
  the selected green Offer Accepted step and its fully visible outline.
- Remove the separate green completion-card layout. Relocate its heading,
  introduction, legal disclosures, status, remaining-document guidance, external
  resources, deadline guidance and lifecycle actions into the shared
  asset-analysis header/content/panel hierarchy.
- Use the attempt heading typography and content alignment. Preserve all text,
  resource links, accessible statuses, heading hierarchy and action handlers;
  layout changes must not change completion or case lifecycle behavior.
- Preserve the closed banner, single Open your case action, open-case Back to
  attempt #N / Close your case actions, reopen navigation, permanent attempt
  locks and verification/error behavior from Spec 110.
- Apply consistently to both accepted-offer implementations and fictional demos,
  without altering the separate rejected-offer completion page.
- Keep shared progress outlines unclipped across desktop/tablet/mobile layouts
  without horizontal document overflow.

## Regression validation

- Measure actual attempt and accepted-completion shell geometry, shared styles,
  navigation placement/grid, content alignment and heading typography at desktop,
  tablet and narrow mobile widths, for open and closed cases and both backends.
- Assert the standalone completion card is absent, all guidance/resources and
  lifecycle actions remain inside the shared workspace, and selected progress
  remains green, outlined and visible.
- Retain acceptance, reopen/close, historical/file navigation, failure/retry,
  account entry and demo regression coverage.
