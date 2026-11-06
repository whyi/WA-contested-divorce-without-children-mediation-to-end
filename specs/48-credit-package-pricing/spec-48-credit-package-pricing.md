# Spec 48: Attempt-Credit Package Pricing and Purchase Terms

- **Status:** Implemented
- **Related issues:** [#140 — Set prices and purchase terms for attempt-credit packages](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/140), [#122 — Replace subscription tiers with free, 5-credit, and 10-credit attempt packages](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/122), [#125 — Failure recovery](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/125), [#138 — Payment-provider production verification](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/138)
- **Supersedes:** Spec 36's deployment-configured/provisional price language only. Spec 36's free-first finalization and case-scoped credit rules remain unchanged. Historical specifications are preserved.

## Approved product terms

- One-time purchase of **5 attempt credits for USD $5** or **10 attempt credits for USD $8**.
- Applicable tax is calculated, displayed, and collected by Stripe Tax.
- Stripe emails the payment receipt; the app stores no card or payment-method details.
- A full refund is available within 30 days only when **zero credits from that package have been used**. Once any package credit is used, that package is not refundable. Service-failure credit restoration remains separate under #125 and does not erase the package's usage history.
- Another package may be purchased only after the case's credit balance reaches zero.
- The first successful finalization per case remains free under #122. There are no monthly subscriptions.

## Requirements

1. Server catalog is authoritative for SKU, quantity, USD price, and one-time mode. Deployment-configured Stripe Price IDs must match the catalog; client input never selects an amount.
2. Checkout uses Stripe Tax automatic tax, required billing address collection, and the payer's email for Stripe's payment receipt. Checkout and pricing views disclose all terms above.
3. Only a signed, paid, completed Stripe Checkout event with a matching configured Price ID, quantity one, tax-enabled session, customer, case, and reserved purchase may grant credits. Delayed-payment success events are supported; declines, expirations, redirects, unpaid sessions, unknown prices, and duplicates grant none.
4. Package purchases and consumption are auditable. Each debit is linked to its package, and package usage is cumulative for refund eligibility.
5. Purchase history displays package, price, status, usage, and the refund deadline. Refund requests use the verified PaymentIntent reference and Stripe's idempotent refund API. Only a full, unused package within 30 days is eligible. A refund-pending package cannot be consumed; successful refunds create an immutable negative ledger entry.
6. Case row locking and a persisted pending-checkout reservation prevent concurrent top-ups while a balance is zero. Any positive balance or another pending checkout blocks checkout. Expired and declined Checkout sessions release the reservation.
7. No card numbers, security codes, or payment-method credentials are stored by this application. Production provider account setup/verification remains #138; this work does not deploy credentials.
8. Existing #122 package ledger entries are linked to historical purchase records but are marked legacy with unrecorded prices and ineligible for refunds; the migration does not invent a historical price or payment reference.

## Verification

Tests cover configured SKU/amount/quantity matching, Stripe Tax and receipt parameters, paid/unpaid/declined/delayed/duplicate webhook events, redirect non-grants, balance and pending-checkout restrictions, refund window and package-specific usage, and ledger-safe refunds.
