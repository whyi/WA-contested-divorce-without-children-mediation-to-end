# Spec 126: Fixed Homepage Logo Destination

- **Issue:** [#389](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/389)
- **Amends:** Spec 66's logo navigation behavior. Historical specifications
  remain unchanged.

## Requirements

1. Hardcode every top-left Casework brand link to `/?view=home`, including
   the shared application header and export-provider connection result pages.
2. Do not rewrite the logo destination after session verification or depend
   on JavaScript initialization to set its destination.
3. Signed-in and signed-out logo clicks open the public homepage, including
   clicks made before session verification finishes on Pricing, Account,
   onboarding, and demo pages.
4. Preserve bare `/` direct signed-in entry and existing authorization gates.

## Verification

- Assert the literal destination in shared HTML and every provider/outcome
  connection result page.
- Hold the initial session request pending and click the logo from Pricing,
  Account, onboarding, and demos in both session states. Assert the exact URL
  and homepage content, not an account or new-case screen.
