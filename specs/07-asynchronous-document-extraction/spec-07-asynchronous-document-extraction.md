# Spec 07: Asynchronous Document Extraction

- **Status:** Draft
- **Related issue:** [#31 — Add asynchronous document extraction and per-file job status](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/31)
- **Depends on:** [#30 — Encrypt and securely persist imported case materials](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/30)
- **Coordinates with:** [#32 — Consent-based, evidence-grounded document analysis](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/32)
- **Objective:** Extract text from stored PDF and DOCX case documents in a durable worker, preserve source/page provenance, and report safe per-file status without blocking API requests.
- **Scope:** This specification covers extraction job persistence, worker claiming and recovery, text extraction, OCR-needed detection, status reporting, retry behavior, authorization, and cleanup when a source document is deleted. It does not call an AI provider or perform OCR.

## 1. Consent and Processing Boundary

- A successful upload remains in `stored` state. Upload, page load, status polling, and worker startup must not start extraction.
- Extraction jobs may be enqueued only by a server-side analysis-request workflow after it has verified a current, affirmative user consent. Issue #32 supplies that consent workflow and invokes the extraction queue.
- This issue may provide internal enqueue and retry services for the consent workflow, but must not expose an unauthenticated or consent-free way to create or retry jobs.
- Extracted text is sensitive case data. It must remain server-side, be available only to authorized case members, and never be sent to an AI provider by this worker.

## 2. Durable Job Lifecycle

- **FR-07-01 — Durable queue:** Persist extraction jobs in PostgreSQL so queued and active work survives API or worker restarts. Do not use an in-memory queue as the source of truth.
- **FR-07-02 — Idempotency:** Identify a job by document, immutable document content digest, and consented analysis-request identifier. Repeated enqueue requests for the same tuple return the existing job rather than duplicate work or extraction results.
- **FR-07-03 — Claim and recovery:** Workers claim jobs transactionally using row locks that allow multiple workers to cooperate. A processing lease must expire so abandoned jobs can be recovered after a worker crash.
- **FR-07-04 — Statuses:** Expose safe per-file states: `stored`, `queued`, `processing`, `needs_attention`, `failed`, and `completed`. Persist timestamps, bounded attempt counts, and stable safe error codes; never return stack traces or internal paths.
- **FR-07-05 — Retry:** Retry only failed or explicitly retryable jobs, under the same valid consent request. A retry must not duplicate completed extraction output. Malformed, encrypted, or OCR-needed documents must not be blindly retried as infrastructure failures.
- **FR-07-06 — Partial work:** A failure for one document must not block other jobs in the same user request. Job status and retry are per document.

## 3. Extraction and Provenance

- **FR-07-07 — PDF pages:** Extract selectable text separately for each PDF page, preserve 1-based page numbers, enforce the existing upload-byte and maximum-page limits, and retain the page-level text alongside the aggregate extraction.
- **FR-07-08 — DOCX source location:** Extract paragraphs and tables from DOCX. Do not invent physical page numbers because pagination depends on rendering; mark the source location unavailable while preserving document-level provenance.
- **FR-07-09 — OCR-needed state:** OCR is not configured in this issue. If a PDF page has no selectable text, preserve any text that was extracted but mark the file `needs_attention` with a safe `ocr_required` error code. Do not present it as fully analyzed or eligible for AI processing.
- **FR-07-10 — Invalid and protected files:** Malformed, unsupported, unreadable, or password-protected files receive an actionable per-file `needs_attention` state with a stable safe code. Never log document bytes or extracted text.
- **FR-07-11 — Persist once:** Store extracted text, page boundaries, source document ID, and content digest transactionally with job completion. A failed transaction must leave no success-shaped status or duplicate extraction result.
- **FR-07-12 — No untrusted instructions:** Treat file contents strictly as data. Extraction does not interpret document instructions, call tools, or alter account or case state.

## 4. API and Authorization

- **FR-07-13 — Status access:** Authenticated users may query processing status only for documents in cases where they have an active membership. Return a non-disclosing not-found response for absent or unauthorized documents.
- **FR-07-14 — Retry access:** Retrying a failed job requires an active non-viewer case membership and a still-valid consent request. The client cannot choose a storage key, source digest, job owner, or consent record.
- **FR-07-15 — Prompt response:** Consent-authorized enqueue requests return job identifiers and current per-file states promptly; no extraction work runs in the request handler.
- **FR-07-16 — Safe errors:** Storage, database, and extraction failures return explicit safe statuses and do not reveal object keys, extracted text, credentials, or internal stack traces.

## 5. Retention and Operations

- Deleting a source document removes its extraction job records and all extracted page/text data. A worker must re-check that the source document still exists before persisting output.
- Workers read source content through the authenticated server-side storage service; they never create public or presigned object URLs.
- Run the worker as a separate process from API request handling. PostgreSQL is the durable queue; a restart resumes queued or expired-lease work.
- Worker logs may include job state and safe error codes, but must exclude filenames, object keys, source text, credentials, and provider payloads.
- No AI analysis or OCR request starts in this issue. OCR language/provider policy and AI consent/provider behavior are handled in later specifications.

## 6. Acceptance Criteria

1. Upload does not enqueue or execute extraction; only the consent-verified analysis workflow can enqueue a job.
2. Queue state survives API and worker restarts, recovers expired work, and prevents concurrent duplicate processing.
3. PDF text is stored with exact 1-based page boundaries; DOCX text records that physical page location is unavailable.
4. OCR-needed, malformed, encrypted, and unsupported files receive safe actionable statuses without blocking sibling files.
5. Status and retry operations enforce case membership, viewer restrictions, and consent requirements without disclosing case existence.
6. Retry is idempotent and only repeats failed eligible work; successful extractions are not duplicated.
7. Deleting a document also deletes queued jobs and extracted text; workers cannot persist results for a deleted source.
8. No AI or OCR provider is called, and no document content or object key is logged.
9. Tests cover durable job persistence/claiming, idempotency and recovery, extraction/page provenance, consent gates, authorization, partial failure, and retry.

## 7. Out of Scope and Deployment Decisions

- OCR engines, OCR language selection, and OCR result correction.
- AI provider calls, evidence proposals, or automatic changes to case data; see issues #32 and #33.
- User-configurable retention schedules and legal-hold processing; see Spec 06.
