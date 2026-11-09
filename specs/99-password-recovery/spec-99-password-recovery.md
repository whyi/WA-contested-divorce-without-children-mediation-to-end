# Spec 99: Locked login identity and password recovery

## Amendment

This specification amends the login and recovery interaction in
[Spec 03](../03-authentication/spec-03-authentication.md) and extends the email-first
flow in [Spec 97](../97-email-first-signup-and-logout/spec-97-email-first-signup-and-logout.md).
Existing account access,
owner-only authentication restrictions, password policy, and session revocation
requirements remain unchanged.

## Login

- Ask for an email or username once. Continue locks the identity as read-only and
  reveals the password input. Only the password is editable in this step.
- An explicit "Use a different account" action returns to identity entry and
  clears the password.
- Show "Forgot your password?" beside the login feedback, including an invalid
  email/password error. The link opens `/?auth=reset`, a separate recovery view
  using the same account form styling.

## Recovery

- Carry the entered email into recovery without putting it in the URL or
  persistent browser storage. Automatically request a code when it is a valid
  email; otherwise ask for an email before sending.
- Use the existing SMTP delivery service. Return the same generic response for
  unknown and ineligible accounts. Delivery failures must be explicit and must
  not commit an unusable code or start its resend cooldown.
- Email a high-entropy, one-time verification code. Store only its hash, expire
  it after 30 minutes, and revoke prior unused codes on successful resend.
- Permit at most one successful code issuance per account every five minutes.
  Show a countdown and a disabled "Resend verification code" button until the
  five-minute wait completes. Enforce the cooldown on the server as well.
- Display "Enter the code sent to your email" and a Verify button. Invalid or
  expired codes show a red error asking the user to retry; inputs remain usable.
- `POST /api/auth/password/verify` checks the same code eligibility as password
  reset without consuming it. Apply IP-based verification throttling that cannot
  be bypassed by submitting different codes.
- Only successful verification reveals New password, Confirm new password, and
  Update. Update starts disabled and becomes enabled when both values match and
  satisfy the field constraints (15-character minimum and 1024-character maximum).
  Server-side password policy remains authoritative.
- Changing or resending the code hides and clears the password fields and
  invalidates the browser's verified state.
- Update revalidates the code on the server, hashes the new password, consumes
  the code, revokes other recovery codes and active sessions, and returns to `/`.
  Serialize updates and resends for the same account; a consumed or revoked code
  cannot be reused.
- Failed requests show explicit feedback and preserve retryable form state.
