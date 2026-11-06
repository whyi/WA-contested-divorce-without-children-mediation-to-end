# Spec 44: Single-Case Demo Flow

- **Status:** Implementing
- **Related issue:** [#171 — Fix Demo 1 and Essential demo case navigation, limits, and archive behavior](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/171)
- **Related specifications:** [Spec 34: Party-Owned Case with One Invited Operator at a Time](../34-party-owned-case-delegation/spec-34-party-owned-case-delegation.md), [Spec 43: Demo Account Navigation, Entitlements, and Archive](../43-demo-account-navigation-archive/spec-43-demo-account-navigation-archive.md), [Spec 30: Subscription Plans and Stripe Billing](../30-subscription-billing/spec-30-subscription-billing.md)
- **Superseded requirements:** This additive spec supersedes Spec 43's demo-only multiple-case lists, plan-based case capacity, archive/restore flows, and “My cases” return navigation. It does not alter real-account case ownership; Spec 34's single-case invariant remains authoritative.
- **Objective:** Keep every demo centered on one fictional case. Plan tiers change the number of negotiation attempts available for that case, not the number of cases.
- **Scope:** Demo entry routing, the single fictional case, demo case navigation, and tier-specific attempt limits. Authenticated case APIs and billing remain unchanged.

## Functional requirements

- **FR-44-01 — One case per demo identity:** A demo identity contains at most one case. Demo 1 (Free) creates its one fictional case when the user chooses a preparation path. Demo 2 (Essential) opens its existing sample case. Re-entering either demo opens that same case; it never creates another case.
- **FR-44-02 — No case-list dashboard:** Demo navigation does not show a “My cases” page, active-case list, archived-case list, or create-another-case affordance. The entry for a demo without a case offers the two preparation paths; after case creation, the demo opens its case directly.
- **FR-44-03 — Attempts, not case slots:** Free and Essential differ by the per-case attempt allowance (1 and 3, respectively). Neither the UI nor demo state derives the number of cases from plan tier. A counteroffer/rejection may start another attempt only while the current demo case remains below its tier's attempt limit. The current attempt ordinal is stored with that single browser-local case so refreshing cannot reset the allowance.
- **FR-44-04 — Case navigation:** Demo preparation, Asset Overview, file management, and completion routes preserve the same demo identity and case ID. The case navigation offers case views, not a My Cases destination.
- **FR-44-05 — Browser-local isolation:** Demo state is stored locally under a demo-identity-specific key, never submitted to authenticated case APIs, and never modifies a real account or case. Storage failures are shown explicitly.
- **FR-44-06 — No demo archive:** A demo case cannot be archived, restored as a second case, or deleted through a case-list workflow. Real account closure/reopen remains unchanged.
- **FR-44-07 — Historical route compatibility:** Existing `/demo/1`, `/demo/1/dashboard`, `/demo/2`, `/demo/2/dashboard`, and `/demo/dashboard` URLs redirect to the appropriate single-case start or Asset Overview route; they do not render a case-list page.

## Acceptance criteria

1. Demo 1 opens a preparation-path choice when it has no case, creates exactly one browser-local case, and returns to that same case after refresh or navigation.
2. Demo 2 opens `XYZ vs ABC` directly; neither demo exposes a My Cases dashboard, multiple-case list, archive list, or create-another-case action.
3. “My cases” navigation is absent from demo case navigation and completion screens. Returning from preparation or completion opens the same case.
4. Free is limited to one attempt and Essential to three attempts for the same case. The current ordinal survives refresh; no limit or messaging permits additional cases.
5. Legacy demo-dashboard URLs redirect to the single-case flow.
6. Demo actions do not call authenticated case creation, close, reopen, archive, or deletion APIs.
7. Existing authenticated account, ownership, authorization, attempt charging, and case lifecycle behavior is unchanged.
