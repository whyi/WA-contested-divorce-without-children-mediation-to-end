# Spec 128: Account Entry Without Homepage Flash

- **Issue:** [#397](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/397)
- **Amends:** Specs 96 and 125 for explicit Account entry presentation only.
  Historical specifications and authorization requirements remain unchanged.

## Requirements

1. Explicit `/?view=account` entry hides main content before first paint,
   then shows the existing account loading shell while verifying the session.
   Never display homepage content before a successful Account entry.
2. Keep the shared header visible and retain server session verification.
3. An ordinary Account click while Account is already displayed does not
   reload the document. Preserve modified-click/new-tab browser behavior.
4. Account refresh still verifies the session. Rejected sessions and service
   errors follow existing signed-out and retryable-error behavior without
   leaving content hidden.

## Verification

- Delay session verification during initial Account navigation and reload at
  desktop and mobile widths; assert homepage hidden and loading shell visible.
- Re-click Account and assert its content stays visible without new requests.
- Verify expired sessions and service failures clear the initial render gate.
