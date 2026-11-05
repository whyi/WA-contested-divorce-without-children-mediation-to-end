# Spec 35: Attempt Finalization and Snapshot on Final Proposal Download

- **Status:** Implemented; automated tests passing
- **Related issue:** [#121 — Finalize and snapshot an attempt on successful final proposal download](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/121)
- **Related specifications:** [Spec 23: Explicit Sent Confirmation Freeze](../23-explicit-sent-confirmation-freeze/), [Spec 28: Rejection Continuation and Negotiation Attempt Limits](../28-negotiation-attempt-limits/spec-28-negotiation-attempt-limits.md), [Spec 29: Explicit Proposal Document Credit Consent](../29-document-credit-consent/spec-29-document-credit-consent.md), [Spec 33: Existing Opposing Offer Intake](../33-existing-offer-intake/spec-33-existing-offer-intake.md)
- **Superseded historical requirements:** No historical spec is edited. This spec supersedes the following only for the stated aspect:
  - FR-29-05 (revised versions): a proposal version of a **finalized** attempt cannot be unlocked for revision; creating a new editable version of a non-finalized attempt is unchanged.
  - Spec 23 / Spec 28 sent-confirmation as the *only* read-only boundary: finalization is an additional, earlier read-only boundary for negotiation content. Sent confirmation, outcome recording and `frozen_at` keep their Spec 23 meaning and are not set by finalization.
  - FR-28-08 / FR-28-09 (lock on first issued draft): a draft download still pins that version's terms (unchanged), but only the explicit final-download action finalizes the attempt.
- **Out of scope / deferred:** Attempt-credit packages, the free first attempt, package pricing, subscription removal and the credit-balance UX are decided in #122. This spec makes **no** entitlement or pricing decision; see FR-35-06.
- **Objective:** Make a confirmed, successful final mediator-facing proposal download the single boundary that snapshots and locks the whole negotiation attempt, without double charging and without claiming external delivery.
- **Scope:** Server finalization state, snapshot, immutability, idempotency and failure semantics on the real-case DOCX/XLSX download routes; response/history read models; minimal confirmation UI. Not in scope: demo exports, payment, the next-attempt flow (Specs 24/28 unchanged), and tracking external delivery (Spec 23/#109).

## Definitions

- **Final-download action:** a DOCX or XLSX download request with `finalize=true` and `confirm_finalization=true`. Plain downloads (drafts) remain distinct and never finalize.
- **Finalized attempt:** an attempt with `finalized_at` set, a persisted `finalized_snapshot_json`, the finalized proposal version ordinal, and the finalizing account's id snapshot.
- **Entitlement charge:** whatever the current credit policy debits for the finalized proposal version. Today (Spec 29) that is the single document-credit debit recorded with the version; #122 may replace it.

## Requirements

- **FR-35-01 — Distinct action and confirmation:** Draft editing, previews and plain downloads never finalize. Finalization requires `finalize=true` plus a server-checked `confirm_finalization=true`; otherwise the server returns 428 and changes nothing. Cancelling the client confirmation sends no request, so there is no charge and no lock.
- **FR-35-02 — Finalizing snapshot:** On success, in the same transaction as any new proposal version, persist `finalized_snapshot_json` containing the attempt inputs (profile, ledger, revisions), the complete negotiation state (both sides' values and every editable attempt value), scenario assumptions and result, proposal terms, proposal version ordinal/id/request digest, SHA-256 digests of the stored DOCX and XLSX, the entitlement charge record (policy name, credit cost), and `finalized_at`. The snapshot states `externally_sent: false`.
- **FR-35-03 — Server-side immutability:** After finalization every route that could alter negotiation content or the proposal is rejected with 409: attempt-state updates with changed content, scenario recalculation, new proposal versions, and generation with different terms. Workflow-only fields (`sent_offer_mode`, `modified_offer_reviewed`) and recording sent documents/outcome remain governed by Specs 23/27 because they do not change negotiated terms.
- **FR-35-04 — Idempotent finalization:** Finalization is serialized by the case lock. A repeated or concurrent final-download for the same attempt and identical terms returns the stored finalized version, creates no second snapshot, version or ledger entry, and never debits again. A request with different terms is rejected.
- **FR-35-05 — Free re-download:** Plain or finalizing DOCX/XLSX downloads and delivery of the finalized version use the stored bytes at no charge.
- **FR-35-06 — No double charge; policy seam:** Finalization introduces **no charge of its own**. If the final-download action must generate a new proposal version, it uses the existing Spec 29 path and records exactly one debit with that version. If the exact version was already generated and paid, finalizing it debits nothing. A single finalization therefore results in at most one debit across generation and finalization. The charge stays isolated in proposal-version generation and is only *recorded* in the snapshot, so replacing it (#122) does not change snapshot semantics.
- **FR-35-07 — Failure preserves editability:** If rendering, size validation, revision checks, insufficient balance or persistence fails, the attempt is not finalized, no snapshot exists, the attempt remains editable, and the balance and ledger are unchanged (debit, version and finalization commit atomically; a failed commit rolls back any debit).
- **FR-35-08 — Not proof of delivery:** Finalization does not set `sent_confirmed_at`, `frozen_at`, an outcome, or any delivery record, and the UI says the user must separately attach and confirm what they sent. The proposal is a mediator-facing document; no route sends it to the other party, and the UI makes no legal conclusion.
- **FR-35-09 — Security preserved:** Authentication, case write authorization, CSRF protection, attempt revision checks, stale-revision checks and `Cache-Control: no-store` are unchanged. Finalization bumps the attempt revision so stale clients must reload.
- **FR-35-10 — Read models and UI:** Response and history read models expose `finalized`, `finalized_at` and `finalized_version_ordinal`. The UI offers a separate "Finalize attempt and download final proposal" control with an explicit confirmation, locks inputs when finalized, and shows that re-downloading the snapshot is free.

## Acceptance criteria

1. Before finalization, both sides' values can be edited and calculations update.
2. A final download without `confirm_finalization` fails with 428 and leaves the attempt unchanged.
3. A confirmed successful final download persists the snapshot and finalizes the attempt; the version's single debit (or none if already paid) is the only charge.
4. Repeating the final download, or running it for the second file format, is free and creates no new version, snapshot or ledger entry.
5. After finalization, content edits, scenario changes, new versions and different-term generation are rejected server-side.
6. A render, persistence or balance failure leaves the attempt editable, unfinalized and uncharged.
7. Finalization does not mark the attempt sent or frozen.
8. Migration `0019_attempt_finalization` adds nullable columns only and is reversible.

## Known limitations

- The server cannot observe whether the browser saved the downloaded file; "successful" means the server rendered, persisted and is returning the files.
- Continuing to the next attempt still requires the Spec 23/28 sent confirmation and outcome; #109/#88 may relax this.
- Database-level write protection of finalized rows (triggers) is not added; immutability is enforced in the application under the case lock.
- Attempt credits, the free first attempt and package pricing belong to #122.
