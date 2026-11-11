# Spec 134: Your Case Entry Without Homepage Flash

- **Issue:** [#408](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/408)
- **Amends:** Spec 128's initial navigation render gate to include Your case.
  Preserve historical specifications.

## Requirements

1. Treat `/?view=case` as a working destination during initial HTML parsing.
   Hide main content before the application initializes, never painting the
   public homepage while authentication or destination resolution is pending.
2. At application startup show the existing account/case loading shell, then
   resolve the current case using existing authenticated APIs.
3. Preserve latest-attempt and closed/accepted-case destination checks,
   no-case creation, signed-out fallback, explicit errors, and native link
   behavior including modified clicks.
4. Apply this to direct visits, refresh, and Your case clicks from working pages.

## Verification

Test before application execution, delayed dashboard and workspace responses,
case-page navigation, refresh, no-case, signed-out, and API error states.
Observe homepage visibility through rendering frames and verify final routes.
