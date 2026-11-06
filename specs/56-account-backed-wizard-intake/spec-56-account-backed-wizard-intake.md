# Spec 56: Account-Backed Wizard Intake Draft

- **Status:** Implemented
- **Related issue:** [#207 — Implement account-backed workflows for Demo 1 and Demo 2](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/207)
- **Objective:** Persist authenticated wizard intake in the user's authorized case so it survives refreshes and later sign-ins, while preserving the public demos' browser-only behavior.
- **Scope:** `/onboarding/wizard?case_id=...` and the case-scoped wizard-intake API. This is the first vertical slice of #207; case uploads, dashboard/file-manager wiring, and negotiation workflow integration remain separate work.

## Requirements

1. **Authenticated case scope:** Read and write wizard drafts only through the specified case ID after normal case membership and lifecycle checks. An ID is not authorization. Reads must use `Cache-Control: no-store`.
2. **Server persistence:** `GET /cases/{case_id}/wizard-intake` returns the saved draft and its revision. A case with no saved draft returns an empty version-1 draft at revision 0.
3. **Validated writes:** `PUT /cases/{case_id}/wizard-intake` accepts a complete version-1 draft and the expected revision. Persist the draft and increment the revision atomically. Reject stale revisions with a conflict instead of silently overwriting another tab's newer edits.
4. **Draft data:** Persist filed status, party role, relationship/case dates with unknown markers, finance entries, issues/goals, and known agreements. Enforce the UI's text lengths, valid date/amount values, unique entry IDs, and a maximum of 250 entries per collection. Reject unknown fields.
5. **Explicit storage boundary:** Wizard evidence files remain browser-local and are not represented as case-uploaded documents by this API. Continue to show that distinction; case-scoped file upload is outside this slice.
6. **Existing-offer boundary:** Existing-offer answers/notes continue to use the existing case-creation and existing-offer APIs; do not duplicate or overwrite them in the wizard draft.
7. **Frontend integration:** Authenticated wizard load uses the server draft as the source of truth and retains browser-local attachments only as a local sidecar. Autosave and the finish action must report server failures and must not navigate away as though a failed server save succeeded.
8. **Demo isolation:** Demo 1/2 remain browser-local, temporary previews. They must not call the authenticated wizard-intake endpoints or create account-backed cases.
9. **Failure behavior:** Database failures return an explicit retryable service error, roll back the transaction, and do not claim the draft was saved.
10. **Case export:** Include the persisted wizard draft and revision in the unrestricted case-data export; browser-local attachments remain excluded.

## Acceptance Criteria

- An authorized case owner can save a draft, reload the wizard, and recover all structured wizard fields and the server revision.
- A user without membership cannot read or modify another user's draft; finalized or closed cases cannot be modified.
- A stale `expected_revision` is rejected without changing stored data.
- Malformed dates, negative or over-precision amounts, duplicate IDs, excess entries, and unsupported fields are rejected.
- Authenticated wizard saves remain available when browser storage is unavailable, with any unsaved browser-only attachments clearly reported.
- Case export contains the saved structured wizard draft and revision without implying that browser-local attachments were uploaded.
- Public demo drafts continue to use the existing local storage flow and do not make wizard-intake API requests.
- Migration upgrade and downgrade, route behavior, and UI integration have focused automated coverage.

## Implementation Notes

- Store the draft in a dedicated JSONB case column to avoid collisions with case metadata such as workflow selection and existing-offer history.
- Keep each API response uncached and omit browser-local file blobs.
- Do not map the intake into legal/property classifications or send it to AI as part of this feature.
