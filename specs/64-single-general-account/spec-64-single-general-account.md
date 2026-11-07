# Spec 64: One General Account Type

- **Status:** Implemented; automated tests passing
- **Related issue:** [#240 — Use one general account type; remove attorney/paralegal accounts and case delegation](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/240)
- **Parent issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 34: Party-Owned Case with One Invited Operator at a Time](../34-party-owned-case-delegation/spec-34-party-owned-case-delegation.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), [Spec 36: Attempt Credit Packages](../36-attempt-credit-packages/spec-36-attempt-credit-packages.md)
- **Superseded historical requirements:** No historical specification is edited. This spec supersedes the Spec 34 requirements listed below and the "professional operates client cases" clause of Spec 36 FR-36-08. Spec 34 remains as the record of the removed design.
- **Objective:** Replace the party and attorney/paralegal ("professional") account types and party-to-professional delegation with one general account type. Every account owns at most one divorce case for one side only and is the only operator of that case.

## Product decision

Owner decision on 2026-11-07: remove attorney/paralegal accounts entirely and keep a single general account.

## Superseded and amended requirements

| Requirement | Disposition |
|---|---|
| Spec 34 FR-34-01 (account type, chosen at signup) | Superseded: no account-type concept exists in signup, API, or UI. |
| Spec 34 FR-34-02 (one case per party) | Retained, restated for every account (FR-64-03). |
| Spec 34 FR-34-03, FR-34-07 (professionals do not own cases; multiple client cases) | Superseded: there are no professional accounts. |
| Spec 34 FR-34-04, FR-34-05, FR-34-06, FR-34-08 (invite, accept, single delegate operator, revoke) | Superseded: delegation is removed. |
| Spec 34 FR-34-09 (isolation) | Retained: access without an active membership returns 404. |
| Spec 34 FR-34-10, FR-34-11, FR-34-12 (delegation audit, security patterns, legal-claim copy) | Superseded: they only applied to delegation. |
| Spec 34 FR-34-13, FR-34-14 (account-type/delegation UI; owner-visible delegated case) | Superseded: removed. |
| Spec 34 FR-34-15 (dashboard copy) | Amended: the dashboard no longer returns `account_type` or `delegated_to`; the plan-tier-copy removal stays. |
| Spec 36 FR-36-08 (credits and delegation) | Amended: the case's owner is its only operator; credits belong to the case and are not shared. |

## Requirements

- **FR-64-01 — One account type:** Sign-up offers no account-type choice. `POST /api/auth/signup` accepts only an email and a password. Every account is a general account.
- **FR-64-02 — No attorney or paralegal behavior:** The product has no attorney or paralegal account, invitation, or delegated-operator state. Signed-out and signed-in UI copy never refers to them.
- **FR-64-03 — One case per account:** An account may own exactly one case, counting every owned case regardless of status. A second case is refused with HTTP 409 and the message "An account can own one divorce case. Open or reopen your existing case."
- **FR-64-04 — Owner is the only operator:** Only an owner membership operates a case. Any account without an active membership receives 404. The opposing party is not a user role, workspace participant, or offer recipient.
- **FR-64-05 — Removed API surface:** `/cases/{case_id}/delegation` and `/api/v1/delegations/accept` no longer exist. `GET /api/v1/dashboard/status` no longer returns `account_type` or `delegated_to`.
- **FR-64-06 — Data migration:** Migration `0027_single_general_account` cancels open delegation invitations, revokes delegate memberships first and then lifts owner suspensions (so the single-operator unique index is never violated), and converts professional accounts to general accounts. It is idempotent and changes no schema. Legacy delegation tables and columns are retained for a later cleanup and are not used.
- **FR-64-07 — Existing privacy behavior:** Permanent account deletion still anonymizes any legacy invitation addressed to the deleted account's email.

## Acceptance criteria

1. Sign-up, sign-in, and the signed-in UI contain no account-type choice and no text referring to attorneys, paralegals, professional accounts, or delegation.
2. The delegation routes are absent from the application and the dashboard response omits `account_type` and `delegated_to`.
3. A general account creates one case; a second attempt returns the FR-64-03 message; other accounts receive 404 for that case.
4. On PostgreSQL, the migration turns a delegated case back into an owner-operated case with exactly one active operator, revokes the invitation, and converts a professional account, and a second run changes nothing.
5. The full automated test suite passes.

## Implementation boundary

This spec does not add multi-user or professional collaboration, does not change legal-advice disclaimers (tracked in #127), and does not drop legacy tables or columns. Historical evidence documents that cite the removed delegation tests are not rewritten.
