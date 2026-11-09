# Spec 108: Closed attempt styling and accepted-case Account entry

Tracking issue: [#344](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/344).

## Amendment

Amends [Spec 106](../106-accepted-case-timeline/spec-106-accepted-case-timeline.md)
and [Spec 107](../107-accepted-closure-lifecycle/spec-107-accepted-closure-lifecycle.md).
Existing specifications remain unchanged.

## Requirements

- Every actual attempt in a closed case, including the last attempt, uses the
  existing muted gray past-attempt circle styling, not the green current-attempt
  styling. Apply this on attempt and file pages, including when actual server
  lifecycle identifies closure without a closed-view query.
- Preserve the selected-step outline, historical navigation, disabled controls,
  and the separate Offer Accepted shortcut. Describe the closed timeline as
  read-only rather than labeling the final attempt as current.
- Account's closed-case View action opens a case closed by acceptance directly
  on its server-provided Offer Accepted completion page. Support both asset
  attempt and selection-based acceptance, including later attempts.
- Resolve the destination on explicit View activation. Verify the workspace
  matches the listed closed case, closure timestamp and accepted reason, and
  that the destination is this case's same-origin completion page.
- Carry `view=closed` to completion; retain completion's existing accepted-offer
  verification and disabled closure action. Viewing must not reopen, close, save,
  or otherwise mutate the case.
- If lookup fails or the accepted destination cannot be verified, stay on Account,
  display an explicit error and allow retry. Do not silently fall back to an
  attempt page.
- Non-accepted closed cases retain their existing read-only attempt/file entry.
  Active-case entry and fictional demos remain unchanged.

## Regression validation

- Reproduce incorrect current-marker styling and Account destination before fixing.
- Check closed first/later attempts at desktop and mobile widths, including
  computed equality of earlier and final circle background, border and text colors.
- Check Account View for both acceptance implementations at desktop and mobile
  widths, direct completion routing, disabled closure, and absence of mutations.
- Cover missing accepted destinations, mismatched case identity, stale closure,
  reopened lifecycle and foreign destinations with visible errors and retry.
- Preserve the non-accepted closed-case View, historical navigation and file tests.
