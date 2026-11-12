# Spec 137: Your Case Self-Navigation

- **Issue:** [#421](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/421)
- **Amends:** Spec 134 requirement 3 only. Preserve historical specifications.

## Requirements

1. When the verified final destination for the signed-in **Your case** link is
   the page currently open, activating the link must not reload the document or
   navigate through `/?view=case`.
2. Apply this to the current latest asset attempt and accepted-completion
   destination, including closed read-only views. Keep the existing final-circle
   resolution, closure verification, and accepted-destination validation.
3. If the final destination differs from the current page, preserve existing
   navigation behavior. Modified clicks retain native link behavior.
4. Do not write case data, alter read-only or accepted locks, or change case
   closure state as a result of activating **Your case**.

## Regression verification

- On a closed latest-attempt page and a closed accepted-completion page, click
  **Your case** and verify that the URL and main document remain unchanged.
- Verify that attempts to navigate from historical or other non-final pages
  still resolve to the final saved destination.
- Verify that the click performs no case mutations and preserves the closed
  read-only state.
