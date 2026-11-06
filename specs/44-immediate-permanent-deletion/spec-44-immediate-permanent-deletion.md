# Spec 44: Immediate Permanent Deletion

- **Status:** Application deletion boundary documented; provider backup/version guarantees unresolved
- **Related issue:** [#134 — Immediately honor permanent deletion of accounts and case materials](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/134)
- **Related specifications:** [Spec 06: Secure Case Material Storage](../06-secure-case-material-storage/spec-06-secure-case-material-storage.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md)
- **Objective:** Provide an explicit, permanent deletion action separate from reversible case closure, and define a fail-closed boundary for what this application can truthfully promise.
- **Scope:** Deletion of a case's source materials and derived case data, a whole case, or an account's data; authorization, confirmation, retries, stale work, and storage lifecycle.

## Policy and lifecycle separation

- **FR-44-01 — Deletion is explicit:** Permanent case-material deletion, whole-case deletion, and account deletion are distinct confirmed actions. None is triggered by closing, stopping, finalizing, or reopening a case.
- **FR-44-02 — Closure remains reversible:** Spec 32 governs close/reopen. Closure does not delete or tombstone anything, alter credits, or start a retention period. Reopen restores the same case and data.
- **FR-44-03 — Scope is explicit:** A material deletion removes that source document and all document-scoped extractions, analysis requests/jobs/proposals/review records, and import-item references. A case deletion removes all case-scoped structured records, jobs, source objects, generated proposal artifacts, exports under application control, and membership. Account deletion removes the user's credentials and account data, plus cases whose deletion is explicitly included in the confirmed scope. Shared-case/account ownership and transfer behavior must not be inferred.
- **FR-44-04 — Authorization and confirmation:** Only an authenticated case owner may permanently delete case materials or a case. Account deletion requires recent account verification and an unmistakable account-deletion confirmation. Non-owners and unauthenticated callers receive no data or success-shaped response.
- **FR-44-05 — Immediate application unavailability:** Once a deletion operation reports application deletion complete, the selected scope is unavailable through every application route, export, storage lookup, job, cache, and stale retry path. Deletion is idempotent. Persisted tombstones/denial records prevent a retry or stale import/job from recreating the deleted scope. A failed operation reports failure and remains safely retryable.
- **FR-44-06 — No misleading completion:** A response may say "deleted" only for the precise scope and storage boundary actually verified. If provider object versions, provider-managed backups, replicas, or disaster-recovery snapshots may retain the bytes, the application must not claim their immediate purge or overall permanent deletion.

## Current implementation boundary

The application currently stores source objects through a generic S3-compatible adapter. Its `delete` operation sends `DeleteObject(Bucket, Key)` and does not inspect bucket versioning, enumerate object versions, identify lifecycle/replication rules, or control provider backups and disaster-recovery snapshots. In a versioned S3 bucket, deleting by key can create a delete marker while older object versions remain retrievable to principals with version access. The repository has no provider retention/backup configuration or permission evidence proving those copies can be synchronously purged.

Database rows have many `ON DELETE CASCADE` constraints, but this is not by itself a deletion protocol: source objects are outside the database; case exports can include derived records; and workers may hold leases while deletion races them. The current extraction and analysis queues are database-backed polling workers (not Redis/Celery), and generated proposal DOCX/XLSX data is stored in database rows. Export responses use `Cache-Control: no-store`; there is no application-managed shared cache observed in the current code.

Therefore this specification does **not** certify that provider versions/backups are synchronously erased. Product/infrastructure must decide whether to configure and verify a purgeable storage/backup regime or explicitly revise the acceptance policy. No grace period or asynchronous purge may be presented as meeting this issue.

## Acceptance criteria

1. Closing then reopening preserves the case, source and derived data, history, and remaining credits; closure has no deletion side effects.
2. Confirmed deletion of a material or whole case removes active database metadata/derived artifacts and application-addressable source objects before returning success.
3. Authorization is enforced for each scope, and confirmation is explicit and distinct from close/reopen.
4. Partial failures are reported. Retrying is idempotent; stale sessions, uploads, extraction/analysis jobs, and exports cannot recreate or access deleted data.
5. Tests verify real cascade behavior, source and derived cleanup, authorization, retries/failures, stale work denial, and non-destructive closure.
6. The system reports the provider-version/backup limitation and does not claim full deletion until the infrastructure guarantee is verified.

## Delivery status and unresolved decision

This additive specification records the policy without modifying historical specs. A deployable end-to-end implementation cannot claim all of issue #134's acceptance criteria until the object-store versioning and backup/restore guarantees are established and tested. If application deletion is shipped before that decision, it must be described as deletion from active application data only, and the issue must remain open.
