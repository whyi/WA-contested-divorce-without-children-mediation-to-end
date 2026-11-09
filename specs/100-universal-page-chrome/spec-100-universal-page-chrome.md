# Spec 100: Header and footer on every application page

## Amendment

This specification amends the page-shell behavior in
[Spec 12](../12-demo-entry-points/spec-12-demo-entry-points.md),
[Spec 65](../65-direct-entry-after-sign-in/spec-65-direct-entry-after-sign-in.md),
[Spec 97](../97-email-first-signup-and-logout/spec-97-email-first-signup-and-logout.md),
and [Spec 99](../99-password-recovery/spec-99-password-recovery.md).
Any previous page-specific header or footer suppression is superseded.

## Requirements

- Every user-facing application page includes a visible header before its main
  content and a visible footer after it, on desktop and mobile.
- This includes the public home, login, signup, email verification, password
  recovery, signed-in home, account, preparation, attempt, file-management,
  accepted-offer, and rejection screens, for real accounts and both demos.
- Provider connection result pages also retain header and footer landmarks,
  including success, cancellation, and verification-failure results. Preserve
  existing opener notifications, popup closure, and cache-control behavior.
- Keep the existing application header and footer. Do not invent a new footer
  design or remove existing disclosures; redesign the footer separately later.
- Page-specific navigation availability and authentication restrictions remain
  unchanged. Header/footer presence does not grant account or case access.
- The footer remains in normal document flow and can require scrolling. This
  requirement does not make either landmark fixed or sticky.

## Validation

Browser regression tests must check both landmarks across public,
authentication, signed-in, demo, and completion views at desktop and mobile
widths. Provider result tests must cover both providers and all result states.
