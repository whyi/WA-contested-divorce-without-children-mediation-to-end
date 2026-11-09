# Spec 105: Homepage navigation spacing on every page

## Amendment

This specification amends the shared header requirements in
[Spec 100](../100-universal-page-chrome/spec-100-universal-page-chrome.md)
and the theme-control layout in
[Spec 80](../80-theme-selector-every-page/spec-80-theme-selector-every-page.md).
Page-specific navigation gaps, space-between distribution, and mobile grid
layouts are superseded. Existing specifications remain unchanged.

Tracking issue: [#337](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/337).

## Requirements

- The existing homepage is the spacing reference for every shared application
  header: 10 CSS pixels between adjacent visible controls above 850px viewport
  width, and 8 CSS pixels at or below 850px.
- Account, Your case, and Log out remain adjacent, in that order, with the same
  measured edge-to-edge spacing on the signed-in homepage, account, preparation,
  case/attempt, files, accepted-offer, and rejection screens.
- Public and authentication screens and both demos use the same shared spacing
  rule for their available controls. No page-specific spacing exceptions.
- Navigation is a compact, right-aligned flex group, not a stretched grid or
  space-between row. Controls may wrap on narrow screens with the shared gap;
  they must not overlap, clip, or overflow the header horizontally at 320px.
- Preserve control visibility, labels, destinations, authentication restrictions,
  theme selection, and logout behavior. Do not add account actions to anonymous
  or demo pages. Provider result popups without this navigation are unchanged.

## Regression validation

- Use the full application HTML and strict existing API fixtures.
- Measure rendered control bounding rectangles, not only CSS gap declarations.
  Compare each page with the homepage reference at the same viewport width.
- Cover anonymous authentication views, signed-in accounts with and without a
  case, both preparation modes, case assets/attempts, files, completion views,
  and every route in both demos.
- Exercise desktop, tablet, and mobile widths, including both sides of the
  850px spacing breakpoint and the existing 900px, 600px, and 420px layouts.
- Assert adjacent account buttons share a row with the reference gap, wrapped
  controls do not overlap, and all visible controls stay inside the header.
- Retain existing navigation, theme, and logout regression coverage.
