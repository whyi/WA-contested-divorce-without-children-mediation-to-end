# Spec 131: Verified Initial Header

- **Issue:** [#404](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/404)
- **Supersedes:** Spec 125's use of readable CSRF-cookie presence as an initial
  navigation hint. Historical specifications remain unchanged.

## Requirements

1. Never show initial Account, Your case, or Log out controls solely because a
   CSRF cookie exists. Stale cookies must not flash signed-in controls when an
   anonymous visitor clicks the logo or refreshes.
2. Verify supplied access sessions with the existing server authentication
   helper before serving public home/Pricing HTML. Only a verified session
   adds the initial header marker. Reject expired/revoked sessions for that
   marker; report database failures explicitly with a retryable error.
3. Reuse protected-page verification for their initial marker; public demos
   remain unmarked. Keep the existing browser API verification and authorization.
4. Serve session-dependent HTML with Cache-Control no-store and Vary Cookie,
   Authorization. Do not expose credentials or case data in the marker.
5. Valid sessions retain immediate account navigation before the browser
   dashboard request completes. Unverified visitors keep signed-out controls.

## Verification

- Test anonymous, CSRF-only, valid, expired/revoked, and unavailable sessions.
- Observe header mutations across logo navigation, reload, and delayed API
  responses; assert no anonymous Log out flash.
- Preserve immediate valid-session header and protected-content tests.
