# Spec 118: Account Active Case Navigation

- **Issue:** [#374](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/374)
- **Amends:** Spec 65 Account navigation wording and actions only.
  Existing specifications, including Spec 100, remain unchanged.

## Requirements

1. The Account closed-case section heading is exactly **Closed case**.
   Preserve existing review, reopen and export actions.
2. Replace the generic Back to your case link with an **Active Case** button.
   Enable it only when the authenticated dashboard reports an active case.
   Otherwise disable it and announce **You have no active case.**
3. Use the existing direct-entry `openActiveCase` routing and fresh workspace
   verification: never open a closed/finalized case as active, reopen a case,
   create a case or show an intermediate case-list page.
4. Preserve working-screen, saved onboarding mode, start-choice and accepted
   completion routing, including existing accepted-case read-only locks.
5. Disable duplicate activation during loading. Announce loading and errors
   accessibly; retain Account and permit retry after verification/network
   failure, without success navigation.
6. Preserve mobile layout, keyboard access, sign-in protections and Account
   profile/plan/delete controls. No backend endpoint or schema changes.

## Regression coverage

- Desktop/mobile and keyboard navigation into started, wizard, document,
  unselected-mode and accepted cases.
- No-case/closed-only accounts, stale closed/finalized workspace, wrong-case
  response, pending request and retry after server failure.
- Exact singular heading and preserved closed-case actions.
- Keep the complete browser suite mandatory; allow a 15-minute CI job budget
  for browser installation and the expanded serial regression suite.
