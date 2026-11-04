# Spec 24: Counteroffer Attempt Inheritance in the Demo

- **Status:** Implemented; automated tests passing
- **Related issue:** [#80 — Show inherited values on the next counteroffer attempt](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/80)
- **Related specifications:** [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 23: Explicit Sent Confirmation Freeze](../23-explicit-sent-confirmation-freeze/spec-23-explicit-sent-confirmation-freeze.md)
- **Objective:** Reuse the first-attempt proposal page for every demo counteroffer round, carry forward its values as an independent editable copy, and make inherited values and their source attempt obvious.
- **Scope:** Public fictional settlement demo only. It remains in-page and non-persistent; authenticated attempt creation and server snapshots retain their existing behavior.

## 1. Counteroffer Progression

- **FR-24-01 — Shared proposal page:** After a fictional counteroffer is recorded and Next is selected, return to the beginning of the same proposal page used for First Attempt, update the prominent attempt ordinal, and preserve the current scenario inputs.
- **FR-24-02 — Independent copy:** Capture the completed attempt's dates, selected timeline point, sample asset values and overrides, milestone state, and selected scenario before opening the next attempt. The next attempt starts with equal values but subsequent edits must not change its predecessor's captured state.
- **FR-24-03 — Inherited-value indicator:** Clearly identify values copied from the immediately preceding attempt. Highlight both settlement date controls, the selected-date asset table, and the selected scenario/results, and provide a textual source label such as “From First Attempt”.
- **FR-24-04 — Edited values:** Remove inherited highlighting for dates or values when they no longer match their copied value. Re-rendered table and scenario values must retain the indicator only while they still match their inherited state.
- **FR-24-05 — Repeated attempts:** Apply the same independent-copy behavior without an attempt limit. Each new attempt's source label names the immediately preceding ordinal, including ordinal formatting after Third Attempt.
- **FR-24-06 — Outcome boundaries:** Acceptance and rejection keep their existing terminal/placeholder flows and do not start a new proposal attempt.
- **FR-24-07 — Demo boundary:** No actual file is uploaded or sent, no case data is persisted, and no AI call is introduced.

## 2. Accessibility and Presentation

- **FR-24-08 — Non-color cue:** Pair any theme-consistent highlight color with visible text identifying the source attempt. The source must remain understandable without color.
- **FR-24-09 — Transition focus:** Move focus/scroll to the beginning of the reused proposal page after counteroffer progression so the new attempt starts in the same context as the first.
- **FR-24-10 — Responsive theme:** Inherited-value styling follows existing light/dark theme tokens and remains legible on narrow layouts.

## 3. Acceptance Criteria

1. A recorded fictional counteroffer followed by Next returns to the top of the shared proposal page with the next attempt ordinal.
2. The new attempt starts with the previous attempt's dates, selected scenario, table values, selected timeline point, and milestone state.
3. The date range, selected-date asset table, and selected scenario/results identify which previous attempt supplied their inherited values.
4. Changing copied values updates their inherited indicators and leaves the completed attempt snapshot unchanged.
5. Third and later attempts repeat the behavior and identify the immediately previous attempt as the source.
6. Accepted/rejected outcomes and the demo's fictional, non-persistent boundary are unchanged.

## 4. Implementation Status

- Counteroffer progression captures the completed in-memory attempt, restores an independent editable copy into the shared proposal view, and scrolls/focuses the top of that view.
- The new attempt's ordinal and inherited source are shown prominently. Unchanged dates, timeline point, selected-date asset values, milestones, and scenario share receive theme-aware highlights with textual source labels; changing a value removes its corresponding highlight.
- Previous attempt snapshots are retained in page memory only. No demo attempt is persisted, no actual file is sent, and no AI call is made.
- The complete automated test suite passes.
