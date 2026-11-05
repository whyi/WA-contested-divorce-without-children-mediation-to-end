# Spec 32: Reopenable Case Closure and Complete Data Export

- **Status:** Implemented; automated tests passing
- **Related issue:** [#126 — Keep closed cases reopenable and provide complete user data export](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/126)
- **Related specifications:** [Spec 06: Secure Case Material Storage](../06-secure-case-material-storage/spec-06-secure-case-material-storage.md), [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 25: Accepted Offer Completion Page](../25-accepted-offer-completion-page/spec-25-accepted-offer-completion-page.md), [Spec 28: Rejection Continuation and Negotiation Attempt Limits](../28-negotiation-attempt-limits/spec-28-negotiation-attempt-limits.md), [Spec 29: Explicit Proposal Document Credit Consent](../29-document-credit-consent/spec-29-document-credit-consent.md), [Spec 30: Subscription Plans and Stripe Billing](../30-subscription-billing/spec-30-subscription-billing.md)
- **Superseded historical specifications:** None are edited. This spec supersedes, for closure only, any historical assumption that completing/closing a case is terminal, read-only forever, or expires the case or unused credits. Spec 25's read-only completed state applies only until the user reopens the case.
- **Objective:** Make closing, completing, or stopping a case a reversible lifecycle state distinct from deletion, and let users export all of their case data at any time.
- **Scope:** Case close/reopen, preservation of case data and credits, and a case export. Permanent deletion, retention/purge policy, and legal conclusions are out of scope and undecided. Initial-offer intake (#120) is neither depended on nor duplicated; any offer metadata stored on the case or its attempts is exported generically.

## Functional requirements

- **FR-32-01 — Reversible closure:** An owner can close a case with reason `stopped` or `closed`. Completing an accepted offer (Spec 25) closes it with reason `accepted`. Closing records `closed_at`, the reason and the pre-close status; it never deletes or alters case data, files, attempts, snapshots, generated artifacts, or credits. Closing is idempotent.
- **FR-32-02 — Reopen:** An owner can reopen a closed case at any time, including one closed by mistake. Reopening restores the saved pre-close status on the same case; it does not create a case or reset attempts. It is subject to the plan's active-case limit, which closed cases do not consume.
- **FR-32-03 — No expiry:** No calendar-based retention countdown, purge, or credit expiration is created or implied by closing. Remaining document credits are user-level and unchanged by close/reopen.
- **FR-32-04 — Closed is read-only, not final:** While closed, case writes are rejected except reopen/close; reads and export remain available. Closed cases are excluded from the active dashboard and listed by `GET /api/v1/closed-cases`.
- **FR-32-05 — Lifecycle history:** Each close and reopen is appended to a case lifecycle event record included in the export.
- **FR-32-06 — Complete export:** Any active case member can `GET /cases/{case_id}/export` at any time, with no quota or fee, receiving a ZIP archive containing `README.txt`, `manifest.json` (case profile and metadata, negotiation events, scenario runs and selections, attempts with snapshots and proposal terms, offer responses, proposal versions, consent and review records, profile facts, lifecycle events, document records, extractions, and the requester's credit balance and ledger) and `files/` with every stored case document, proposal DOCX/XLSX version, and response attachment.
- **FR-32-07 — Authorization and minimization:** Close/reopen require the owner role; export requires active membership of that case. Export contains only that case and the requester's own credit data, and omits other accounts, memberships, credentials, tokens, provider connections, storage keys, job lease tokens and destination digests. Responses are `Cache-Control: no-store`.
- **FR-32-08 — No legal claim:** Closed means the workspace is inactive, not that the legal matter is resolved or that any agreement is legally effective.

## Acceptance criteria

1. Close then reopen retains the same case id, status, attempts, files and the user's credit balance.
2. Closing creates no deletion, expiry or retention countdown.
3. A member can export repeatedly without limit; the archive includes JSON data and files and excludes the listed sensitive fields.
4. Accepted-offer completion and `stopped` closure are both reopenable.
5. Non-owners cannot close/reopen; closed cases reject other writes.

## Implementation status

- Implemented in `app/case_lifecycle.py`, `Case` closure columns, `CaseLifecycleEvent`, migration `0017_case_closure_and_events`, and changes in `app/main.py`, `app/case_limits.py` and `app/offer_response.py`.
- Limitation: close/reopen/export are API-only (no UI). Permanent deletion remains undecided.
