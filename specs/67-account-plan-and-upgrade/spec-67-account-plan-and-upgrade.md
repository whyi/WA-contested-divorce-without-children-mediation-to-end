# Spec 67: Account Plan and Upgrade Action

- **Status:** Implemented; automated tests passing
- **Related issue:** [#246 — Show the account plan and an upgrade action in the Account area](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/246)
- **Parent issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 36: Free First Finalization and One-Time Attempt-Credit Packages](../36-attempt-credit-packages/spec-36-attempt-credit-packages.md), [Spec 65: Direct Entry After Sign-In](../65-direct-entry-after-sign-in/spec-65-direct-entry-after-sign-in.md)
- **Superseded historical requirements:** No historical specification is edited. This spec amends Spec 65 FR-65-07 by adding a plan card to the Account area. It does not change Spec 36: there are still no recurring subscriptions or tiers.
- **Objective:** Show the account's plan in the Account area with an action on the right to upgrade or buy more credits.

## Product note

The product has no recurring subscription. An account is **Free** until a verified one-time attempt-credit package is purchased and then stays **Paid**; a paid account cannot switch back to Free. The Account area therefore reports that real entitlement and offers the one-time packages.

## Requirements

- **FR-67-01 — Plan card:** The top of the Account area shows a labelled "Your plan" card with the plan name (**Free plan** or **Paid plan**) and a one-line summary taken from the product rules, derived from `GET /api/billing/account/entitlement`. The server is the only source of the plan.
- **FR-67-02 — Right-aligned action:** The card's action is on the right: **Upgrade** for Free and **Buy more credits** for Paid. On narrow screens it stacks below the text.
- **FR-67-03 — Packages and checkout:** The action opens the one-time packages (5 or 10 credits) from `GET /api/billing/packages` with server-provided prices. Each available package starts the existing `POST /api/billing/cases/{case_id}/checkout` for the account's case and follows only a `https://checkout.stripe.com` address. The panel explains that a case is needed when the account has none, and that packages are not available yet when none is available; it never shows a success-shaped result.
- **FR-67-04 — No downgrade:** No control switches a Paid account to Free.
- **FR-67-05 — Failures:** If the plan or packages cannot be loaded, the card says the plan is unavailable and the rest of the Account area keeps working. A checkout failure is shown in the panel.
- **FR-67-06 — Accessibility:** The card is a labelled region, the summary and panel status are announced politely, and the action is a button that reports whether its panel is expanded.

## Acceptance criteria

1. A Free account shows Free plan with Upgrade; a Paid account shows Paid plan with Buy more credits; neither shows a downgrade control.
2. The panel lists server packages and prices, starts the existing checkout, and explains missing case or unavailable packages.
3. Load failures leave the Account area usable.
4. Automated tests cover the card and its states; the Free, Paid, and no-case states were exercised in a browser against PostgreSQL.

## Implementation boundary

No new billing API, price, tier, refund, or invoice view. The plan summary does not state numeric limits.
