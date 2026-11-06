# Spec 44: Immediate Permanent Deletion

- **Status:** Implemented for active application data and application-level restore reconciliation; provider restore exercise remains outstanding
- **Related issue:** [#134 — Immediately honor permanent deletion of accounts and case materials](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/134)
- **Related specifications:** [Spec 06: Secure Case Material Storage](../06-secure-case-material-storage/spec-06-secure-case-material-storage.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md)
- **Objective:** When a user confirms deletion, remove everything under application control immediately, separately from reversible case closure, and fail closed at any unsupported storage boundary.
- **Scope:** Deletion of a case's source materials and derived case data, a whole case, or an account's data; authorization, confirmation, retries, stale work, and storage lifecycle.

## Policy and lifecycle separation

- **FR-44-01 — Deletion is explicit:** Permanent case-material deletion, whole-case deletion, and account deletion are distinct confirmed actions. None is triggered by closing, stopping, finalizing, or reopening a case.
- **FR-44-02 — Closure remains reversible:** Spec 32 governs close/reopen. Closure does not delete or tombstone anything, alter credits, or start a retention period. Reopen restores the same case and data.
- **FR-44-03 — Delete everything in the selected scope:** A material deletion removes its source bytes and every document-scoped extraction, analysis request/job/proposal/review record, and import-item reference. A case deletion removes all case-scoped structured records and generated artifacts, source objects, jobs, export records and memberships. Account deletion removes the account's credentials, tokens, connections, audit-identifying data, and every case owned by the account; invitations addressed to the deleted account in other people's cases are revoked and their email address is scrubbed. The deleting account's membership is removed from other people's cases, but those cases and their remaining case data are preserved.
- **FR-44-04 — Authorization and confirmation:** Only an authenticated case owner may permanently delete case materials or a case. Account deletion requires recent account verification and an unmistakable account-deletion confirmation. Non-owners and unauthenticated callers receive no data or success-shaped response.
- **FR-44-05 — Immediate application unavailability:** Once a deletion operation reports application-data deletion complete, the selected scope is unavailable through every application route, export, storage lookup, job, and stale retry path. Deletion is idempotent. Durable deletion tombstones block stale in-app work and remain in the active database after content rows are removed. A failed operation reports failure and remains safely retryable.
- **FR-44-06 — S3 object versions:** The supported production backend is AWS S3 and the local backend is Moto's S3-compatible API. Deletion enumerates and purges all versions and delete markers for each known source-object key; missing version-list/delete-version permissions fail the operation. This guarantee covers only the configured bucket and known keys, not provider-managed snapshots or independent replicas.
- **FR-44-07 — No misleading completion:** A response may say "deleted" only for the precise scope and storage boundary actually verified. Never claim immediate purge of provider-managed database backups, snapshots, replicas, or disaster-recovery copies unless that infrastructure is configured and its restore flow is verified to consume deletion tombstones.

## Current implementation boundary

The application stores source objects through an S3-compatible adapter. The deletion implementation enumerates exact-key object versions and delete markers and deletes them individually. Its success depends on provider credentials granting `ListBucketVersions` and `DeleteObjectVersion`; failures are explicit and retryable. In an S3-compatible backend that does not implement these operations, deletion fails closed.

Database rows have many `ON DELETE CASCADE` constraints, but this is not by itself a deletion protocol. The application writes opaque deletion intents to the dedicated, versioned `DELETION_LEDGER_BUCKET` before committing database tombstones or purging external objects. The API replays that external ledger before accepting traffic whenever case data is enabled; readiness fails if the bucket is unavailable, versioning is disabled, or the initialization marker is missing. Reconciliation restores tombstones, purges any restored source-object versions, and removes restored case/document/account rows and derived records. The ledger bucket must be separate from the database backup boundary and protected from deletion by the application identity; see [the restore procedure](../../docs/deletion-ledger-restore.md).

The one-time initialization command copies tombstones from the authoritative live database and is intentionally not an automatic fallback. A deployment that has already lost its only post-deletion database state without an initialized independent ledger cannot infer historic deletion requests from an older snapshot. Never initialize from a stale restored snapshot and claim protection.

The current extraction and analysis queues are database-backed polling workers (not Redis/Celery). Export responses use `Cache-Control: no-store`; no shared application cache is configured in the repository.

The repository includes Docker Compose for local Postgres and Moto only. It has no production database backup/snapshot policy, backup inventory, point-in-time restore procedure, or restore hook that reconciles tombstones from a separately protected deletion ledger. A database restore from a snapshot preceding deletion can therefore restore both content rows and omit the tombstone. No code change can truthfully guarantee non-resurrection from those unobservable provider-managed backups. This is the remaining infrastructure blocker; no user policy decision is pending.

## Acceptance criteria

1. Closing then reopening preserves the case, source and derived data, history, and remaining credits; closure has no deletion side effects.
2. Confirmed deletion of a material, case, or account removes application database data and all known S3 object versions/delete markers before returning success.
3. Authorization is enforced for each scope, and confirmation is explicit and distinct from close/reopen.
4. Partial failures are reported. Retrying is idempotent; stale sessions, uploads, extraction/analysis jobs, and exports cannot recreate or access deleted data.
5. Tests verify real cascade behavior, source and derived cleanup, authorization, retries/failures, stale work denial, and non-destructive closure.
6. S3 version purge fails closed when provider operations are unavailable; the system never claims to purge unconfigured provider-managed backups.
7. Deletion intents are durably written to the independent ledger before the database barrier; a failed ledger write prevents deletion from being reported as started.
8. API startup and readiness fail closed until the external ledger is initialized and versioned; startup reconciles the ledger before serving case-data routes.
9. A restore exercise against the deployment's actual database backup and object-storage providers must pass and be recorded before issue closure.

## Delivery status and unresolved decision

This additive specification records the confirmed policy without modifying historical specs. Active application deletion, S3 object-version deletion, and code-driven restore reconciliation are implemented. Issue #134 remains open until the production ledger is initialized with the authoritative tombstone history, its IAM/retention controls are verified, and an actual deployment backup restore exercise proves reconciliation before traffic resumes.
