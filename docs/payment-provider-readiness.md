# Payment Provider Readiness Runbook

This runbook covers operational Stripe verification for the one-time attempt-credit packages. It complements [Spec 49](../specs/49-payment-provider-readiness/spec-49-payment-provider-readiness.md) and [Spec 48](../specs/48-credit-package-pricing/spec-48-credit-package-pricing.md).

## Safe setup

- Use the deployment secret manager, not source files, chat, shell history, or screenshots, for Stripe credentials.
- Keep `DEMO_MODE_ENABLED=true` until the test-mode scenarios pass.
- Configure test-mode Price IDs for active one-time USD Prices: 5 credits / $5 and 10 credits / $8. Set the account's Stripe Tax configuration and the Price tax behavior for the supported jurisdiction.
- Configure the signed webhook endpoint and exact event set described in Spec 49. Use the deployment's HTTPS origin for return URLs.
- Confirm production and test keys, Price IDs, and webhook secrets are not mixed.

## Test-mode verification

For each package, use Stripe-hosted test payment methods to verify:

1. Successful payment redirects to the app but remains pending until the signed webhook is processed; then exactly one package grant appears.
2. Declined, abandoned, expired, unpaid, and delayed-payment-failed checkouts do not grant credits.
3. Delayed-payment success grants once after provider confirmation.
4. Replaying a signed event does not create another purchase grant.
5. An unused package can receive a full refund within 30 days; a package with any consumed credit cannot be refunded.
6. Stripe Tax displays the applicable tax based on the test billing address, and Stripe sends the receipt email.
7. Purchase history, provider event, Checkout/PaymentIntent identifiers, and ledger entry reconcile without accessing or recording payment-method data.

Record only non-sensitive test evidence: environment, UTC timestamp, provider event and purchase IDs, package size, expected/actual credit delta, tax and receipt result, and reviewer. Do not record card details, secrets, or case contents.

## Production enablement and rollback

An operator must independently review production secret storage, webhook delivery, approved Price IDs and tax configuration, and the checkout disable/rollback path. Do not use a real customer charge to test production. If configuration or webhook processing is uncertain, disable checkout and reconcile pending purchases before re-enabling it; do not grant credits manually based on a browser redirect.

## Current status

Automated application tests are not provider test-mode evidence. This repository checkout has no Stripe credentials or Price IDs configured, so test-mode and production checks remain outstanding. Keep checkout disabled in any environment that has not completed and recorded the verification above.
