# Spec 129: Account Settings Rows

- **Issue:** [#400](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/400)
- **Amends:** Spec 67's plan-card presentation. Historical specs remain intact.

## Requirements

1. Retain the existing Account colors, borders, typography, and card styling.
   List first name, last name, email, and password one item per horizontal row,
   with the label on the left and the value on the right.
2. This iteration is design-only. Do not introduce mutation APIs, fake Edit
   actions, or credential retrieval. The password row states that the password
   is not displayed for security, including for federated accounts.
3. Present Your plan, the existing plan name, and the purchase action together
   in one row. Retain the explanatory summary and package chooser below it.
4. Label the purchase action Upgrade for both free and paid accounts. Preserve
   existing package expansion and checkout behavior.
5. Keep rows usable without horizontal overflow on desktop and narrow mobile.

## Verification

- Check row order, vertical separation, right-aligned values, and long email
  wrapping at desktop and mobile widths.
- Test free/paid Upgrade labels and existing package expansion.
- Preserve profile loading/error behavior and existing plan contract tests.
