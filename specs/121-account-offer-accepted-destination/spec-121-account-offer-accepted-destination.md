# Spec 121: Account Offer Accepted Destination

- **Issue:** [#378](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/378)
- **Amends:** Spec 119's active-card navigation label and destination only.
  Prior specifications remain unchanged.

## Requirements

1. When the verified active workspace exposes an Offer Accepted timeline
   circle, replace **Go to attempt #N** with exactly
   **Go to offer accepted page** and open its saved accepted-completion target.
2. Use the same accepted-target validation and reopened-case rule as Spec 120:
   same origin, `/settlement-completion`, matching case ID, and an asset attempt
   or selection identifier are required. Open previously accepted/locked
   workspaces without an Offer Accepted circle retain latest-attempt navigation.
3. Re-read and verify the workspace on activation. Update the label and target
   together if acceptance has changed since rendering. Unsafe targets and
   lookup failures must show the existing accessible error/retry state and
   never navigate as though verification succeeded.
4. Preserve Active/Closed case card styling, export, closed-card actions,
   homepage final-circle navigation and accepted closure/read-only protections.
   Navigation performs no writes.

## Regression coverage

- Desktop/mobile and keyboard: ordinary/latest-attempt, asset/selection
  accepted targets, reopened locks, reload and transition before activation.
- Foreign/wrong-case/missing-context targets and stale lookup failure/retry.
- Existing Account card, export, closed-case and homepage routing contracts.
