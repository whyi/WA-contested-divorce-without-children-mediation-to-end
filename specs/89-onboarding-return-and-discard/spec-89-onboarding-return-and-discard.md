# Spec 89: Onboarding return, autosave and confirmed mode discard

This additive specification amends specs 82, 85, 86 and 87. Prior specs remain
unchanged.

- Remove the top account-return link. Guided intake has document-style bottom
  **Back** (left) and **Next** (right) buttons, available outside its gated
  questionnaire. Back saves the draft and opens the starting-point page; Next
  retains the minimum-input gate, saves and opens Asset Overview. Failed writes
  remain visible and retryable on the current screen.
- Restore functional starting-point controls on browser back/forward-cache
  return. Consult saved case mode, not the destination page's URL mode. Reopening
  the same mode never resets it or creates another case.
- Retain just-edited wizard answers locally before the server-save debounce.
  Restore pending local changes on same-mode return using the saved server
  revision; surface revision conflicts rather than silently overwriting them.
  If Back cannot save to the server, preserve locally and show that limitation
  on mode selection instead of trapping the user or claiming server success.
- Persist selected document bytes and offer drafts in browser-local IndexedDB
  so leaving for mode selection and returning retains selection. Preserve upload
  retry identities. Report browser-storage failures explicitly.
- Remove **Save offer details**. Debounce offer text/file changes into automatic
  server saves, preserve edits made during a request, and show saved, pending or
  failure status. Back flushes saves; Next verifies saving before continuing.
- Mark the mode with existing work using **\* You have work in progress**.
- Choosing the other mode with existing work opens a Yes/No dialog naming the
  working mode. No preserves everything. Yes permanently discards all onboarding
  inputs, offer details, locally selected files and uploaded case files before
  starting the chosen mode. Clear wizard answers and attached evidence, case
  property/milestone/inventory inputs and any onboarding asset snapshots.
- Use existing permanent-document-deletion machinery for uploaded files, including
  object deletion, dependent metadata cleanup and attachment-slot recovery.
  Persist pending discard intent, surface incomplete deletion, and allow retry
  only toward the same target mode. Do not report success until cleanup completes.
- Block new imports and questionnaire/offer writes while a discard is pending.
  Reject delayed offer autosaves from the discarded mode so they cannot restore
  cleared data after the mode changes.
- Switching is an onboarding operation, not an attempt operation. Reject discard
  once a workspace has been entered or an attempt exists; do not alter attempts,
  credits, case ownership or the account.
- Verify button ordering, browser history return, both same-mode resumes, both
  confirmed switches, No, autosave/reload, deletion failure/retry and local-file
  preservation.
