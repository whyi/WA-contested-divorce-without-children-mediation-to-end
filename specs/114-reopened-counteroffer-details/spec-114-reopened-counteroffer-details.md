# Spec 114: Editable Counteroffer Details on the Latest Reopened Attempt

- **Tracking issue:** [#366](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/366)
- **Amends:** Specs 100, 107 (accepted closure), 110 (completion lifecycle), 112
  (response-only reopening), and 113 (counteroffer Next readiness), only for the
  latest reopened attempt's counteroffer notes and attachments. Historical
  specifications remain unchanged.

## Requirements

1. When an accepted-closed case is reopened and its latest response is
   **Counteroffer received**, restore all previously saved counteroffer notes
   and attachment links unchanged. Allow editing the notes and uploading
   counteroffer files on that latest attempt, including the final plan attempt.
2. Save notes separately from the outcome-only update, with owner authorization,
   revision checks, scope checks, and explicit errors. Reject bundled selection,
   outcome, document-link replacement, confirmation, or proposal changes.
   Uploads use the existing validated, quota-enforced, idempotent file route.
3. Keep proposal values, dates, sent documents, frozen snapshots, historical
   attempts, permanently closed case review, and attempt creation read-only.
   Do not clear the permanent lock or consume credits. Only the current
   counteroffer response is editable; other response choices do not unlock files.
4. Preserve same-name overwrite confirmation for current counteroffer files.
   Do not overwrite files also used by other saved responses, accepted documents,
   or the original offer. Ask for a different filename in that case.
5. Keep exactly one visible Next inside the counteroffer panel at its bottom.
   Disable it until saved non-whitespace notes or a saved attachment exist, and
   while editing, saving, or uploading. Enable it after successful persistence.
   Failed persistence retains the draft and announces the error.
6. Reopened-case Next saves current counteroffer details and shows the existing
   **Subscription required** dialog for every plan; no new attempt, navigation,
   checkout, or credit consumption occurs. Accepted/rejected behavior is unchanged.
7. Restored data, subsequent edits, and attachments survive reload and switching
   response choices. Preserve existing file validation, attachment limits, CSRF,
   session handling, and unrelated ordinary-attempt and fictional-demo behavior.

## Regression coverage

- Backend: reopen/restore/edit/upload, snapshots and lock invariance, scope and
  field guards, stale revisions, closed/historical/wrong-outcome rejection,
  owner checks, and safe overwrite behavior.
- Chromium: Free/paid final attempts, desktop/mobile, restored notes and links,
  editing/autosave and failure recovery, upload and failure recovery, reload,
  Next readiness and placement, and subscription popup without continuation.
