# Spec 96: Session-gated real working pages

This additive specification amends specs 65, 87, 93 and 95. Prior specifications
remain unchanged.

- Anonymous users may view the homepage and public Demo 1/Demo 2 pages.
  Login/signup/recovery endpoints remain available. Public demo behavior does
  not grant access to real case data.
- Before serving real `/case/*`, `/onboarding/*`, `/settlement-completion` and
  `/rejection-completion` pages, verify the existing authenticated user/session
  helper, including token, session expiry/revocation, active user and deletion
  checks. Do not treat mere cookie presence as authentication.
- Missing, invalid or expired authentication redirects to bare `/`, removing
  case/query context. Do not serve working-page HTML first. Protected page
  responses and redirects use `Cache-Control: no-store`.
- Browser startup keeps working content hidden until authenticated status is
  verified. Completion-page initialization checks authentication before
  rendering. A restored back/forward-cache working page reloads and rechecks
  the session, redirecting signed-out users to `/`.
- Session/database verification failures fail closed with an explicit logged,
  retryable error; do not render case content or silently treat backend failure
  as a valid session. Existing API authentication/error semantics remain.
- Verify all real page URLs, query/trailing slash forms, active/expired/revoked/
  invalid/deleted sessions, public demos/home, database errors and browser
  history restoration. Read-only shared configuration attachments are untouched.
