# Spec 83: Document navigation and concise attempt presentation

This additive specification amends specs 81 and 82. Counteroffer input from spec
82 remains available.

- Show only `1st Attempt is current.` below the current first-attempt navigation;
  use the corresponding ordinal for a later current attempt. Remove preparation
  and unsaved-attempt explanations from this location.
- On the real document-selection page, place an actual **Back** button on the
  left and **Next** button on the right. Both use button styling and pointer
  cursors. Empty selection still disables Next; do not import empty selections.
- Back opens the existing case's documents-or-guided mode selection, not Asset
  Overview. Preserve the existing case and any saved offer/materials. Choosing
  a different mode uses the existing workflow-mode API, not case creation.
- Next continues to save a checked offer and selected documents before opening
  Asset Overview. Failed saving does not navigate.
- Delete the duplicate source-record presentation at the bottom of Asset
  Overview, including its extra heading, current-saved-case-information status,
  source table, and edit link. Keep the shared Asset Overview controls only.
  Preserve all source data in storage and case export.
- Historical/frozen views still render only snapshot overrides and remain
  read-only; deletion of duplicate markup must not expose current values there.
