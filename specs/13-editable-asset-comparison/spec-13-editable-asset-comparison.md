# Spec 13: Editable Asset Comparison

- **Status:** Draft
- **Related issue:** [#57 — Allow editing fictional asset comparison values](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/57)
- **Related specification:** [Spec 10: Mock Asset-Analysis Dashboard](../10-mock-asset-analysis-dashboard/spec-10-mock-asset-analysis-dashboard.md)
- **Objective:** Let users explore the fictional annual asset comparison by editing its sample amounts and immediately seeing derived totals and timeline effects.
- **Scope:** In-page edit mode for the selected year's asset and liability values. This does not edit case data, persist changes, or send values to an API or provider.

## 1. Editing Behavior

- **FR-13-01 — Explicit edit entry:** Provide a clearly labeled, keyboard-accessible **Edit values** action for the currently selected year. Double-click may be an additional shortcut, but must not be the only way to enter edit mode.
- **FR-13-02 — Editable fields:** In edit mode, allow editing each category's amount for **You** and **Other party**. Preserve the existing category labels and row order.
- **FR-13-03 — Derived amounts:** Keep **Combined** values and **Net assets** totals calculated and read-only. Recalculate them from the two party values when edits are saved.
- **FR-13-04 — Currency input:** Accept whole-dollar values only. Permit negative values for liabilities such as debt; reject empty, non-numeric, fractional, and unsafe numeric values with accessible inline feedback. Do not silently coerce invalid input.
- **FR-13-05 — Save and cancel:** Show explicit **Save changes** and **Cancel** actions in edit mode. Save applies valid edits to the selected fictional year; Cancel discards unsaved edits and restores the displayed values.
- **FR-13-06 — Year navigation:** If the user changes the selected year during edit mode, discard pending edits and announce that the edit was canceled. The user must not accidentally apply edits to another year.
- **FR-13-07 — Feedback and focus:** Use the existing live status region or a related accessible status to announce edit entry, successful save, cancellation, and validation errors. Return focus to the edit action after save/cancel.

## 2. Data and Demo Boundaries

- **FR-13-08 — Recalculate timeline:** After a successful save, update the selected-year table and recompute the asset timeline from the edited year data. Keep all years visible.
- **FR-13-09 — Session-only changes:** Edited values exist only in page memory. Do not write to local or session storage, IndexedDB, an API, or a database. Reloading restores the original fictional values.
- **FR-13-10 — Isolation and labeling:** Keep the fictional-example notice visible. Edits affect only this local demo and must never read or modify user case data.

## 3. Accessibility and Responsive Behavior

- **FR-13-11 — Semantic controls:** Keep the comparison as a semantic table. Give each numeric input an accessible name containing its category, party, and year. Do not make calculated cells appear editable.
- **FR-13-12 — Keyboard support:** All edit, save, cancel, and field controls must be operable with a keyboard. Validation feedback must be programmatically associated with the relevant inputs.
- **FR-13-13 — Narrow screens:** Keep edit controls within the existing labeled horizontal table-scrolling region and usable at narrow viewport widths.

## 4. Acceptance Criteria

1. Users can enter edit mode through an explicit accessible action and edit each party amount in the selected year.
2. Combined amounts and net assets remain read-only and are recalculated after save.
3. Invalid, incomplete, fractional, and unsafe numeric values prevent saving and produce accessible feedback.
4. Cancel discards pending changes; changing years during editing cancels the draft rather than applying it to a different year.
5. Saving updates the selected-year table and the timeline while retaining all sample years.
6. Edits are limited to the current page session; reload restores the original fictional data.
7. No API/provider calls or browser storage are used for these edits, and the fictional-demo notice remains visible.
