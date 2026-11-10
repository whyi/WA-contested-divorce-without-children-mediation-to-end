# Spec 122: Accepted Account Links Preserve Reopened Locks

- **Issue:** [#378](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/378)
- **Amends:** Spec 121 requirements 1 and 2: the Account accepted-page
  destination is based on the saved accepted target, regardless of an existing
  accepted-case attempt lock. Prior specifications remain unchanged.

## Requirements

1. If an active workspace exposes a valid `accepted_offer_url`, the Account
   card must show **Go to offer accepted page** and navigate there, even when
   `attempts_locked_at` is set and the current response is completed.
2. Do not equate an existing read-only lock with a rejected or missing accepted
   response. When the saved accepted target is absent, retain **Go to attempt
   #N**. Revalidate the target and current workspace on activation.
3. Keep all existing locks, read-only rules, closed-card actions and same-origin
   target checks. Navigation must not mutate case data or clear a lock.
   The homepage's existing reopened-case timeline routing is unchanged.

## Regression coverage

- Reproduce the reported combination: open/non-finalized case, third attempt,
  sent/accepted/completed response, existing case and response locks, and a
  saved accepted target. Verify label, reload, keyboard navigation and retained
  locks at desktop/mobile widths for both asset and selection targets.
- Reopened nonaccepted cases without a saved target still link to their latest
  attempt; recheck acceptance changes and invalid targets without writes.
- Verify the actual authenticated served Account page without substituting
  acceptance or lock state with isolated fixtures.
