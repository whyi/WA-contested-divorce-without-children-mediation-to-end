# Spec 23: Explicit Sent Confirmation Freeze

- **Status:** Implemented; automated tests passing
- **Related issue:** [#78 — Freeze settlement attempt after explicit sent confirmation](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/78)
- **Follow-up to:** [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md)
- **Objective:** Keep proposal assumptions editable through drafting and final-file attachment, then freeze an immutable attempt only after the user explicitly confirms that they reviewed and sent the final documents.
- **Scope:** Authenticated, authorized case workflows. The public fictional demo must not imply that any actual file was sent or persisted.

## 1. Confirmation and Freeze Lifecycle

- **FR-23-01 — Editable draft:** Downloading proposal drafts or attaching final DOCX/XLSX files does not freeze dates, scenario assumptions, milestones, proposed values, or other attempt inputs.
- **FR-23-02 — Explicit attestation:** After both final sent documents are attached, present a clear user action such as “I reviewed and sent these final documents.” This records the user's attestation only; it does not transmit documents.
- **FR-23-03 — Snapshot on confirmation:** The server validates current authorization and expected attempt revision, then captures a server-generated immutable snapshot of the selected scenario and attempt-specific proposal inputs, including dates, milestones, values, and final sent-document metadata.
- **FR-23-04 — Outcome gate:** Do not allow acceptance, rejection, or counteroffer outcome recording until both sent documents are attached and the explicit confirmation has been recorded. Enforce this on the server as well as in the UI.
- **FR-23-05 — Frozen state:** After confirmation, prevent edits to the attempt, replacing final sent documents, or changing the confirmation/outcome. Reload must restore and display the frozen status and snapshot.
- **FR-23-06 — Counteroffer progression:** Preserve the confirmed attempt unchanged. After the counteroffer attachment is successfully stored, Next creates the subsequent attempt as an independently editable copy of the confirmed snapshot.
- **FR-23-07 — Terminal outcomes:** Acceptance and rejection retain their existing non-progression behavior.

## 2. Data Integrity, Security, and UX

- **FR-23-08 — Revision checks:** Confirmation and all pre-confirmation edits use expected attempt revisions and current case revisions. Conflicts fail visibly; confirmation must not overwrite edits made elsewhere.
- **FR-23-09 — Existing safeguards:** Preserve case authorization, secure upload validation/storage, response history, counteroffer upload gating, and the no-AI/no-automatic-delivery boundaries.
- **FR-23-10 — Clear timing:** Explain that downloading and attaching are still draft preparation; the attempt becomes read-only only after the user confirms the actual final documents were sent.
- **FR-23-11 — Resume behavior:** Reloading an unconfirmed attempt keeps it editable; reloading a confirmed attempt keeps it frozen.
- **FR-23-12 — Public demo:** Keep the demo fictional and non-persistent. Its demonstration of attempt progression must not imply an actual send or case record.

## 3. Acceptance Criteria

1. Draft downloads and final-file uploads leave attempt assumptions editable.
2. The explicit reviewed-and-sent action is the only proposal freeze point.
3. Outcome recording requires both final documents and server-recorded confirmation.
4. Confirmed attempts cannot be edited or have sent files replaced and remain frozen after reload.
5. Counteroffer progression clones the confirmed snapshot without mutating its predecessor.
6. Rejected/accepted outcomes remain terminal; no files are auto-sent and no AI is invoked.

## 4. Implementation Status

- Implemented in migration `0012_sent_confirmation_freeze`, which records explicit confirmation timestamps and treats attempts frozen under the prior workflow as already confirmed.
- Final-file uploads remain replaceable and proposal inputs remain editable until the authorized user confirms that both final documents were reviewed and sent.
- The confirmation endpoint snapshots the server-held scenario, attempt fields, and sent-file metadata, then locks the attempt. Outcome selection and continuation require that confirmation.
- The authenticated UI restores the saved confirmation state, displays the freeze point clearly, and preserves counteroffer cloning and terminal outcomes.
- Focused and full test suites pass; no files are sent or processed by AI as part of confirmation.
