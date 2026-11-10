# Spec 101: Dedicated One-Time Pricing Page

- **Status:** Implemented; route and browser regressions passing
- **Related issue:** [#291 — Publish a dedicated one-time pricing page for attempt tiers](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/291)
- **Amends:** Spec 48's public pricing presentation only. Existing checkout-package amounts and purchase behavior are unchanged by this page.
- **Objective:** Present the accepted one-time attempt pricing in a dedicated public page, clearly separate from subscriptions and from the existing package checkout flow.
- **Scope:** Public `/pricing` route, pricing navigation, attempt tier descriptions, and placeholder purchase links. Billing, checkout, server entitlements, and attempt-limit enforcement are out of scope.

## Accepted pricing

| Tier | Attempts per case | Price |
|---|---:|---:|
| Free | 1 | $0 |
| Essential | Up to 3 | $5 one time |
| Pro | Up to 10 | $10 one time |

Users who need more than 10 attempts are directed to contact Casework. The pricing page does not offer a Buy now button for Free. Essential and Pro Buy now links use `href="#"` placeholders and are not connected to checkout.

## Requirements

1. `GET /pricing` serves the shared public application shell and displays a dedicated pricing view directly, without requiring navigation from the homepage.
2. The public navigation links to `/pricing`; the pricing view keeps the public sign-in and free-signup paths available.
3. The pricing view presents all three tiers, the listed prices and total attempt allowances, a no-subscription statement, and a contact prompt for needs above 10 attempts.
4. Only Essential and Pro show Buy now links; each link is an inert `#` placeholder and the page explains that checkout is not connected.
5. Pricing content is responsive and accessible, with a single page heading and clearly grouped tier cards.
6. This change does not modify payment-provider behavior, purchase catalog values, account entitlements, or server-side attempt limits.

## Acceptance criteria

1. `/pricing` returns HTTP 200 and visibly renders Free ($0, 1 attempt), Essential ($5 one time, up to 3 attempts), and Pro ($10 one time, up to 10 attempts).
2. Free has no Buy now link; the Essential and Pro links have `href="#"`.
3. The page says there are no subscriptions, explains that checkout is not connected, and directs users who need more than 10 attempts to contact Casework.
4. The Pricing navigation entry works from the public homepage.
5. Existing authentication, demo, and homepage behavior remains unchanged.
