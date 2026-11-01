# Spec 10: Mock Asset-Analysis Dashboard

- **Status:** Draft
- **Related issue:** [#45 — Add a mock asset-analysis dashboard with timeline and settlement scenarios](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/45)
- **Objective:** Give users a tangible preview of the asset-comparison and settlement-scenario experience after importing case materials, before connecting an AI analysis provider.
- **Scope:** A local-only sample results view, a six-year spreadsheet-style asset and liability comparison, a relationship timeline chart, and three illustrative negotiation scenarios. This specification does not define AI analysis, legal advice, asset valuation, or saving selected scenarios.

## 1. Entry and Data Boundaries

- **FR-10-01 — Direct demo entry:** Provide a visible **Demo** link on the landing page and authenticated case dashboard. It opens the mock asset-analysis view directly without requiring sign-in, MFA, case lookup, or document import. After a successful import in the authenticated materials workflow, an **Analyze** action also opens this view.
- **FR-10-01a — Demo isolation:** The direct demo route uses only fixed fictional sample data. It does not create a demo login session or access the signed-in user's cases, documents, or profile.
- **FR-10-02 — No provider calls:** Opening or interacting with the mock view must not call an AI provider, create an analysis request, or require AI consent. The current AI analysis APIs remain outside this mock flow.
- **FR-10-03 — Fictional sample values:** All displayed dates, asset amounts, liabilities, totals, and scenario values are fixed illustrative data. They are not extracted from, inferred from, or associated with uploaded documents or case-profile facts.
- **FR-10-04 — No persistence:** Changing the selected year with the timeline slider or selecting a scenario is an in-page preview interaction only. Do not write sample values or scenario selections to the API, database, or browser storage.
- **FR-10-05 — Honest labeling:** Prominently state that the page uses fictional sample figures, does not analyze uploaded documents, and is not legal advice or a recommended property division.
- **FR-10-06 — Return path:** Provide an accessible action to return to the imported-files view without losing the current page state.

## 2. Asset Comparison and Timeline

- **FR-10-07 — Annual selector:** Represent the fictional six-year relationship timeline with one keyboard-accessible range slider, plus previous/next buttons. Do not create a separate tab or button for every year. Selecting a year updates the comparison table and moves a highlighted marker on the chart while keeping the complete timeline visible. Derive the slider bounds and endpoint labels from the available timeline data.
- **FR-10-08 — Spreadsheet comparison:** For the selected year, show asset and liability categories in rows and side-by-side columns for **You**, **Other party**, and **Combined** amounts. Include a net-assets total and clearly format amounts as U.S. dollars.
- **FR-10-09 — Timeline chart:** Show one chart with time on the horizontal axis and money on the vertical axis. Plot the fictional asset trend across all six years independently of the selected table year, with a legend, a selected-year marker, and an accessible text description that announces the highlighted year.
- **FR-10-10 — Responsive layout:** Keep the comparison usable on narrow screens with a labeled horizontal table-scrolling region; keep the year slider, previous/next buttons, and chart labels operable/readable without relying on color alone.

## 3. Illustrative Settlement Scenarios

- **FR-10-11 — Three scenarios:** Show three distinct sample scenarios: **Best-case proposal**, **Balanced proposal**, and **Fallback position**. Each includes its illustrative division and a brief explanation of its role in a negotiation conversation.
- **FR-10-12 — Interactive selection:** A user can select one scenario at a time. Announce the selected scenario accessibly; selection does not submit an offer, modify a case, or persist.
- **FR-10-13 — No legal conclusion:** Do not imply that any scenario is fair, legally correct, optimal, court-approved, or suitable for a specific user. Clearly state that figures are hypothetical and should be reviewed with qualified counsel or a mediator.

## 4. Acceptance Criteria

1. The landing page and signed-in case dashboard provide a **Demo** action that opens the sample results view without sign-in, MFA, case lookup, document import, an AI provider, or consent.
2. A successful import reveals an **Analyze** action, and activating it opens the sample results view without requiring an AI provider or consent.
3. One year slider and previous/next controls select any available year without rendering a tab per year; the selected-year asset/liability comparison shows both parties, the combined amount, and a net-assets total.
4. One timeline chart shows amounts over all six years, remains unfiltered by year selection, and highlights the selected year.
5. Three scenario cards can be selected independently of the year selector and are labeled as fictional, non-binding examples.
6. Browser network activity from opening the mock view contains no authentication, case lookup, analysis-request, provider, or persistence call.
7. No sample amount, scenario choice, or inferred claim is sent to or saved by the backend.
8. Keyboard and screen-reader users can operate the year slider, previous/next controls, scenario selection, and return navigation; the layout remains usable on mobile.
