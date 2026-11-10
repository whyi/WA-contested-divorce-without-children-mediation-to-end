# Spec 113: Your case resumes open accepted completion

Tracking issue: [#355](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/355).

## Amendment

Amends Spec 65 direct signed-in entry and Specs 106, 110 and 112 for ordinary
active-case entry. Historical specifications remain unchanged.

## Requirements

- The top-right Your case action and common signed-in active-case entry resolve
  the authorized workspace before choosing an ordinary destination.
- An open accepted case that has not been explicitly reopened resumes its
  server-provided Offer Accepted completion page rather than the last attempt.
  Support asset-attempt and selection-based acceptance, including later attempts.
- Verify case identity, open lifecycle and a same-origin completion destination
  identifying this case and an accepted offer. Completion retains its own
  acceptance verification. Lookup and validation failures remain explicit;
  never silently fall back to an attempt or mutate state.
- Preserve explicit Back to attempt navigation: direct attempt/file URLs remain
  usable and are not redirected merely because an offer was accepted.
- Preserve reopened permanently locked cases entering their latest attempt,
  even if their saved outcome is Accepted. Preserve response-only editing and
  subscription gating from Spec 112.
- Preserve nonaccepted workspace/onboarding entry, explicit start-path choice,
  Account tools, closed-case review and fictional demo isolation.

## Regression validation

- Use the actual Your case link from accepted completion, Account, public signed-in
  home and an explicitly opened attempt. Assert accepted completion is restored.
- Cover both offer implementations, first/later attempts, desktop/mobile and
  reloads without writes. Assert the completion's selected green progress remains.
- Verify explicit return navigation, reopened and nonaccepted entry and visible
  lookup/identity/destination errors without misleading navigation.
