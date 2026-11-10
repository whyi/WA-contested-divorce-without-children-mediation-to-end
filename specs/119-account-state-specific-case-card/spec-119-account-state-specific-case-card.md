# Spec 119: State-Specific Account Case Card

- **Issue:** [#376](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/376)
- **Supersedes:** Spec 118's standalone Active Case button, no-active-case
  message and Account navigation destination. Amends Account case-action
  presentation only; existing specifications remain unchanged.

## Requirements

1. Remove the standalone **Active Case** button and **You have no active case**
   message entirely. Use **Active case** as a section heading, not a button.
2. Display an active case using the exact section/list/row/action CSS classes
   used by **Closed case**, in the same position after the plan card.
   Include the case title and exactly two card actions: **Export data** and
   **Go to attempt #N**, where N is the maximum saved attempt ordinal.
   An untouched workspace with no saved attempts starts at attempt #1.
3. If the authenticated account has an active case, show only Active case,
   not Closed case. Otherwise show Closed case only when closed records
   exist; with no case, hide both sections without an empty-state message.
4. Verify the workspace belongs to the expected case and is not closed or
   finalized before deriving the latest attempt, and verify again on navigation.
   Open `/case/assets?case_id=...&attempt=N` directly, including accepted and
   reopened cases. This Account action must not route to a completion/onboarding
   page, create/reopen a case or modify a response.
5. Reuse complete case export and its loading, error and retry handling.
   Latest-attempt lookup failures are announced accessibly, offer an explicit
   retry and never substitute an invented successful response.
6. This two-action card replaces the separate active-case action toolbar.
   Preserve case close/permanent deletion under a collapsed **Manage case**
   disclosure outside the two-action row, without a duplicate export action.
   Preserve outcome-specific Close Case, accepted closure, closed-case
   View/Reopen/Export, Account deletion, profile, billing, authentication and
   all server lifecycle/deletion APIs unchanged.
7. Preserve shared closed-card responsive layout and keyboard access. Prevent
   duplicate navigation during fresh verification.

## Regression coverage

- Desktop/mobile: shared card classes/title, exact two actions, latest ordinal,
  empty attempt history, direct attempt navigation and export ZIP download.
- Active-only, closed-only and no-case display; removal of old button/message.
- Pending lookup, server error/retry, malformed attempt ordinals, wrong case,
  stale closed/finalized workspace, and newer attempt appearing before click.
- Closed review/reopen/export, accepted/reopened locks and unchanged
  outcome-specific closure remain covered.
