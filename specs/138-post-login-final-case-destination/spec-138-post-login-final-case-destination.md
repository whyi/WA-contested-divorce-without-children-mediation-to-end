# Spec 138: Post-Login Final Case Destination

- **Issue:** [#423](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/423)
- **Amends:** Spec 65 FR-65-01, FR-65-03, and the closed-only entry exception
  in FR-65-07; extends Spec 123's accepted-destination precedence to automatic
  signed-in entry. Preserve historical specifications.

## Requirements

1. After successful homepage sign-in and on later default signed-in entry,
   an active case's verified `accepted_offer_url` takes precedence over its
   latest attempt, including reopened cases with persistent attempt locks.
   Asset-attempt and selection-based completion destinations follow the same rule.
2. With no active case, resolve the saved closed case through the existing
   final-circle resolver and closure checks. Open its accepted completion when
   present, otherwise its highest saved attempt, with `view=closed`. Do not
   detour through Account or reopen the case.
3. Without an accepted destination, a started active workspace continues to
   display its latest saved attempt. Preserve unfinished onboarding, explicit
   start-path and new-case requests, explicit Account navigation, and the
   new-case choice when no case exists.
4. Reuse accepted-destination validation: same origin, completion route,
   matching case identity, and an offer identifier. Invalid destinations,
   workspace failures, or stale closure state show existing explicit,
   retryable errors rather than falling back to an attempt or Account.
5. Use replace navigation. Entry must not mutate case data, clear locks,
   restore editability, consume credits, or change closure status.

## Regression verification

- Exercise actual password sign-in from the homepage, not only Your case.
- At desktop and mobile widths, verify open locked and closed accepted cases
  with asset-attempt and selection destinations, and non-accepted latest
  third-attempt destinations.
- Revisit the default root while signed in and verify the same destination.
- Check closed read-only context and no mutations other than authentication.
- Verify invalid accepted destinations, lookup failures, stale closure,
  no-case creation choice, explicit Account, and onboarding behavior.
