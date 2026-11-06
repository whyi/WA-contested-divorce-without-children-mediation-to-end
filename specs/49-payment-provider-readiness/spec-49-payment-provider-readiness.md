# Spec 49: One-Time Payment Provider Readiness

- **Status:** Application behavior verified by automated tests; provider test-mode and production evidence pending
- **Related issue:** [#138 — Verify one-time payments and credit grants with the payment provider](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/138)
- **Related specifications:** [Spec 36: One-Time Attempt-Credit Packages](../36-one-time-attempt-credit-packages/spec-36-one-time-attempt-credit-packages.md), [Spec 48: Attempt-Credit Package Pricing and Purchase Terms](../48-credit-package-pricing/spec-48-credit-package-pricing.md)

## Verified application behavior

The application uses a server-owned, one-time Stripe Price catalog for the approved 5-credit USD $5 and 10-credit USD $8 packages. Checkout enables Stripe Tax, requires a billing address, and requests a provider-issued email receipt. Credits are granted only after a signed, paid, completed Checkout event whose purchase, case, customer, configured Price ID, package quantity, and tax setting are verified. Delayed payment success is supported; redirects alone grant no credits. Webhook event IDs and credit ledger entries are idempotent.

Refunds use the verified PaymentIntent reference and are limited to a full refund within 30 days when no credit from that purchase has been consumed. Service-failure credit restoration remains separate. These behaviors are covered by automated unit tests; those tests do not substitute for a live Stripe test-mode transaction.

## Operational verification gate

Before enabling checkout in a deployment, the operator must:

1. Create or verify the two active, one-time USD Prices at the approved amounts. Configure their tax behavior for the applicable jurisdiction and enable Stripe Tax in the account.
2. Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_ATTEMPT_CREDITS_5`, and `STRIPE_PRICE_ID_ATTEMPT_CREDITS_10` in the deployment secret manager. Keep demo mode enabled until the test-mode run passes; never place live credentials in source control or chat.
3. Configure the public HTTPS return origin and a signed webhook endpoint for `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, and `checkout.session.expired`.
4. In test mode, exercise a successful purchase of each package, a declined or abandoned checkout, a delayed payment success and failure where the account supports it, a duplicate webhook delivery, a refund-eligible unused purchase, and a refund rejection after package credit use.
5. Confirm each successful purchase has exactly one matching purchase-history row and credit-ledger grant; verify redirects do not grant credits. Confirm receipts are sent by Stripe and the operator can reconcile a purchase using provider and ledger identifiers without accessing payment credentials.
6. Record the test account/environment, UTC timestamps, event IDs, purchase IDs, expected and actual credit deltas, tax/receipt outcomes, and reviewer in the deployment record. Do not record card data, secrets, or case contents.
7. Review production secret storage, webhook delivery, disable/rollback procedure, and a controlled readiness check before enabling real checkout. Do not make a live customer charge as a test.

## Current evidence and limitations

The repository's automated billing tests pass, but no Stripe test or production credentials, configured Price IDs, test webhook secret, Stripe CLI, or provider transaction evidence are available in this checkout. Consequently no live test-mode or production transaction has been performed, no webhook endpoint has been verified with Stripe, and no operator reconciliation has been demonstrated. Keep issue #138 open until the deployment owner records those results. Never claim payment-provider launch readiness based only on mocked tests.
