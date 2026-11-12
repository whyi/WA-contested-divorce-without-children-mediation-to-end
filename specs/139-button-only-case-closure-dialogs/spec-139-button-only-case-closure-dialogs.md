# Spec 139: Button-Only Case Closure Dialogs

- **Issue:** [#425](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/425)
- **Amends:** Spec 99's shared presentation for reversible case closure only.
  Preserve historical specifications.

## Requirements

1. Account, rejected-attempt, and accepted-completion case closure confirmations
   show their title, explanatory text, and exactly two controls: Cancel and the
   close-confirmation button.
2. Do not display or allow keyboard focus on a confirmation-phrase input,
   Diagnostic details textarea, Copy details button, or any other control.
   Shared field layout styles must honor each field wrapper's hidden state.
3. Keep the existing confirmation, cancellation, failure recovery, read-only
   locks, and reversible closure behavior. Do not change API contracts.
4. Permanent-deletion phrase confirmations and explicitly requested diagnostic
   dialogs retain their required fields; do not remove shared capabilities.

## Regression verification

- Verify rendered visibility, not merely the presence of a hidden attribute.
- Cover Account closure at desktop/mobile widths, rejected-attempt closure,
  and both accepted-completion backends for ordinary and reopened cases.
- Tab through an Account closure dialog and verify only its two buttons receive
  focus. Preserve existing cancellation and successful closure assertions.
