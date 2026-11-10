# Spec 113: Counteroffer Next Placement and Readiness

- **Related issue:** [#364](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/364)

This additive specification amends Spec 94's disabled-looking but clickable
quota action. Historical specifications remain unchanged.

## Requirements

- On the current real attempt, place the counteroffer Next action inside the
  bottom of the **Offer from the other party** panel, including the last allowed
  attempt and a reopened response-only case. Do not show a second Next above it.
- For editable counteroffers, use native disabled state until non-whitespace
  notes or a counteroffer attachment have been successfully saved. Disable Next
  during note edits, persistence, uploads, and after failed note persistence.
- At the attempt limit, a ready Next is genuinely enabled. Clicking it saves
  the response and opens the existing credits dialog without creating an
  attempt or navigating. Click and keyboard activation behave identically.
- Removing the only notes disables Next again; a saved attachment alone is
  sufficient. Reload restores readiness from saved data.
- Preserve historical/closed case locks, reopened response-only restrictions,
  accepted/rejected navigation, upload validation, and server quota enforcement.
  Reopened response-only cases retain their subscription dialog and cannot
  edit permanently locked notes or files.

## Regression coverage

Exercise final Free and paid attempts at desktop and mobile widths, empty and
whitespace notes, saved/cleared notes, file-only readiness, persistence failures,
reload, bottom-of-panel placement, and credit-dialog activation without
continuation requests.
