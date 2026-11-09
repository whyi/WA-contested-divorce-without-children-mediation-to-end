# Spec 95: Shared accepted page and single case return

This additive specification amends specs 93 and 94. Prior specifications remain
unchanged.

- Use one shared guidance section for real and demo Offer accepted pages, with
  the demo's headings, official-form links and judgment/deadline guidance.
  Keep fictional notices only in demo mode and verify accepted/sent state for
  real cases before revealing the guidance.
- Remove the accepted-page file chooser, attachment status and upload handlers.
  Remove the duplicate authenticated-only guidance markup.
- Remove Back to mediation and the mark-completed/return button and handlers.
  The bottom action area contains only **Back to your case**, linking directly
  to that case's Asset Overview (or the corresponding demo case).
- Returning does not close/finalize the case or upload any document. Existing
  saved documents, responses and backend lifecycle APIs remain preserved.
- Verify real asset-workflow and legacy selection-based completion pages, demo
  variants, missing/unconfirmed responses, no chooser, shared content/layout,
  exactly one bottom action and correct return navigation.
