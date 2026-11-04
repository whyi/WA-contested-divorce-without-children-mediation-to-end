# Spec 22: Versioned Settlement Negotiation Attempts

- **Status:** Implemented; automated test validation pending
- **Related issue:** [#76 — Version settlement negotiations across counteroffer attempts](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/76)
- **Related specifications:** [Spec 16: Evidence-Traced Settlement Planning](../16-evidence-traced-settlement-planning/spec-16-evidence-traced-settlement-planning.md), [Spec 19: CR 2A Proposal and Property-Division Exports](../19-cr2a-property-division-exports/spec-19-cr2a-property-division-exports.md), [Spec 21: Settlement Offer Response and Finalization](../21-settlement-offer-response-and-finalization/spec-21-settlement-offer-response-and-finalization.md)
- **Objective:** Preserve a clear, auditable version for every settlement proposal and counteroffer round, freeze completed rounds, and start each subsequent attempt from an editable copy of its predecessor.
- **Scope:** Authenticated, authorized case workspaces only. Public demo interactions remain fictional and do not persist.
- **Terminology:** An **attempt** is one proposal sent by the user and the recorded response to that proposal. The first is “First Attempt”; each counteroffer creates the next attempt.

## 1. Attempt Lifecycle

- **FR-22-01 — Visible ordinal:** Show the current attempt prominently throughout scenario selection, proposal preparation, and response tracking. Render ordinals naturally (“First Attempt”, “Second Attempt”, “Third Attempt”, then continuing numeric ordinals) without an arbitrary attempt limit.
- **FR-22-02 — Attempt snapshot:** Persist an immutable snapshot for every attempt, including selected scenario/run and assumptions, relevant case-profile/milestone state, settlement ledger values/revisions, and the final files the user records as sent. Preserve response outcome and received counteroffer attachment with that attempt.
- **FR-22-03 — Counteroffer selection and upload:** When the user selects “Counteroffer received”, immediately freeze the current attempt’s editable inputs and show “Attach the counteroffer here”. Accept supported files through the authorized secure local upload path. Explain that Google Drive Picker is unavailable unless a secure implementation is actually configured; never imply Drive selection works when it does not.
- **FR-22-04 — Continue gate:** Keep Next disabled until the counteroffer attachment is successfully stored. Server-side continue validation is authoritative; a client-side button state is not sufficient.
- **FR-22-05 — Create the next attempt:** After a counteroffer is attached and the user continues, create the next attempt from the predecessor’s frozen snapshot. Carry over scenario axes, dates, milestones, values, and other relevant selections as a starting point. The new attempt is editable independently; edits must never mutate earlier attempts.
- **FR-22-06 — Freeze prior attempt:** A completed/counteroffer attempt is read-only. Reject attempts to replace its sent documents, alter its outcome/assumptions, or add inconsistent state after the next attempt is created, except through an explicit, audited correction path if one is later specified.
- **FR-22-07 — Repeated negotiations:** Counteroffer → next attempt can repeat until the user records acceptance or rejection. Do not impose a fixed maximum. Rejection and acceptance do not spawn another negotiation attempt.
- **FR-22-08 — History:** List all attempts in order, identify active versus frozen, show their outcome and attachment metadata, and allow authorized members to inspect previous snapshots without editing them.
- **FR-22-09 — Explicit transition:** Creating the next attempt is a user-confirmed action following a valid uploaded counteroffer. No files are automatically sent, and no AI analysis is triggered.

## 2. Data Integrity, Security, and UX

- **FR-22-10 — Server-enforced revisions:** Bind snapshots and mutations to case membership, scenario selection/run, and expected profile/settlement revisions. Reject stale or conflicting writes visibly; never overwrite a frozen snapshot.
- **FR-22-11 — Facts versus negotiation assumptions:** Preserve evidence-backed facts and source records as case data. Attempt-specific negotiation assumptions and proposed allocations are versioned separately; a user must not silently rewrite adopted facts when making a new offer.
- **FR-22-12 — Secure attachment storage:** Continue using case-scoped authorization, content/type/size validation, encrypted object storage, and minimal metadata. Do not return or log file contents, OAuth credentials, or source-document text.
- **FR-22-13 — Accessible freeze state:** Clearly announce that choosing a counteroffer locks the completed attempt. Disable/mark its date, milestone, ledger, scenario, and proposal controls read-only. Explain that Next opens an editable copy as the next attempt.
- **FR-22-14 — Resumption:** Reloading the case restores the active attempt and immutable history accurately. A failed next-attempt creation leaves the prior attempt frozen and reports the failure instead of presenting a success-shaped transition.

## 3. Acceptance Criteria

1. Initial negotiation is visibly labeled “First Attempt”; every subsequent counteroffer advances the ordinal indefinitely.
2. Selecting a counteroffer freezes the current attempt and exposes a required attachment prompt.
3. Continue is disabled until a valid counteroffer attachment is stored, and the backend independently enforces the same gate.
4. Next creates an editable next attempt populated from the prior frozen snapshot; no prior attempt can be mutated through the new attempt.
5. Dates, milestones, scenario assumptions/values, sent documents, counteroffers, and outcomes remain visible in ordered history.
6. Accepted/rejected attempts stop negotiation progression.
7. Case authorization, auditability, upload validation, no-auto-send, and no-AI boundaries remain intact.

## 4. Implementation Status

- Implemented in migration `0011_settlement_attempts` with a case-scoped attempt chain, server-built scenario/profile/ledger snapshots, editable attempt state, and frozen snapshots.
- Counteroffer selection freezes the attempt; authorized local uploads remain required before Next. Next creates an independently editable copy with the next ordinal. Acceptance and rejection are terminal.
- The browser restores attempt history and state, labels ordinals and frozen status, and keeps case facts/ledger data separate from attempt-specific proposal values.
- Drive Picker remains unavailable. Negotiation transitions do not send files or invoke AI; public demo interactions remain fictional and non-persistent.
