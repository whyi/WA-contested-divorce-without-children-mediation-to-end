# Spec 91: Original filenames and confirmed duplicate overwrite

This additive specification amends specs 79 and 81's case file management.
Prior specifications remain unchanged.

- Display uploaded filenames verbatim, including spaces, case and Unicode.
  Store the original filename independently of private storage keys. Downloads
  use the original filename with a safely encoded Content-Disposition header.
- Legacy records whose original names were never stored display an explicit
  unavailable-name label. Do not invent or reconstruct their original names.
- Adding an exactly matching filename within the same case requires an explicit
  **Overwrite it?** confirmation. No cancels that file's upload; Yes replaces
  that exact document, preserving the filename. Names are case-sensitive.
- Apply confirmation consistently to document intake, case file management,
  optional offer uploads and the browser-local demo file manager.
- Remove the Replace and Refresh saved files buttons, their inputs, handlers
  and replacement-only code. Automatically reconcile saved files after changes.
- Serialize collision checks on the case row. Confirmed overwrites can succeed
  at the attachment quota. Preserve the old file until the new file is stored.
  If cleanup fails, retain a pending target and retry the same import without
  uploading duplicate content; do not report completion prematurely.
- Retarget existing-offer document references to the successful new document.
  Invalid/stale overwrite targets fail explicitly. Retries must retain filename
  and content identity. Internal staging does not grant extra attachment slots.
- Verify original Unicode names and download headers, confirmation/cancellation,
  quota-full overwrites, storage and cleanup failures, idempotent cleanup retries,
  existing-offer references and upgrade/downgrade preservation of legacy rows.
