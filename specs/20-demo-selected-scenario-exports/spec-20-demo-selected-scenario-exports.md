# Spec 20: Scenario-Selected Demo Document Exports

- **Status:** Implemented
- **Related issue:** [#72 — Tie demo document downloads to the selected scenario](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/72)
- **Related specification:** [Spec 19: CR 2A Proposal and Property-Division Exports](../19-cr2a-property-division-exports/spec-19-cr2a-property-division-exports.md)
- **Objective:** Place fictional demo document downloads directly beneath the three displayed scenario examples and generate documents using the scenario the user selected, without a separate share-percentage control.
- **Scope:** Public fictional demo scenario selection and demo-only DOCX/XLSX downloads. This does not alter authenticated case-workspace exports, delivery providers, or legal scenario calculations.

## 1. Scenario Selection and Downloads

- **FR-20-01 — Selectable scenario cards:** Each of the three currently rendered fictional scenario cards exposes a keyboard-operable selection control and a clear selected visual state. Exactly one scenario is selected at a time.
- **FR-20-02 — Deterministic default:** Select the even-share scenario on initial render. When dates change and cards are recalculated, preserve the selected share if it remains available; keep a deterministic selected scenario if the current selection becomes unavailable.
- **FR-20-03 — Export placement:** Place the DOCX and XLSX download actions immediately after the three scenario cards so the actions are visually and structurally associated with those choices.
- **FR-20-04 — One selected source of truth:** Remove the independent share dropdown and duplicate share state. Both document requests derive `community_share_bps` from the currently selected card and use the current start and end dates.
- **FR-20-05 — Explicit selection feedback:** Make the selected scenario apparent to assistive technology and visually apparent in both light and dark themes. Announce selection and export progress/results through accessible status messaging.
- **FR-20-06 — No selection mismatch:** A download must use a currently rendered, selected scenario. If no valid selection exists, do not send a request; report the issue and ask the user to select a scenario.
- **FR-20-07 — Demo privacy:** Keep demo documents fictional and page-only. Do not send them to external services or introduce case-data access, persistence, or AI processing.

## 2. Acceptance Criteria

1. Both download buttons appear directly below the three scenario cards.
2. No separate share-percentage dropdown remains in the demo export controls.
3. Selecting a different card visibly and accessibly changes the scenario used by both DOCX and XLSX downloads.
4. The submitted share and date range match the selected card and current date controls at request time.
5. Date changes recalculate all three cards while retaining the selected share when possible.
6. Invalid or missing selection prevents export and produces an accessible message.
7. Existing demo isolation, export error handling, fictional-data notice, keyboard access, and theme consistency remain intact.
