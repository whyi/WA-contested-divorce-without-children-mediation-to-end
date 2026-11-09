# Spec 97: Minimal account entry, verified signup and visible logout

This additive specification amends spec 03's new-account verification lifecycle,
spec 65's post-signup destination, and spec 95's accepted-page spacing. Existing
specifications remain unchanged. Owner-beta restrictions and real-page access
requirements in specs 58 and 96 remain in force.

## Account entry

- Login and Get started show the same compact, theme-aware entry card: heading,
  configured Google action, email input, divider and Continue. Remove preview
  explanations, account tabs and the unrelated landing-page sections.
- Continue preserves the chosen login/signup intent, carries the entered email
  to the next form, and makes no account-discovery request. Password login offers
  an explicit create-account action; signup offers an existing-account login
  action. Do not disclose account existence from an unverified email lookup.
- Only Google is in scope. Do not show nonfunctional Apple/Microsoft actions or
  a fabricated personalized Google identity.

## Signup and verification

- Email signup collects email, first name, last name and password. Keep the
  existing server-enforced password policy and Argon2 hashing.
- A Verify email action beside the email field sends a cryptographically random
  token through configured SMTP and reveals a token input. Clearly state the
  five-minute expiration. There is no account before successful final signup.
- Store only token/proof hashes. Verification is bound to the exact normalized
  email and challenge; prevent replay and enforce expiration server-side.
  Return an existing-account login suggestion only after email possession is
  verified. Existing pending-verification accounts keep the legacy verification
  and resend endpoints.
- Enable Agree and sign up only after verification and all required fields are
  complete. Changing email or expiring verification disables it again. Reject
  missing proof, expired proof, missing/blank names and missing/false consent
  server-side, including requests using the former signup payload.
- Final signup atomically consumes proof, creates a verified account, stores
  names and versioned consent, establishes a session and opens Account.
  Migration 0029 adds nullable fields without inventing consent for old users.

## Google consent

- Clicking Google first shows the site's notices and an explicit agreement
  action. Declining returns to the preceding form without any OAuth request,
  account, identity link or provider permission request.
- Only agreement POSTs to the start endpoint. A direct GET cannot start OAuth.
  Bind pending state to an HttpOnly, SameSite=Lax browser cookie and consent
  version. The callback validates that binding before exchanging an OAuth code.
- Provider denial consumes the pending state and clears the pending cookie
  without exchanging a code or creating an account/link. Existing independent
  Google permissions are not claimed to have been revoked.
- New Google accounts record consent and open Account. Returning Google users
  preserve their existing signed-in entry destination. Existing-account linking,
  MFA, PKCE, verified-email and provider-token validation remain enforced.
- Provider access/refresh tokens are not persisted. Draft Terms and Privacy
  Notice are accessible before authentication and explicitly require counsel
  review before launch; signup is not model-training or marketing consent.

## Navigation and local validation

- Authenticated real pages and signed-in home show Log out beside Account.
  POST the existing logout endpoint with CSRF, revoke the session, clear auth
  cookies and replace the page with signed-out home. Show failures explicitly.
- Move the shared real/demo accepted page upward by removing generic section
  padding, retaining its guidance and sole Back to your case action.
- The isolated local seed provisions a separate Essential fictional account
  using the existing secret. Preserve the Free account, existing work/passwords
  and spent credits. An idempotent, clearly local-only grant enables paid
  entitlement, 100 attachments and the existing three-attempt behavior.
- Local email verification uses Mailpit, not external email delivery. Publish
  its inbox only on host loopback. Production email and Google credentials must
  be configured separately; do not pretend external integrations were tested.

## Acceptance tests

Cover narrow-screen layout, intent/back actions, consent refusal with zero
mutation requests, incorrect/expired/replayed/mismatched verification, stale UI
responses, required names, server-enforced consent, signup session/cookies and
Account destination, Google browser binding/provider denial/new-account consent,
logout revocation/CSRF, migration round-trip and idempotent Essential provisioning.
