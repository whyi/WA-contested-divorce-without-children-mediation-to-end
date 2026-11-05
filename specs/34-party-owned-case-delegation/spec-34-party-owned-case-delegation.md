# Spec 34: Party-Owned Case with One Invited Operator at a Time

- **Status:** Implemented; automated tests passing
- **Related issue:** [#124 — Implement party-owned case with one invited operator at a time](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/124)
- **Related specifications:** [Spec 03: Authentication](../03-authentication/), [Spec 30: Subscription Plans and Stripe Billing](../30-subscription-billing/spec-30-subscription-billing.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), [Spec 33: Existing Opposing Offer Intake](../33-existing-offer-intake/spec-33-existing-offer-intake.md)
- **Superseded historical requirements:** None of the historical specs is edited. This spec supersedes, for case creation only, FR-30-02 (plan-tier active-case allowance): case count is no longer derived from the subscription plan. A party account owns exactly one divorce case (FR-34-02), and professional accounts own none. Plan catalog values for attempts and credits are unchanged. Spec 32 reopen/export and Spec 33 intake are reused, not duplicated; they are available to whichever account is the active operator.
- **Objective:** Model the divorcing party as the case owner and let that party explicitly designate one attorney or paralegal as the sole operator, revocably, without concurrent access.
- **Scope:** Account type, case ownership and creation, delegation invitation/acceptance/revocation API, case-access enforcement, audit, and a minimal UI. Not in scope: legal identity or bar verification, multi-user collaboration, firm/organization accounts, billing for professionals.

## Definitions

- **Case owner (party):** the account that created the case. A case represents one side only (Petitioner or Respondent). The owner is never replaced by a delegate.
- **Operator:** the single account currently allowed to access and act on the case: the owner, or the accepted delegate.
- **Professional account:** an account that self-declared `account_type = professional` at signup (attorney or paralegal). Declaration is not verified.

## Functional requirements

- **FR-34-01 — Account type:** Users have `account_type` of `party` (default, including all existing accounts) or `professional`, chosen at signup and immutable through the API afterwards.
- **FR-34-02 — One case per party:** A party account may own exactly one case, counting every owned case regardless of status (active, closed, finalized). A second `POST /cases` (and the materials-import case creation) is rejected with 409. The check holds a row lock on the user. Plan tier does not change this.
- **FR-34-03 — Professionals do not own cases:** Professional accounts cannot create cases (403) and are not subject to a case-count limit as operators.
- **FR-34-04 — Invitation:** Only the owner, while operating, may `POST /cases/{case_id}/delegation` with a delegate email. The delegate must be a different address from the owner. At most one pending-or-accepted invitation exists per case. A single-use random token (stored only as a SHA-256 hash, 7-day expiry) is emailed to the invitee; it is never returned by the API or written to logs/audit. If email cannot be sent the invitation is not created.
- **FR-34-05 — Explicit acceptance:** `POST /api/v1/delegations/accept` with the token, by an authenticated, active professional account whose verified normalized email equals the invited email. Signup, email match alone, or a delegate-supplied case ID never grants access; the token is required and is single use. Invalid, expired, revoked, used, or mismatched tokens return the same 404 without revealing the case.
- **FR-34-06 — Single active operator:** Acceptance creates a `delegate` membership and suspends the owner's membership in one transaction. A database partial unique index permits at most one non-revoked, non-suspended membership per case. While suspended, the owner receives 409 for every case or document route except delegation management; the delegate cannot manage delegation (403).
- **FR-34-07 — Multiple client cases:** A professional may hold delegate memberships on any number of distinct cases but never an owner membership.
- **FR-34-08 — Revocation:** The owner may `DELETE /cases/{case_id}/delegation` at any time, including while suspended, to cancel a pending invitation or revoke an accepted one. Revocation immediately sets the delegate membership's `revoked_at`, unsuspends the owner, and invalidates the token. The party can then invite another delegate. Closed cases can still be revoked.
- **FR-34-09 — Isolation:** Cross-case access by any account without an active membership returns 404. The opposing party is not a user role, workspace participant, invitee type, or offer recipient; UI copy must not imply otherwise.
- **FR-34-10 — Audit:** Invitation, acceptance, revocation, and denied acceptance are recorded in `auth_audit_events` with case ID, invitation ID, and actor only. Emails, tokens, and case content are never recorded.
- **FR-34-11 — Security patterns:** Cookie-authenticated writes require the CSRF header; case routes use the existing middleware; delegation responses use `Cache-Control: no-store`; acceptance is rate limited per account.
- **FR-34-12 — No legal claims:** The UI and API state that delegation is the party's explicit permission only and is not verification of identity or legal authority.
- **FR-34-13 — UI:** Signup offers an account-type choice. A case-delegation panel lets the owner invite, view status, and revoke; professionals have a form to accept an invitation token. Messages use live regions.

## Acceptance criteria

1. A party cannot create a second case; a professional cannot create any case.
2. A professional can accept invitations for multiple distinct cases without owning them.
3. Only an invited, token-presenting, email-matching professional can become operator; wrong email, wrong/used/expired token fail.
4. After acceptance the owner is locked out; after revocation the delegate is locked out immediately and the owner resumes.
5. Unrelated accounts cannot access the case; delegation actions are audited without secrets.

## Implementation status

- Code: `src/app/case_delegation.py`, `src/app/case_limits.py`, `src/app/main.py` (middleware), migration `0018_case_delegation`, UI in `src/app/static/index.html`.
- Tests: `tests/test_case_delegation.py`, `tests/test_case_delegation_ui.py`.
- Limitations: professional status is self-declared and unverified; the owner account is suspended (not shared) during delegation; the dashboard still displays the legacy plan case allowance text; legacy accounts that already own several cases keep them but cannot create more; delegates cannot release themselves (the party revokes); no organization or concurrent-user features.
