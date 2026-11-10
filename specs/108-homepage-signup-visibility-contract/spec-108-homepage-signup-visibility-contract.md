# Spec 108: Enforce the Homepage-Only Get Started Visibility Contract

- **Status:** Implemented with automated browser regression coverage
- **Related issue:** [#360 — Enforce homepage-only Get started across auth states and session failures](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/360)
- **Related specifications:** [Spec 107: Show Get Started Only on the Signed-Out Homepage](../107-get-started-public-homepage/spec-107-get-started-public-homepage.md), [Spec 65: Direct Entry After Sign-In](../65-direct-entry-after-sign-in/spec-65-direct-entry-after-sign-in.md), and [Spec 97: Email-First Signup and Logout](../97-email-first-signup-and-logout/spec-97-email-first-signup-and-logout.md)
- **Amends:** Clarifies FR-107-01 through FR-107-05 for legacy hash authentication, verification failures, and transitions. All prior specifications remain unchanged.
- **Objective:** Display **Get started** only to verified signed-out visitors viewing the public homepage, never on an authentication screen or while signed in.
- **Scope:** Existing signup CTA visibility and regression enforcement. No authentication API, pricing, case workflow, or navigation redesign.

## Functional requirements

- **FR-108-01 — Explicit signed-out gate:** Reveal the CTA only after the homepage session check returns HTTP 401. The route must be `/` or `/?view=home`, with no authentication query or active authentication view. Ordinary public-page rendering does not establish signed-out state.
- **FR-108-02 — Authentication is not home:** Keep the CTA hidden on login, signup, verification, and password recovery, including the legacy `/#account` entry.
- **FR-108-03 — Signed-in suppression:** Keep every Get started action hidden and unavailable to keyboard focus on authenticated homepage, Account, workspace, onboarding, completion, and demo screens. Preserve Account, Your case, Logout, theme selection, and demo navigation.
- **FR-108-04 — Fail closed:** Keep the CTA hidden during pending session verification and after network errors, server failures, malformed account responses, and the `Authentication is not configured.` fallback. Preserve existing error presentation and retry behavior.
- **FR-108-05 — Authentication transitions:** Login, homepage return, reload, and Account navigation never restore the CTA for a signed-in visitor. Failed logout does not restore it. Successful logout restores it only after the destination homepage confirms sign-out.
- **FR-108-06 — Signup remains usable:** A verified signed-out homepage visitor can focus and activate Get started to reach the existing signup destination.
- **FR-108-07 — Continuous regression enforcement:** Keep browser tests in the existing entry-regressions CI job for every pull request and main-branch push. Test rendered visibility and keyboard focusability, not source-string presence alone.

## Acceptance criteria

1. `/` and `/?view=home` show a working signup action only after verified sign-out.
2. `/#account` and all authentication forms hide it at desktop, mobile, and narrow mobile widths.
3. Signed-in routes, demo routes, and existing responsive navigation retain their controls without exposing any Get started action.
4. Pending, unavailable, unconfigured, malformed, and failed session checks never expose signup.
5. Login, reload, navigation, successful logout verification, and failed logout meet the transition requirements.
6. Tests reject attempts to focus the hidden CTA and verify the visible homepage CTA remains focusable.
7. New tests reproduce the legacy-hash and unconfigured-authentication defects before the implementation fix and pass afterward.

## Implementation and verification

The existing public-page renderer requires an explicit verified-sign-out argument before revealing signup. Authentication-view and authenticated-view styles preserve hidden behavior against public-header display overrides. The existing strict Playwright fixtures continue to reject unexpected API requests, page errors, and native dialogs.

Run `npm run entry` in `uat/`. The Tests workflow runs this suite automatically, including the named **Get started visibility contract** scenarios and signup visibility assertions in the responsive navigation matrix. Repository branch protection remains a hosting/account setting; tests do not make source files immutable.
