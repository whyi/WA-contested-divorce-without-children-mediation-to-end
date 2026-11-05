# Spec 36: Free First Finalization and One-Time Attempt-Credit Packages

- **Status:** Implemented; focused tests passing; full suite has one known pre-existing failure
- **Related issue:** [#122 — Replace subscription tiers with free, 5-credit, and 10-credit attempt packages](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/122)
- **Related specifications:** [Spec 28: Rejection Continuation and Negotiation Attempt Limits](../28-negotiation-attempt-limits/spec-28-negotiation-attempt-limits.md), [Spec 29: Explicit Proposal Document Credit Consent](../29-document-credit-consent/spec-29-document-credit-consent.md), [Spec 30: Subscription Plans and Stripe Billing](../30-subscription-billing/spec-30-subscription-billing.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), [Spec 34: Party-Owned Case with One Invited Operator at a Time](../34-party-owned-case-delegation/spec-34-party-owned-case-delegation.md), [Spec 35: Attempt Finalization and Snapshot](../35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md)
- **Superseded historical requirements:** Historical specs remain unchanged. This spec supersedes:
  - Spec 28 FR-28-04 through FR-28-07 and FR-28-12/13's plan-based attempt limits and exhaustion behavior. Negotiation attempts may continue without a tier quota; a credit is consumed at finalization, not when starting an attempt.
  - Spec 29 FR-29-02/03/05/06/07/08's document-version-generation charge, generation consent, version-based debit, and trusted credit provisioning. Drafts and proposal versions are free; an attempt credit is charged atomically only at successful finalization. Spec 29's no-retroactive-charge and historical-access requirements remain, subject to the explicit legacy reset below.
  - Spec 30 in its entirety for recurring plans, monthly billing, tier entitlements, case quotas, checkout, portal, and subscription webhooks. There are no recurring tiers or monthly credit grants.
  - Spec 34 FR-34-15's compatibility-only plan fields: the dashboard API no longer exposes plan names or plan-derived case limits. The party-one-case ownership invariant remains.
  - Spec 35 FR-35-06's policy seam only: its finalization snapshot now records the case-level free-first or attempt-credit entitlement actually applied at finalization; it still introduces no separate charge.
- **Objective:** Replace plan and document-credit subscriptions with one free successful finalization per party-owned case and optional one-time packages of 5 or 10 attempt credits.
- **Scope:** Server-owned per-case attempt balance, finalization accounting, Stripe one-time checkout and verified webhook grants, package and balance UI, and a forward migration. No price points or monetary amounts are selected here.

## Definitions

- **Attempt credit:** One server-controlled entitlement to finalize one negotiation attempt. Draft creation, editing, proposal generation, re-download and delivery of the exact finalized snapshot do not use a credit.
- **Party-owned case:** The unique case owned by the party account under Spec 34. Balances and the free-first entitlement belong to this case, not to whichever professional is currently operating it.
- **Successful finalization:** The confirmed Spec 35 action that has rendered or reused the proposal, persisted the immutable snapshot, and committed the finalization transaction.
- **Package SKU:** One of two server-defined one-time package sizes, 5 or 10 credits. Its Stripe Price ID is deployment configuration and must be allow-listed.

## Functional requirements

- **FR-36-01 — Free first finalization:** Each party-owned case gets one free successful finalization. A failed or cancelled finalization does not use this entitlement. The successful action is serialized with the case lock.
- **FR-36-02 — Subsequent attempt credits:** After the free finalization, each different attempt's successful finalization costs exactly one case credit. The balance is checked and debited in the same transaction that stores the finalized snapshot. Insufficient balance, stale revisions, rendering/size errors, or commit failures leave the attempt editable and do not permanently debit a credit.
- **FR-36-03 — No charge on draft/version:** Preview, editing, proposal generation, proposal-version creation, plain downloads and delivery are free. The first finalizing action requires explicit Spec 35 confirmation. Confirmation explains whether that action is the case's free first finalization or will consume one credit and shows the current balance.
- **FR-36-04 — Snapshot reuse:** Finalizing an existing exact proposal version follows the same case entitlement rule. Repeated/concurrent finalization or re-download of the finalized snapshot (including the other format) is free and does not create another ledger entry or debit. Different terms remain rejected after finalization.
- **FR-36-05 — Packages:** Offer one-time packages of exactly 5 or 10 credits, in addition to the free first finalization. Prices and currency remain deployment/provider configured and are never guessed or hardcoded. When configuration is absent or invalid, checkout is unavailable and no success-shaped response is shown.
- **FR-36-06 — Server-controlled payment grants:** Checkout accepts only an allow-listed package SKU and an authorized case. A browser redirect, query parameter, client-supplied amount, metadata SKU, or unverified provider event never grants credits. A grant occurs only after verifying the Stripe signature, confirming a paid one-time Checkout Session, retrieving its line items from Stripe, and matching exactly one configured Price ID and quantity one.
- **FR-36-07 — Idempotent, auditable ledger:** Each successful package grant and finalization debit is recorded with case, actor, source, unique idempotency key and resulting balance. Verified webhook event receipts and Checkout Session references prevent replay/double grant. The case lock serializes finalization and package balance updates.
- **FR-36-08 — Case ownership and delegation:** The balance/free-first entitlement belongs to the party-owned case and cannot be shared with a professional's other client cases. The currently authorized case operator may purchase a package for that case; any resulting grant is case-scoped. Case creation remains governed by Spec 34: a party owns one case and a professional may operate multiple cases.
- **FR-36-09 — Close/reopen:** Credits do not expire and are preserved unchanged when a case closes or reopens, per Spec 32.
- **FR-36-10 — Legacy cutover:** The deployment cutover assumes no existing monthly subscription customers. Existing user-level document-credit balances are reset to zero, and their ledger records are retained and labeled as retired legacy document-credit history. The migration marks a case's free-first entitlement used if any attempt already has a successful Spec 35 finalization snapshot. Existing attempts, case data, offer data, case history and finalized snapshots are not deleted. Existing proposal-version rows and files may remain for audit/history and retain historical download access, but their former document-credit charges or version records do not grant, offset, or replace new-model attempt credits. Finalizing an unfinalized legacy version uses the case's current free-first state or one current attempt credit, just like any other attempt.
- **FR-36-11 — No legal claim:** Attempt-credit or payment status does not represent legal status, delivery, or acceptance.

## Acceptance criteria

1. The first successful finalization of a case records the free-first entitlement and no debit.
2. A later successful finalization with a balance of at least one records exactly one debit; an insufficient balance or any failed finalization preserves work and balance.
3. Proposal drafts/versions are free; retry, concurrency, same-snapshot downloads and the second format do not double-charge.
4. An allow-listed one-time package grants exactly 5 or 10 credits only after verified paid checkout; browser redirects and unknown/mixed/wrong-quantity SKUs grant nothing.
5. Duplicate provider events or distinct events for one Checkout Session cannot grant twice.
6. Credits are case-scoped and remain unchanged through close/reopen; professionals operating multiple cases cannot pool those balances.
7. Legacy balances are zeroed, historical ledger rows are retained as retired history, cases with previous finalized snapshots do not receive a second free-first entitlement, and no user case/history/snapshot data is deleted.
8. No recurring plan, monthly credit or plan-based case/attempt quota is offered or enforced.
9. Prices are provider/configuration supplied only; no amount is hardcoded.

## Implementation status

- The case now owns its balance and free-first flag. Migration `0020_attempt_credit_packages` resets legacy balances, retains and reclassifies the old ledger, backfills already-finalized cases, and removes recurring subscription and tier-limit columns without deleting case or proposal history.
- Stripe Checkout is one-time and SKU/Price-ID allow-listed. Only a verified, paid, idempotent webhook grants case credits.
- Proposal generation is free; the case balance is charged atomically with the Spec 35 finalized snapshot.
- Package prices remain absent until deployment configuration supplies valid one-time Stripe Price IDs.
- Limitations: no existing monthly subscription customers are assumed at cutover; future subscription records are not migrated. Checkout uses the configured Stripe Price's actual display amount and does not invent a local price.
- Verification: the new policy test first failed because the attempt-credit module did not yet exist, then passed after implementation (red/green). Focused billing, policy, finalization, export, offer-response, lifecycle and dashboard suites pass. The full suite ran 398 tests with one pre-existing failure in `test_theme_selection_persistence_and_shared_page_coverage` (`#17241f` is incorrectly treated as a six-digit theme token by its regex).
