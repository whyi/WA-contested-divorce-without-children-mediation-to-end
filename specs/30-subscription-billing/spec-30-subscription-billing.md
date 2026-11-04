# Spec 30: Subscription Plans and Stripe Billing

- **Status:** In progress
- **Related issue:** [#92 — Add Stripe subscriptions and server-managed membership tiers](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/92)
- **Related specifications:** [Spec 28: Negotiation Attempt Limits](../28-negotiation-attempt-limits/spec-28-negotiation-attempt-limits.md), [Spec 29: Explicit Proposal Document Credit Consent](../29-document-credit-consent/spec-29-document-credit-consent.md)
- **Objective:** Compare a small number of clear plans and grant paid features only after the backend verifies billing-provider events.
- **Scope:** Monthly Stripe subscriptions, tier entitlements, case and negotiation limits, proposal credits, checkout, customer portal, and subscription UI. Payment provider integration is Stripe; no card data is handled or stored by the application.

## 1. Recommended launch policy

The prices below are starting experiments, not market-validated commitments. Configure real recurring Stripe Prices and display their actual amounts and billing cadence; do not hardcode money values in application source.

| Plan | Suggested monthly price | Active cases | Attempts per case | Proposal credits per billing month |
|---|---:|---:|---:|---:|
| Free | $0 | 1 | 1 | 0 |
| Essential | $19 | 3 | 3 | 2 |
| Plus | $39 | 10 | 5 | 5 |
| Pro | $79 | Unlimited | 10 | 10 |

- Keep calculation preview and editing free. A generated DOCX+XLSX proposal version costs one document credit as specified by Spec 29.
- Use monthly billing at launch. Consider annual billing only after retention and support-cost data are available.
- Monthly credits may roll over, capped at twice the plan's monthly allowance. A positive-amount paid recurring invoice tops the balance up to that cap; free-trial invoices grant no credits, and a duplicate webhook never grants credits twice. Existing credits remain usable after cancellation, but no new monthly credits are granted after expiry.
- Paid entitlements remain effective through the paid-through date when cancellation is scheduled. Immediately stop new paid entitlements after an unpaid/expired subscription; preserve read access to existing case data and generated files.
- The pricing comparison is visible when billing is not configured, but checkout actions are disabled with a clear operator-configuration message.

## 2. Functional requirements

- **FR-30-01 — Trusted tier:** Persist plan code and billing status on the user. Plan limits are derived from a server-owned catalog; client requests cannot set a plan, case limit, attempt limit, or credit amount.
- **FR-30-02 — Case allowance:** Enforce the active-case allowance on the server when creating an owned case. Count active owner workspaces, not cases the user can only view. Existing workspaces remain readable after downgrade.
- **FR-30-03 — Attempt allowance:** Use the active plan's per-case attempt allowance for every negotiation creation, transition, and export guard. Preserve legacy manually provisioned limits until a Stripe subscription takes over the entitlement.
- **FR-30-04 — Credit allowance:** On each verified successful paid recurring invoice, top the account up to at most twice that plan's monthly document-credit allowance. Record each adjustment in the credit ledger with an invoice idempotency key and resulting balance.
- **FR-30-05 — Checkout:** Authenticated users select an allow-listed plan code. The backend maps it to a configured recurring Stripe Price ID and creates a Stripe-hosted Checkout Session. The application never accepts card numbers.
- **FR-30-06 — No optimistic upgrade:** Checkout success is pending until a signed provider webhook confirms the subscription. Browser redirects, query strings, and checkout metadata do not independently grant benefits.
- **FR-30-07 — Webhook verification:** Verify Stripe signatures against the original request bytes before parsing. Store provider event IDs and process each event exactly once. Invalid signatures fail closed; duplicate events are acknowledged without repeating entitlement or credit changes.
- **FR-30-08 — Subscription lifecycle:** Process subscription creation/update/deletion and successful recurring invoices. Reject unknown price IDs. Scheduled cancellation retains tier entitlements only through the provider's paid-through timestamp.
- **FR-30-09 — Customer portal:** Create a portal session only for the authenticated account's persisted Stripe customer ID. Never accept a customer ID from the browser.
- **FR-30-10 — Comparison and status:** Display Free/Essential/Plus/Pro features, actual configured monthly price, case allowance, per-case attempts, monthly document credits, current plan, billing state, and renewal/cancellation date.
- **FR-30-11 — Billing unavailable:** When required Stripe credentials/price IDs are missing, report that subscriptions are unavailable, keep the Free tier functional, and disable checkout/portal actions without a success-shaped response.
- **FR-30-12 — Data minimization:** Persist provider IDs, status, plan, billing dates, and event IDs only. Do not retain card details or log raw billing payloads.
- **FR-30-13 — Demo isolation:** Demo mode must not create real Checkout Sessions, apply live webhook entitlements, or issue charges.

## 3. Acceptance criteria

1. The plan catalog is the only source of active limits; unauthenticated or client-modified membership requests cannot grant paid features.
2. Case creation enforces the active-case count for every tier; per-case attempt guards use the same tier catalog.
3. Checkout can be created only for a configured, allow-listed recurring Stripe Price ID.
4. No membership upgrade occurs before webhook verification and successful subscription status processing.
5. Invalid signatures are rejected; duplicate events and invoices do not duplicate plan changes or credit grants.
6. Monthly credits top up to the documented rollover cap, are auditable, and are protected from concurrent invoice replay.
7. Cancel-at-period-end, immediate expiry, failed payment, and downgrade preserve readable historical data while enforcing new-action limits.
8. The comparison page renders configured amounts, explains all included quotas, disables unavailable checkout, and does not claim a pending payment succeeded.
9. Automated tests cover every plan, case/attempt quotas, webhook signature and idempotency, billing lifecycle, credits, and demo-mode isolation.

## 4. Implementation status

- GitHub issue #92 is open and tracked in Project #5.
- Plan prices are provisional product hypotheses. Stripe Price IDs and displayed amounts are supplied by deployment configuration.
- The server-owned plan catalog, case and attempt limits, credit ledger fields, Stripe Checkout/Portal routes, signature-verified webhook handling, and plan comparison/account status UI are implemented.
- Demo mode disables Checkout, customer portal sessions, and entitlement-changing webhooks.
- Focused regression tests cover tier mapping, plan expiry, price formatting, unknown/mixed invoice prices, credit rollover caps, superseded subscriptions, and demo-mode billing isolation.
- Full automated test execution and Stripe test-mode integration verification remain deployment/CI validation tasks; no live charge was attempted.
