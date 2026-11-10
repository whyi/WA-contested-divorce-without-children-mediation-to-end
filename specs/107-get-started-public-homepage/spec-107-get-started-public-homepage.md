# Spec 107: Show Get Started Only on the Signed-Out Homepage

- **Status:** Implemented; automated regression coverage added
- **Related issue:** [#356 — Hide Get started from signed-in visitors](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/356)
- **Related specifications:** [Spec 65: Direct Entry After Sign-In](../65-direct-entry-after-sign-in/spec-65-direct-entry-after-sign-in.md)
- **Objective:** Keep the public sign-up call-to-action limited to the public homepage for visitors whose signed-out state has been verified.
- **Scope:** Header **Get started** navigation and its visibility during startup, authentication, and logout. Sign-in, sign-up, account navigation, and case workflows remain unchanged.
- **Amendments:** This is an additive clarification. It does not alter prior specifications.

## Functional requirements

- **FR-107-01 — Public homepage only:** Show **Get started** on the root public homepage for a visitor verified as signed out.
- **FR-107-02 — Signed-in suppression:** Keep **Get started** hidden on every authenticated view, including the signed-in homepage, Account, and case workspace. It must not be keyboard-focusable while hidden.
- **FR-107-03 — Other routes:** Do not show the homepage sign-up CTA on sign-in, sign-up, verification, or password-recovery views.
- **FR-107-04 — Session verification:** Start with the CTA hidden while session state is being checked. Reveal it only after the app confirms the visitor is signed out and the current route is the public homepage. Keep it hidden when session verification fails.
- **FR-107-05 — Sign-out recovery:** After a successful sign-out and return to the public homepage, show **Get started** again.
- **FR-107-06 — Preserve existing navigation:** Do not change sign-in destinations or authenticated Account, Your case, and Logout controls.

## Acceptance criteria

1. A verified signed-out visitor sees **Get started** on `/`.
2. The CTA is hidden and not focusable on all authenticated routes and auth forms.
3. The CTA is initially hidden during session restoration and remains hidden if session status is unavailable.
4. Successful sign-out restores the CTA on the public homepage.
5. Login, signup, case entry, and authenticated header actions continue to work.
6. Browser regression tests cover homepage, auth views, authenticated routes, and sign-out.

## Implementation status

- The header CTA is hidden by default and revealed only when the signed-out homepage has been confirmed.
- Authenticated and non-home routes keep the CTA hidden with an explicit hidden-state style that cannot be overridden by public landing display rules.
- Playwright entry regressions cover signed-out homepage visibility, auth-route suppression, authenticated navigation suppression, and restoration after logout.
