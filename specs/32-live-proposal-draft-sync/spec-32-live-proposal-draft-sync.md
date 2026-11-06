# Spec 32: Live Proposal Draft Synchronization

- **Status:** Implemented
- **Follow-up to:** [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 23: Explicit Sent Confirmation Freeze](../23-explicit-sent-confirmation-freeze/spec-23-explicit-sent-confirmation-freeze.md)
- **Related specification:** [Spec 19: CR 2A Proposal and Property-Division Exports](../19-cr2a-property-division-exports/spec-19-cr2a-property-division-exports.md)
- **Objective:** Keep proposal documents synchronized with attempt edits, and make current-file downloads and explicit sent confirmation an ordered, enforced workflow.
- **Scope:** Authenticated, authorized case workflows. Public fictional demos remain unchanged.

## 1. Selection and Draft Generation

- **FR-32-01 — Explicit scenario gate:** Disable both proposal-download buttons until the user has selected a settlement scenario.
- **FR-32-02 — Live editable draft:** Keep scenario assumptions and proposal fields editable until the user explicitly confirms that the final files were reviewed and sent. Downloading either file does not lock the attempt.
- **FR-32-03 — Server-generated synchronization:** Save valid attempt edits and regenerate both current draft files on the server as the user edits. Include attempt-specific milestones and proposed values in the generated documents. Preview synchronization alone does not consume a document credit or send files.
- **FR-32-04 — Credit boundary:** Charge one document credit once when the current proposal version is first downloaded or delivered. Refreshing its documents while the attempt remains editable does not create another version or consume another credit.
- **FR-32-05 — Current-download tracking:** Record DOCX and XLSX downloads for the current document content. Any document-affecting edit invalidates both download markers; both buttons must be used again for the updated content.

## 2. Confirmation and Integrity

- **FR-32-06 — Confirmation gate:** Keep “I reviewed and sent these final documents” disabled until both current files have been downloaded and both exact final files have been attached.
- **FR-32-07 — Latest attachment check:** Require the attached final files to have been uploaded after the most recent document-content change. Enforce all download and attachment gates on the server.
- **FR-32-08 — Freeze point:** Only explicit reviewed-and-sent confirmation freezes the attempt and snapshots its current scenario, editable inputs, and final-document metadata.
- **FR-32-09 — Existing safeguards:** Preserve case authorization, revision checks, secure file validation and storage, credit idempotency, and no-AI/no-automatic-delivery behavior during editing and synchronization.

## 3. Acceptance Criteria

1. Both download buttons start disabled and become available only after scenario selection.
2. Before sent confirmation, changes to scenario assumptions, dates, terms, milestones, or proposed values save and regenerate both server-side drafts.
3. Proposal edits remain possible after either or both download buttons have been used.
4. An edit invalidates both current-download markers; re-downloading the current DOCX and XLSX is required before confirmation.
5. Confirmation requires both current downloads and both final attachments uploaded after the latest document edit.
6. Only the reviewed-and-sent confirmation freezes the attempt; updating an editable draft does not consume an additional credit.
7. Public demo behavior, case authorization, explicit delivery confirmation, and no-AI boundaries remain intact.
