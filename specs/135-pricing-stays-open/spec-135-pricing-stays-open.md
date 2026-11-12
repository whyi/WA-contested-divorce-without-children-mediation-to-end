# Spec 135: Keep Pricing Open for Signed-In Users

- **Issue:** [#415](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/415)
- **Amends:** Spec 101's pricing navigation requirements.

Signed-in users can open and refresh `/pricing` without being redirected to
their case or the new-case flow after session verification. Case and account
navigation continue to work normally. Signed-out pricing remains available.

Verify navigation from an active case, session verification, and refresh with
browser regression tests.
