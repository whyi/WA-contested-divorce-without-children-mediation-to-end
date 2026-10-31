# Spec 06: Secure Case-Material Storage

- **Status:** Draft
- **Related issue:** [#30 — Encrypt and securely persist imported case materials](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/30)
- **Depends on:** [#29 — Implement case-materials import page with cloud file pickers](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/29)
- **Related specifications:** [Spec 03: Authentication](../03-authentication/spec-03-authentication.md), [Spec 05: Case-Materials Selection and Import](../05-case-materials-import/spec-05-case-materials-import.md)
- **Objective:** Protect imported case documents in transit and at rest, enforce authorization on document retrieval and deletion, and make storage failures safe and retryable.
- **Scope:** This specification covers S3-compatible storage configuration, upload/read/delete operations, document metadata consistency, and retention/deletion behavior. It does not start text extraction or AI analysis.

## 1. Security and Availability Boundary

- Case-material storage is disabled by default and remains unavailable in demo mode.
- Enabling case-data APIs alone must not enable real case-material uploads. A separate explicit `CASE_MATERIALS_ENABLED` setting is required.
- `CASE_MATERIALS_ENABLED` may be enabled only when authentication and case-data access are enabled, production KMS encryption is configured where applicable, the bucket is private, and the source/derived-data retention policy has been approved.
- Authentication does not grant case access. Every read or delete must require an active case-membership grant for the requesting user.
- Storage credentials, object keys, KMS key identifiers, and presigned URLs must never be returned to the browser or written to application logs.
- Successful persistence does not start extraction, OCR, or AI analysis. Those are separate, explicitly authorized workflows.

## 2. Storage Configuration

- **FR-06-01 — Explicit encryption mode:** In deployed AWS S3, every uploaded object must request server-side encryption with AWS KMS (`aws:kms`) and the configured customer-managed KMS key. An absent key identifier must prevent case-material storage from starting.
- **FR-06-02 — Fail closed:** Production configuration must reject or disable `CASE_MATERIALS_ENABLED` when the required KMS key is missing or the configured endpoint is insecure. An S3 write must never silently fall back from KMS to SSE-S3 or plaintext.
- **FR-06-03 — Local development:** Local Moto/S3-compatible development may omit the KMS key only when using an explicitly configured loopback HTTP endpoint and when case-material imports remain disabled by default. Local development credentials must not be used in a shared or production deployment.
- **FR-06-04 — Transport security:** S3 endpoints using HTTPS are required outside loopback development. HTTP is allowed only for `localhost`, `127.0.0.1`, or `::1`; remote HTTP endpoints must be rejected during settings validation.
- **FR-06-05 — Private bucket:** Deployment must block all public bucket/object access and configure least-privilege application IAM permissions for the configured bucket and KMS key. No public ACL or public URL may be created.
- **FR-06-06 — No browser-direct storage:** Upload, retrieval, and deletion must pass through authenticated application APIs. Do not expose S3 credentials, bucket paths, or reusable object URLs to the client.

## 3. Upload and Persistence

- **FR-06-07 — Server-side validation:** Before writing to S3, independently validate PDF/DOCX extension, file structure/signature, non-empty contents, configured per-file size limit, and existing PDF page-count limit where processing occurs. Never trust client MIME type or metadata as validation.
- **FR-06-08 — Confirmed import only:** Store a file only after the user explicitly confirms the reviewed selection. Invalid files or authorization failures must not create an object, document record, or draft case.
- **FR-06-09 — Metadata minimization:** Store only metadata needed for authorization and document handling. Use opaque, unguessable object keys; filenames and document contents must not be embedded in object keys.
- **FR-06-10 — Consistent object and database state:** If S3 storage fails, roll back database changes and report a per-file retryable failure. If a database transaction fails after an object write, attempt to delete the newly written object and log cleanup failures without logging its content or credentials.
- **FR-06-11 — Idempotent retries:** Repeating an import request for the same batch and item must return the already-persisted document when it belongs to the same user and remains authorized. It must not create duplicate cases, metadata, or objects.
- **FR-06-12 — Partial success:** A failed file must not invalidate successfully stored sibling files. Return safe per-file status and permit retry of failed items only.
- **FR-06-13 — No premature success:** Report a file as stored only after its object write and corresponding metadata transaction succeed. An uncertain request result must be reconciled against persisted import status before retry.

## 4. Authorized Read and Delete

- **FR-06-14 — Authorized retrieval:** Every document download must verify that the authenticated user has an active membership in the document's case before reading from storage. Return a non-disclosing not-found response for absent or unauthorized documents.
- **FR-06-15 — Authorized deletion:** Provide an authenticated document deletion operation that applies the same active-membership check and rejects viewer-only memberships. Never accept a client-supplied object key as authority.
- **FR-06-16 — Delete consistency:** Deletion must remove the stored source object and its document metadata, import-item references, and associated derived extraction records. If object deletion fails, retain metadata and report a retryable error. If metadata cleanup fails after object deletion, report failure and permit an idempotent retry to finish cleanup.
- **FR-06-17 — No raw paths:** Download responses may contain the document's content only; they must not disclose an S3 key, bucket name, KMS key, or presigned URL.

## 5. Retention and Derived Data

- Until a separate retention schedule is approved, source documents are retained only while the user keeps them in the case and may be deleted by an authorized case member at any time. Deletion must take effect as soon as the storage and metadata cleanup completes.
- When a source document is deleted, all derived extraction text and document-linked records must be deleted or made inaccessible in the same logical operation.
- Future asynchronous jobs and AI analyses must retain a source-document reference and be cancellable or purgeable when that source is deleted. This specification does not implement those jobs.
- Do not enable real case-material storage until the deployment owner documents the approved retention schedule, backups/versioning behavior, legal holds, and deletion expectations for source files and derived artifacts.
- Object-store backups, replication, and versioning must be included in the documented deletion/retention policy; deleting the current object version alone must not be represented as physical erasure from retained backups.

## 6. Failure Handling and Observability

- Surface storage/configuration failures as explicit, safe retryable errors; do not silently substitute another encryption mode or return success-shaped fallbacks.
- Log operational failure context without document bytes, extracted text, filenames when not required, credentials, tokens, object URLs, or key material.
- A readiness or deployment validation check must make missing required storage configuration visible before enabling material imports.
- On a storage or database outage, keep document retrieval/deletion failures distinct from missing or unauthorized documents without leaking case existence across accounts.

## 7. Acceptance Criteria

1. Materials storage is disabled by default and cannot be enabled in demo mode or without authentication and case-data access.
2. With production AWS storage enabled, every object write requests SSE-KMS with the configured KMS key; missing key configuration fails closed and never downgrades encryption.
3. Remote non-HTTPS S3 endpoints are rejected; loopback HTTP remains available for local Moto development.
4. Upload, download, and deletion use private application APIs and never disclose S3 object keys, bucket details, credentials, or presigned URLs.
5. Uploads are server-validated and per-file size/page limits are enforced before storage.
6. S3/database failures yield explicit errors, roll back metadata, attempt cleanup of orphan objects, and remain safely retryable.
7. Batch/item retries return the existing authorized document without duplicate storage, database rows, or cases.
8. Download and deletion enforce active case membership; viewers cannot delete, and unauthorized users cannot infer document or case existence.
9. Deleting a document removes its object and linked database extraction/import metadata; retries complete cleanup after partial failure.
10. Retention and deletion behavior for source and derived data is documented, and real-material storage cannot be enabled until the deployment retention policy is approved.
11. Tests cover encryption headers and key configuration, endpoint transport rules, fail-closed feature gates, authorization, successful storage/read/delete, idempotency, and cleanup/error paths.
12. No extraction, OCR, or AI request is started by storage or upload completion.

## 8. Out of Scope and Deployment Decisions

- Selecting or provisioning the production AWS KMS key, IAM role, bucket, backup policy, and provider credentials.
- Asynchronous extraction, OCR, AI analysis, and user review; see the subsequent workflow specifications.
- Automatic retention expiration or legal-hold processing. These require an approved deployment policy before real material is enabled.
- Cloud-provider imports. Google Drive and Dropbox remain disabled until their OAuth applications, scopes, and token lifecycle are configured.
