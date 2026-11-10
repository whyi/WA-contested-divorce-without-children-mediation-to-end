# Spec 127: Consistent Header Control Order

- **Issue:** [#391](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/391)
- **Amends:** Specs 80 and 125 for shared navigation order. Historical specs
  and existing authentication/signup visibility rules remain unchanged.

## Requirements

1. Signed-in navigation order is Theme, Pricing, Account, Your case, Log out.
2. Signed-out navigation order is Theme, Pricing, Log in, Get started wherever
   those controls are available under existing visibility rules.
3. Keep DOM, keyboard, and visual order consistent at desktop, tablet, and
   mobile widths. Theme remains first when navigation wraps and while session
   verification is pending.
4. Signed-out Pricing must not hide Theme. Preserve existing demo controls,
   authentication actions, and homepage-only signup visibility.

## Verification

- Check ordered visible controls and keyboard focus on home and Pricing for
  both session states at 1280, 800, 390, and 320 pixels.
- Verify Theme remains visually first in the existing cross-page spacing
  regressions and preserve delayed-session header rendering tests.
