# Spec 08: Consent-Based, Evidence-Grounded Document Analysis

- **Status:** Draft
- **Related issue:** [#32 — Add consent-based, evidence-grounded document analysis](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/32)
- **Depends on:** [#30 — Encrypt and securely persist imported case materials](../06-secure-case-material-storage/spec-06-secure-case-material-storage.md) and [#31 — Add asynchronous document extraction](../07-asynchronous-document-extraction/spec-07-asynchronous-document-extraction.md)
- **Coordinates with:** [#33 — Let users review and selectively adopt AI document suggestions](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/33)
- **Objective:** Let an authorized user explicitly consent to asynchronous Bedrock analysis of selected, already-extracted case documents and persist only schema-valid proposals whose quotations and provenance are verified against those documents.
- **Scope:** Consent disclosure and revocation, analysis request/job persistence, Bedrock invocation, exact-quote verification, proposal storage, safe status/retry APIs, and a minimal post-import consent/status experience. Human review and adoption are owned by issue #33.

## 1. Consent and Provider Disclosure

- **FR-08-01 — Explicit consent:** Upload, extraction, page load, status polling, and worker polling must never invoke an AI provider. A request is created only after an authenticated case member selects eligible documents and explicitly accepts the current notice.
- **FR-08-02 — Informed notice:** Before consent, show the configured provider (Amazon Bedrock), exact model ID and region, purpose, the fact that selected extracted document text is sent, and a deployment-supplied data-handling/retention notice. Record the notice version and a snapshot of the disclosed provider/model and text with the consent event.
- **FR-08-03 — Fail closed:** Analysis is unavailable unless an explicit `AI_ANALYSIS_ENABLED` flag, Bedrock model ID, Bedrock region, notice version, and non-empty data-handling notice are configured. Missing configuration must not create consent or jobs or call Bedrock.
- **FR-08-04 — Revocation:** A user may revoke consent for a request. Revocation prevents any queued job under that consent from calling Bedrock and cancels work that has not started. In-flight provider calls cannot be recalled; their outcome is persisted without initiating further calls.
- **FR-08-05 — Case authorization:** Consent, request, status, retry, revocation, and proposal reads require an active case membership. Viewer memberships may read status/proposals but cannot consent, start, retry, or revoke processing. Unauthorized and absent case resources remain non-disclosing.

## 2. Request and Durable Job Lifecycle

- **FR-08-06 — Eligible sources:** A request accepts only document IDs belonging to the requested case whose current extraction job is `completed`, whose extracted text and page provenance exist, and whose source digest still matches the document. `stored`, `queued`, `processing`, `needs_attention`, and `failed` extraction results are not eligible.
- **FR-08-07 — Durable queue:** Persist the consent event, analysis request, and one analysis job per selected document in PostgreSQL. Jobs survive API/worker restarts and use row locking and expiring leases for concurrent workers and crash recovery.
- **FR-08-08 — Idempotency:** The client supplies a request idempotency key. A repeat with the same user, case, key, notice, and selected document set returns the existing request; reusing the key with different inputs is a conflict. Document jobs are unique within the request and source digest.
- **FR-08-09 — Safe statuses:** Expose per-document `queued`, `processing`, `completed`, `partial`, `failed`, and `cancelled` states with safe error codes and timestamps. Request status is derived from its document jobs. Do not expose prompts, raw model output, object keys, credentials, or stack traces.
- **FR-08-10 — Retry:** Retry only a `failed` document job while its consent is not revoked, the source digest is unchanged, and the same request remains valid. Retry is per document and does not duplicate proposals. Completed or partial jobs are not retried.
- **FR-08-11 — Partial work:** A failure or invalid model output for one document must not block other jobs in the request. A document is `partial` when the response contains both verifiable and rejected proposals; only verifiable proposals are stored.
- **FR-08-12 — No unsolicited work:** The worker may poll the database without provider calls. It invokes Bedrock only for a queued job after rechecking consent, source identity, extraction completion, and configuration immediately before invocation.

## 3. Evidence-Grounded Proposals

- **FR-08-13 — Bedrock integration:** Reuse the configured Bedrock Converse client and keep credentials server-side. Send only the selected document's extracted text and provenance required for analysis; do not send unrelated account, case-profile, or negotiation data. Do not give the model tools or permission to change application state.
- **FR-08-14 — Structured output:** Validate model output against a strict schema. Each proposal includes a bounded field key, proposed value, source document ID, exact supporting quotation, optional 1-based PDF page number, confidence, and uncertainty. Extra fields and malformed responses are rejected.
- **FR-08-15 — Quote verification:** Verify each quotation as an exact substring of the cited source. For PDFs, the quoted text must match the cited page's extracted text. For DOCX, page location remains unavailable and the quotation must match the document-level extracted text. Discard fabricated, mismatched, or unsupported proposals; never repair or silently normalize quotes.
- **FR-08-16 — Provenance:** Persist the analysis request, provider/model configuration, consent reference, source document ID and SHA-256, page/location, exact quote, and proposal fields for traceability. Do not log document contents, prompts, quotations, or credentials.
- **FR-08-17 — Suggestions only:** Proposals are stored separately from case metadata and asset/liability data. Analysis never applies proposals, changes case status, generates legal forms, gives legal advice, or treats model output as verified fact. User review and explicit adoption are exclusively issue #33.
- **FR-08-18 — Untrusted content:** Treat every document as untrusted data. Instructions in a document cannot override the system prompt, obtain secrets, invoke tools, or cause side effects. Keep prompts and provider requests free of tools/function calling.

## 4. API and User Experience

- **FR-08-19 — Availability and notice:** Provide an authenticated case-scoped response with current provider availability, the exact disclosure/version, and per-document eligibility/status. A disabled or incomplete configuration returns unavailable without creating jobs.
- **FR-08-20 — Start request:** Provide a case-scoped endpoint that accepts the user-selected document IDs, idempotency key, current notice version, and explicit affirmative consent. Validate all inputs and commit the request/jobs promptly; do not run model inference in the API request.
- **FR-08-21 — Status and retry:** Provide authorized per-request/per-document status and a per-document retry operation. The retry path rechecks the same consent and eligibility requirements as the worker.
- **FR-08-22 — Proposal retrieval:** Provide a case-authorized, read-only proposal response for issue #33. Clearly label every item as an AI suggestion and include its exact quotation and source location; this endpoint never writes to the case profile.
- **FR-08-23 — Post-import flow:** After successful import, communicate that documents are stored but not analyzed. Offer analysis only when enabled and disclose the provider, data sent, purpose, and handling notice before the final consent action. Show per-file progress, partial/failure states, and a safe retry for failed files. Preserve keyboard, screen-reader, mobile, loading, empty, and unavailable states.

## 5. Retention and Operations

- Revoking consent cancels queued jobs and prevents retries; it does not claim to recall content already sent to Bedrock.
- Deleting a source document removes its analysis jobs and proposals through database cascades. Workers must recheck document existence and digest before sending content or persisting results.
- Worker logs may contain job IDs, status transitions, and safe error codes, but no filenames, object keys, document text, quotations, prompts, provider payloads, or credentials.
- Configure and document AWS IAM, model access, region, and data-handling/retention notice before enabling analysis in a deployment. The feature is disabled by default.

## 6. Acceptance Criteria

1. No provider call occurs on upload, extraction, page load, status polling, or idle worker polling.
2. No analysis request can be created without explicit informed consent and a complete, enabled Bedrock configuration.
3. Every job revalidates consent, case ownership, extraction completion, and source digest before sending selected text.
4. Output is schema-validated; only exact, source-verifiable quotations and citations become persisted proposals.
5. PDF citations identify the exact 1-based page; DOCX citations truthfully report unavailable physical page location.
6. Jobs are asynchronous, durable, idempotent, recoverable, independently retryable when failed, and support partial outcomes.
7. Revocation blocks queued provider calls and retries; in-flight calls are not misrepresented as recalled.
8. Proposals remain separate from case data and are never automatically adopted.
9. Authorization, viewer restrictions, safe errors, privacy-preserving logs, deletion cascades, and keyboard-accessible consent/status states are tested.

## 7. Out of Scope

- Human proposal review, editing, acceptance/rejection, and adoption into case data; see issue #33.
- OCR, legal conclusions, legal advice, recommendations, settlement offers, or automatic form generation.
- Cloud-drive provider connections and account-wide consent beyond the specific case and selected analysis request.
