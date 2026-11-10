# Spec 125: Immediate Session Navigation

- **Issue:** [#387](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/387)
- **Amends:** Spec 96 only for public header presentation during session
  verification. Its protected-page and API authentication requirements remain
  unchanged. Historical specifications remain unchanged.

## Requirements

1. When the existing readable `auth_csrf` cookie is present and nonempty,
   render Account, Your case, and Log out while parsing the shared header,
   before the main application script and dashboard request complete. Hide
   Log in and Get started during this provisional state. Do not store account
   or case information in browser storage.
2. Cookie presence is only a navigation hint. Keep all existing server-side
   authorization and protected-content session gates. Public demo navigation
   must remain unchanged.
3. Keep homepage and Pricing navigation stable across refresh and successful
   verification at desktop, tablet, and narrow mobile widths.
4. On rejected or failed verification, clear provisional account controls.
   Expired sessions return to the existing signed-out behavior; service errors
   remain explicit and retryable. Never enable signup on an unverified session.
5. Successful logout clears signed-in navigation; failed logout preserves it
   and reports the existing retryable error.

## Verification

- Assert account controls render with the main application script disabled.
- Hold session responses pending across homepage/Pricing loads and refreshes;
  assert controls are already visible and their bounds do not change after
  successful verification at 1280, 800, 390, and 320 pixels.
- Verify expired, malformed, unavailable, and network-failed session responses
  remove provisional controls without bypassing protected-content checks.
- Preserve existing signup-visibility and failed-logout regressions.
- Mock successful logout with the API's CSRF-cookie deletion header and assert
  the cookie is gone before checking signed-out navigation with session
  verification still pending.
