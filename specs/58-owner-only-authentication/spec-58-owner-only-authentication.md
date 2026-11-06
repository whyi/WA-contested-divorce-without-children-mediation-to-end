# Spec 58: Owner-Only Authentication Gate

- **Status:** Implemented as an opt-in server-side authentication restriction; UAT deployment and owner configuration are still outstanding
- **Related issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specification:** [Spec 57: Owner-Only Beta Environment Boundaries](../57-owner-beta-environment-boundaries/spec-57-owner-beta-environment-boundaries.md)
- **Objective:** Provide an explicit, fail-closed configuration that limits account creation and authentication to one designated email address, while retaining the existing email-verification and provider-verification requirements and leaving public demo behavior unchanged when disabled.

## Requirements

1. **Opt-in and explicit identity:** `OWNER_BETA_ENABLED` defaults to false. When enabled, `OWNER_BETA_EMAIL` must be a valid email address, authentication must be enabled, and demo mode must be disabled. Never hard-code the owner's address in source or commit a deployment value.
2. **Signup restriction:** Do not create or send verification email for a non-allowlisted address. Return the same generic accepted response used for signup to avoid disclosing allowlist membership.
3. **Authentication restriction:** Password, Google OIDC, MFA, passkey, access-session, and refresh-session flows must not create or continue a session for a non-allowlisted user. Normal credential and case authorization checks remain in force.
4. **Account recovery restriction:** Email verification, resend, password reset, and recovery entry points must not activate accounts, deliver recovery email, change credentials, or create a session for a non-allowlisted address.
5. **Session enforcement:** Every authenticated request re-checks the current account email against the active owner allowlist. After a deployment applies a changed owner-email configuration, the next authenticated request invalidates access through existing sessions that no longer match; access is not determined solely by claims embedded in the session token.
6. **Public demo isolation:** With owner-only mode disabled, existing local demo authentication and public browser-only Demo 1/2 behavior remain unchanged. Configuration must reject enabling owner-only mode together with demo mode.
7. **Privacy-preserving rejection:** Authentication failures use generic, non-enumerating responses and do not log the configured owner email or other secrets.
8. **No deployment claim:** Enabling this setting alone does not establish UAT isolation, HTTPS deployment, production readiness, safe integrations, or operational approval.

## Acceptance criteria

- Invalid or missing owner email, disabled authentication, or demo mode prevents owner-only mode from starting.
- A non-allowlisted signup produces no account, token, or email while returning the generic signup response.
- A non-allowlisted account cannot sign in by password, MFA, Google OIDC, or passkey and cannot use an old access or refresh session.
- Owner-allowlisted authentication continues through existing verification and MFA requirements.
- Existing authentication behavior remains unchanged when `OWNER_BETA_ENABLED=false`.
- Focused automated tests cover configuration and every distinct route family that can create or continue an authenticated session.

## Implementation boundary

The allowlist is a single deployment-injected address, intended to be the owner's verified account. No account is hard-coded or automatically created. Deployment operators must inject the owner address through protected environment configuration and keep it out of source control and logs. Hosted UAT provisioning and validation remain separate work under #209.
