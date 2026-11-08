# Spec 68: Property Division Ownership-Split Bars

- **Status:** Implemented; automated tests passing
- **Related issue:** [#250 — Show a red/blue ownership-split bar for each row of the Property Division Excel schedule](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/250)
- **Parent issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 27: Modified Offer Review](../27-modified-offer-review/), [Spec 28: Negotiation Attempt Limits](../28-negotiation-attempt-limits/)
- **Superseded historical requirements:** No historical specification is edited. This spec adds columns to the downloadable property-division XLSX; every existing column, formula, and import rule is unchanged.
- **Objective:** Let a reader see each property's proposed split between the two parties at a glance.

## Requirements

- **FR-68-01 — One bar per row:** Each property or debt row of the `Property Division` sheet has a horizontal bar, in the same row, made of 100 narrow cells (1% each) to the right of the existing table.
- **FR-68-02 — Colors:** The user's share is red and the other party's share is blue, so a 50/50 row is exactly half and half and a 40/60 row has a shorter red and longer blue segment.
- **FR-68-03 — Share definition:** User share = **Proposed to user ÷ Total**, clamped to 0–100%; other-party share = 100% − user share. The shares are shown numerically in **User %** and **Other party %** columns.
- **FR-68-04 — Live:** The bar and percentages are formulas and conditional formats, so they update when the user edits proposed amounts in Excel. Proposed values stay editable (the offer values are overridable).
- **FR-68-05 — No split available:** When the row Total is zero or negative, the percentages are blank and the bar is neutral grey.
- **FR-68-06 — Legend:** A legend row above the table explains the colors and the Proposed ÷ Total rule, with red "User" and blue "Other party" swatches. The percentages make the split readable without color.
- **FR-68-07 — Unchanged behavior:** Total and "Net to …" rows have no bar. The existing nine columns, the auto-filter range (`A:I`), and the modified-offer XLSX re-upload, which finds columns by header name, behave as before. The DOCX and the in-app web screens are unchanged.

## Acceptance criteria

1. A 50/50 row renders an equal red/blue bar; a 40/60 row renders a shorter red and longer blue bar.
2. Editing **Proposed to user** updates the bar and percentages.
3. Zero-total, negative, or over-100% rows never break the bar.
4. Legend and numeric percentages are present.
5. Existing export and modified-offer tests still pass.

## Verification

`tests/test_settlement_exports.py` checks the headers, formulas, three conditional-format rules and colors, bar range, and auto-filter. The workbook was also rendered in LibreOffice with 50/50, 40/60, 33/67, 100/0, 0/100, zero-total, and over-100% rows.
