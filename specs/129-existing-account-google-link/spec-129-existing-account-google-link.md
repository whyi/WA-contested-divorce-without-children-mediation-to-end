# Spec 129: Connect Google to an Existing Account

- **Issue:** [#396](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/396)
- **Amends:** Spec 97's account-entry UX with the missing explicit account-link
  action. Existing authentication and owner restrictions remain unchanged.

## Requirements

1. An authenticated user can open Account and explicitly connect Google when
   the provider is configured, using their current Casework password and a
   second-factor code if enabled.
2. Use the existing authenticated, CSRF-protected link endpoint. Preserve its
   password/MFA verification, PKCE, state and nonce checks. Never merge accounts
   automatically based only on matching email addresses.
3. Offer a JSON authorization URL for requests accepting JSON; preserve the
   existing redirect response for other callers. Navigate only to the Google
   HTTPS accounts origin.
4. Show reauthentication failures in the form and allow retry. Clear password
   and second-factor inputs after each submission; never persist them.
5. Hide the link action when Google is unavailable. Successful linking retains
   the existing callback behavior and permits subsequent Google login.

## Verification

- Test JSON and redirect responses and rejection of wrong password/missing MFA.
- Browser-test the Account action, CSRF/payload, retry, cleared inputs, Google
  navigation and provider-unavailable state.
- Do not claim a real Google account was connected until its owner completes
  the password verification and Google account selection themselves.
