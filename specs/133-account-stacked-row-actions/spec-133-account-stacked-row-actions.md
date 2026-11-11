# Spec 133: Stacked Account Row Actions

- **Amends:** Spec 132's plan and case value presentation only. Preserve earlier
  specifications unchanged.
- **Tracking:** [#405](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/405)

## Requirements

1. Remove the visible Account information heading; retain the enclosing card
   and an accessible Account details label.
2. In the Your plan row, display the current plan above its Upgrade button.
   Right-align both. Preserve entitlement-derived plan names and checkout.
3. In the Your case row, display case status/date above the action buttons.
   Apply this to active and closed cases. Right-align the content and let
   buttons wrap on narrow screens.
4. Preserve profile rows, the bottom permanent-deletion button, and its dialog.

## Verification

Verify that plan and case action bounding boxes are below their respective
values, not beside them. Check desktop/mobile widths, hidden heading, Upgrade
expansion, case actions, and deletion-dialog regressions.
