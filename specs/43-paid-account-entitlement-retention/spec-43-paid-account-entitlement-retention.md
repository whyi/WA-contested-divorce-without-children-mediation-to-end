# Spec 43: Retain Paid Account Entitlement After One-Time Purchases

- **Status:** Implemented; focused tests passing; full suite has one known pre-existing theme-color test failure
- **Related issue:** [#133 — Disallow switching a paid account back to Free](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/133)
- **Related specifications:** [Spec 36: Free First Finalization and One-Time Attempt-Credit Packages](../36-attempt-credit-packages/spec-36-attempt-credit-packages.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md)
- **Superseded historical requirements:** Historical specifications are not edited. This spec supersedes the conflicting recurring-subscription and user-initiated tier-transition requirements in [Spec 30: Subscription Plans and Stripe Billing](../30-subscription-billing/spec-30-subscription-billing.md) and [issue #92](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/92). Spec 30's recurring tiers, renewal/expiry downgrades, tier quotas, and subscription UI do not apply to the one-time package model established by Spec 36.
- **Objective:** Preserve a server-owned paid account classification after a verified one-time attempt-credit purchase, including after the purchased case credits are consumed.
- **Scope:** Account-level paid/free classification and rejection of requests to return a paid account to Free. This spec does not add a subscription, recurring plan, price, new paid feature, or case-access rule.

## Definitions and product decision

- **Free account:** An account with no verified one-time attempt-credit package purchase in its retained purchase ledger history.
- **Paid account:** An account with at least one successful, server-verified one-time attempt-credit package purchase recorded as a positive `package_purchase` ledger entry for that account.
- Paid is a durable purchase-history classification, not a subscription tier, current balance, or statement about the legal case. Spending every credit, closing/reopening a case, or a stale browser value does not make the account Free.
- Package credits remain scoped to the case where they were purchased, as specified by Spec 36. This account classification neither moves credits between cases nor grants, removes, or gates case access.

## Functional requirements

- **FR-43-01 — Server-owned state:** The server derives Free/Paid from verified package-purchase ledger history. It does not accept a client-supplied plan, status, balance, or purchase claim as authority.
- **FR-43-02 — Durable Paid state:** Any retained positive `package_purchase` ledger entry makes the purchasing account Paid even when that case's current credit balance is zero. Finalization debits and case closure do not erase or rewrite package-purchase history.
- **FR-43-03 — Reject transition:** An authenticated request to switch an account with verified purchase history to Free returns HTTP 409 with a safe explanation. It changes no account entitlement, purchase history, credit balance, case data, or access. The account remains Paid.
- **FR-43-04 — Authorization and concurrency:** The transition endpoint requires the authenticated account and locks its server-side user row before checking purchase history. The purchase webhook uses the same account-row lock before recording a verified package grant, so stale or concurrent requests cannot erase or overlook a committed purchase. Unauthenticated requests are rejected by the existing authentication dependency.
- **FR-43-05 — UI:** Account status is read from the server. No downgrade-to-Free control is offered; stale client values are not submitted as state. The UI explains that Paid reflects purchase history, remains Paid after credits are spent, and does not change case access or credit balances.
- **FR-43-06 — No subscription behavior:** No recurring billing, monthly price, subscription expiration, tier quota, or automatic return to Free is introduced. There is no schema migration because the verified purchase ledger is the durable source of truth.
- **FR-43-07 — Case lifecycle independence:** Closing and reopening a case remains governed by Spec 32. It preserves case data and remaining credits but does not change the account's purchase-history classification.

## Acceptance criteria

1. A Free account remains Free until the server records a verified package purchase.
2. A verified purchase makes the account Paid even after all purchased credits have been consumed.
3. Authenticated downgrade requests for a Paid account return an explicit safe error without changing entitlements, credits, or access; unauthenticated requests are rejected.
4. Client-supplied state and stale requests cannot override the server-derived result. Concurrent downgrade attempts cannot change a Paid account to Free.
5. Account status display is read-only, and no UI action offers an invalid downgrade.
6. Case close/reopen behavior and the case-scoped credit balance remain independent of account status.
