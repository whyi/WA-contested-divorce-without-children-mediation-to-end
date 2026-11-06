# Spec 45: Failure Messaging, Safe Recovery, and Support Escalation

- **Status:** Implemented in part; deployment-owned support and alert routing remain required
- **Related issue:** [#141 — Complete failure messaging, retry, and support escalation paths](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/141)
- **Related specifications:** [Spec 07: Asynchronous Document Extraction](../07-asynchronous-document-extraction/spec-07-asynchronous-document-extraction.md), [Spec 08: Consent-Based Document Analysis](../08-consent-based-document-analysis/spec-08-consent-based-document-analysis.md), [Spec 35: Attempt Finalization](../35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md), [Spec 36: Attempt Credits](../36-attempt-credit-packages/spec-36-attempt-credit-packages.md), [Spec 38: Failure Recovery](../38-failure-recovery/spec-38-failure-recovery.md)
- **Objective:** Give users concrete, privacy-safe recovery instructions for upload, extraction/OCR, AI analysis, proposal generation, and download failures, and give operators safe signals to triage them.
- **Preserved policy:** Spec 38 and #125 remain authoritative: retain saved work, keep failed work editable/retryable where safe, and never permanently consume a paid attempt credit when finalization fails. This spec adds detail; it does not weaken those remedies.

## Requirements

- **FR-45-01 — Upload:** Explain that failed files remain retryable and successful sibling files remain stored. A lost response is an uncertain outcome, not proof of failure: reconcile the existing import item first; if it was not stored, reselect the same file to reuse its identity. Never retry a different file under the same item identity.
- **FR-45-02 — Extraction/OCR:** A failed extraction must say the source remains stored and offer retry only while the matching source/job remains eligible. For `needs_attention` (including OCR unavailable, unsupported, or unreadable content), explain that extraction did not complete and give a next step; do not offer the failed-job retry as if it could resolve an unsupported source. Do not retry while queued or processing.
- **FR-45-03 — AI analysis:** Explain that a failed file can be retried under the existing consent and source identity, and successful sibling results remain available. A revoked/missing consent or changed source disables retry. A partial response is never presented as complete.
- **FR-45-04 — Proposal generation/download:** A failed draft leaves saved attempt inputs unchanged and editable. If finalization's result is uncertain, reconcile attempt status before continuing; if finalized, the same saved snapshot may be downloaded again without another debit. If not finalized, retry the same operation. A download failure is not proof of generation failure or of delivery to another person.
- **FR-45-05 — Retry safety:** Disable duplicate submissions while a request is in flight, and do not offer retry unless the existing operation state and prerequisites make it safe. Preserve the existing idempotency keys, source-digest checks, consent checks, transaction boundaries, and finalization idempotency. No arbitrary retry count or automatic retry loop is introduced.
- **FR-45-06 — Support action:** When configured, provide a support link without embedding diagnostics or case data. Provide an optional copyable diagnostic summary containing only operation category, UTC observation time, HTTP status when available, a known safe error code, and a random client reference. The user must explicitly send it. Do not include filenames, case/document/user IDs, contents, credentials, cookies, tokens, object keys, prompts, or provider responses.
- **FR-45-07 — Safe operational signals:** Emit stable failure event codes, coarse severity, and exception class only. Logs and alerts must not contain request/response bodies, source text, file names, identifiers, credentials, or raw exception messages. The existing deployment log collector must route these signals according to the accompanying runbook.
- **FR-45-08 — Partial success and retention:** One file's failure must not invalidate successfully imported, extracted, or analyzed siblings. Persisted inputs, source documents, successful outputs, and credit ledger state remain available according to their existing lifecycle.

## Recovery messages and operator classification

| Class | User guidance | Default signal |
|---|---|---|
| Upload | “This file could not be confirmed as stored. We’ll check whether it arrived before retrying. Saved files are kept; reselect the same file only if asked.” | `upload_storage_failed` / `upload_persistence_failed`, SEV2 |
| Extraction/OCR | “The source is still stored. Retry a failed extraction; if this file needs attention, use an OCR-capable/ supported source path or contact support.” | `extraction_job_failed`, SEV2 |
| AI analysis | “This file’s analysis did not complete. Successful files remain available. Retry this file only while the original consent is active.” | `analysis_job_failed`, SEV2 |
| Proposal generation | “Your saved attempt remains editable if finalization did not complete. Check attempt status before retrying.” | `proposal_generation_failed`, SEV2 |
| Download | “The download may have been interrupted. Check whether the attempt finalized; re-download the same snapshot if it did.” | `proposal_generation_failed` / `document_download_failed`, SEV2; browser-only failures are reported only if the user shares diagnostics |
| Systemic/repeated | Stop exposing new retries only when an operation is already in flight or its source/prerequisites are no longer valid. Alert operators using the deployment-configured grouping threshold; do not invent a retry ceiling. | SEV1 when multiple users/workflows or data integrity are affected; route per deployment configuration |

## Acceptance criteria

1. Each failure class has a clear user state, safe next action, and a non-sensitive diagnostic summary.
2. Retry and reload/timeout behavior reuses existing idempotency, job, consent, and finalization identities.
3. Partial successes and user work are retained; generation/download failures do not duplicate artifacts or debit credits twice.
4. Logs/alerts omit sensitive contents and unnecessary identifiers.
5. Before production launch, operators fill the routing and response-target placeholders in the runbook and configure the deployed log/alert platform. No contact address, on-call identity, SLA, provider, or retry ceiling is assumed by this specification.

## Implementation and verification

- Existing retry/idempotency logic from Spec 38 is reused.
- User-facing recovery copy and client-only safe diagnostics are added for the processing and proposal workflows.
- The runbook defines severity semantics and contains deployment-required routing/response placeholders.
- External alert delivery, support destination, and response targets are deployment policy and are not considered configured by source code alone.
- **Not yet launch-complete:** the deployment has not supplied a support URL, alert routes/grouping thresholds, on-call owner, or response targets; the repository has no alerting provider integration. Browser-only download interruptions are not automatically sent to the server and reach operators only when the user shares the copied diagnostic. Keep issue #141 open until these requirements are confirmed.
