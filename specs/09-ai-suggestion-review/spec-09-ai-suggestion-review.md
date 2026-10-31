# Spec 09: Review and Selectively Adopt AI Document Suggestions

- **Status:** Draft
- **Related issue:** [#33 — Let users review and selectively adopt AI document suggestions](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/33)
- **Depends on:** [#32 — Consent-based, evidence-grounded document analysis](../08-consent-based-document-analysis/spec-08-consent-based-document-analysis.md)
- **Objective:** Let an authorized case member inspect evidence-grounded AI suggestions, record a decision for each suggestion, and explicitly adopt only a selected subset as case-profile facts.
- **Scope:** Source preview, per-proposal review decisions, explicit batch adoption, append-only case-profile facts, provenance/audit history, conflict handling, authorization, and accessible review UI.
- **Storage decision:** Approved suggestions are stored in a separate append-only case-profile fact collection. Adoption must not overwrite or mutate `Case.metadata_json` or `Case.asset_liability_inventory`.

## 1. Suggestion and Evidence Review

- **FR-09-01 — Suggestions, not advice:** Every proposal is labeled as an AI suggestion, not a verified fact or legal advice. Proposal text remains separate from case-profile facts until final adoption.
- **FR-09-02 — Evidence status:** A proposal is approvable only while its source document exists, its digest matches the analyzed source, and its exact quote and location still match the stored extraction. If any check fails, show the proposal as unavailable or unsupported and disable acceptance/adoption.
- **FR-09-03 — Source navigation:** Provide an authenticated case-scoped source preview. PDFs open at the cited 1-based page. DOCX documents do not claim a physical page; show an accessible extracted-text view with the exact quote highlighted and state that page location is unavailable. Keep the existing download behavior.
- **FR-09-04 — Compare evidence:** Show the proposed field/value, exact supporting quote, source document, page when available, confidence, uncertainty, and source availability. A user can move between a suggestion and its source without losing the review state.
- **FR-09-05 — Review decisions:** Allow an authorized non-viewer member to accept, edit, or reject each proposal individually. Edited values are bounded plain text; the original proposal and quote remain unchanged. Rejecting a proposal makes it ineligible for adoption until a later explicit review decision changes it.
- **FR-09-06 — No unsupported acceptance:** A missing, changed, or unverifiable source cannot be accepted, edited into an approvable fact, or adopted. Rejected and unreviewed suggestions remain unapplied.

## 2. Explicit Adoption and Append-Only Profile Facts

- **FR-09-07 — Final confirmation:** Recording an accepted/edited review decision does not change case-profile data. Before adoption, show a final confirmation containing exactly the selected accepted/edited values and their evidence. Adoption requires a separate affirmative confirmation.
- **FR-09-08 — Selected subset:** The user may adopt any subset of the currently accepted/edited proposals; the entire analysis request is never implicitly adopted. Reject empty, duplicate, unreviewed, rejected, or unavailable proposal IDs.
- **FR-09-09 — Append-only facts:** Each adopted proposal creates an immutable case-profile fact with the adopted value, original and edited proposal values, proposal/analysis identity, source document ID and digest, exact quote, page/location, consent/model/version metadata, adopting user, review decision, and timestamp. Never overwrite an existing fact or unrelated case data.
- **FR-09-10 — Same-field conflicts:** Different facts for the same field key may coexist. Surface conflicting values and their sources; do not choose a winner or silently replace a prior fact. Resolving, superseding, or withdrawing a fact is an explicit append-only event that preserves the prior fact and decision history.
- **FR-09-11 — Idempotency and concurrency:** Review and adoption requests carry idempotency keys. Identical retries return the existing outcome; reuse with different content conflicts. Adoption locks the case profile revision and checks the caller's expected revision so concurrent requests cannot duplicate or overwrite data. A stale revision returns a conflict with the current revision and makes no partial changes.
- **FR-09-12 — Revisit decisions:** Provide authorized reads of current proposal decisions, adopted facts, and their history. Re-review or withdrawal appends a new event; it does not erase the earlier proposal, adoption, or audit record.

## 3. API and Authorization

- **FR-09-13 — Membership:** All review, evidence, and profile-fact reads require an active case membership. Only active non-viewer members may record decisions, adopt, supersede, or withdraw facts. Use a non-disclosing not-found response for absent or unauthorized case resources.
- **FR-09-14 — Case-scoped source access:** Source and extracted-text preview endpoints derive the storage key and document ownership server-side. Do not expose object keys, public/presigned URLs, or extracted text in logs. Source preview remains subject to case membership and document lifecycle.
- **FR-09-15 — Review API:** Provide case-scoped operations to retrieve proposals with their current evidence/review state and to append an accept, edit, or reject decision. Validate proposal/request/case relationships on the server.
- **FR-09-16 — Adoption API:** Provide a case-scoped operation to adopt the selected reviewed proposals with explicit confirmation, idempotency key, and expected profile revision. Persist selected facts and audit events atomically; on any validation, authorization, or persistence failure, create no partial adoption.
- **FR-09-17 — Profile facts API:** Provide case-scoped reads for adopted facts, conflicts, current profile revision, and decision history. Any action that changes a fact's effective disposition must append an auditable event.
- **FR-09-18 — Safe errors:** Return actionable, safe validation/conflict errors. Never expose stack traces, storage keys, raw provider output, or internal persistence details.

## 4. Accessible User Experience

- **FR-09-19 — Review flow:** Group suggestions by document or topic and show per-item review state. Users can inspect the source, accept, edit, or reject items, select a subset, inspect a final adoption summary, and explicitly confirm or cancel.
- **FR-09-20 — States:** Support loading, empty, unavailable-source, stale-source, partial-analysis, conflict, validation, network-error, and successful adoption states. Explain that no case-profile fact changes before final confirmation.
- **FR-09-21 — Accessibility:** All decisions, source navigation, selection, editing, and confirmation work with keyboard and screen readers; announce asynchronous status changes; use responsive layouts on mobile; do not rely on color alone for evidence or review state.

## 5. Retention and Operations

- Review decisions and adopted facts are case data and follow the configured case-data retention and deletion lifecycle.
- Preserve source identity, digest, quote, and location snapshots in adopted-fact history if the source document is later unavailable; show the source link as unavailable rather than implying it can still be opened.
- Audit records include actor, action, proposal/fact identity, timestamp, and idempotency outcome, but application logs exclude source text and quotations.
- No review or adoption operation calls an AI provider or changes the original analysis proposal.

## 6. Acceptance Criteria

1. Suggestions are never presented as verified facts or legal advice; unreviewed and rejected items remain unapplied.
2. Users can navigate to and compare the exact source quote; PDFs open at the cited page, while DOCX views truthfully show that physical page location is unavailable.
3. Users can accept, edit, and reject proposals independently, then explicitly confirm adoption of only a selected subset.
4. No profile fact is written before final confirmation; adopted facts are append-only and preserve source, consent/model, and review provenance.
5. Same-field conflicts are visible and never silently overwrite prior or unrelated data; supersede/withdraw operations preserve prior history.
6. Membership roles, source ownership, idempotency, optimistic concurrency, and transaction atomicity are enforced.
7. Keyboard, screen-reader, mobile, loading, empty, partial, conflict, unavailable-source, and error states are supported.
8. Tests cover source navigation and citation states, per-suggestion decisions, explicit subset adoption, authorization, conflicts, concurrent updates, retries, and provenance/audit persistence.

## 7. Out of Scope

- New AI analysis or changes to the consent/provider workflow.
- Automatically resolving conflicting legal or financial claims, interpreting law, or recommending settlement positions.
- Editing or deleting original analysis proposals or historical review/adoption events.
