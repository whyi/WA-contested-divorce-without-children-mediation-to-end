# Production Security, Backup, and Restore Readiness

This is an operator checklist, not a production sign-off. See [Spec 50](../specs/50-production-security-backup-and-restore-readiness/spec-50-production-security-backup-and-restore-readiness.md), [Spec 44](../specs/44-immediate-permanent-deletion/spec-44-immediate-permanent-deletion.md), and the [failure-recovery runbook](issue-141-failure-recovery-runbook.md).

## What this repository can and cannot verify

| Area | Evidence in this repository | Not observed / release blocker |
|---|---|---|
| Deployment | `docker-compose.yml` runs local Postgres and Moto; `Dockerfile` runs the API as a non-root user and disables Uvicorn access logs. | No production deployment definition, production network/TLS configuration, ingress policy, or release owner is present. Compose is not a production template. |
| Authentication and membership | Authentication, session, and case delegation/membership denial paths have automated tests (`tests/test_auth.py`, `tests/test_auth_routes.py`, `tests/test_case_delegation.py`, and `tests/test_main.py`). | No deployed identity provider, secret-manager policy, production session review, or live authorization exercise is recorded. |
| Storage and deletion | Case-material storage requires KMS in production configuration; deletion tombstones block active application access and S3 version deletion is tested (`tests/test_storage.py`, `tests/test_deletion.py`). PR #167 adds a separate versioned deletion ledger and restore reconciliation (`tests/test_deletion.py`, `tests/test_storage.py`). | No production bucket/IAM/KMS policy or backup inventory is present. Ledger initialization, retention controls, and provider-level access policies have not been verified. |
| Database backups and restore | [The deletion-ledger runbook](deletion-ledger-restore.md) documents one-time initialization and restore commands. API startup and both workers reconcile the ledger before serving or polling when case-data access is enabled. | No production backup inventory, retention setting, or actual restore evidence is recorded. An initialized and separately protected ledger plus a successful provider restore exercise are still required before recovered data may be exposed. |
| Payments | Automated Stripe route tests and Spec 49 cover application-side checks. | Issue #138 remains open. No Stripe test-mode purchase/refund/chargeback evidence, webhook delivery test, or production review is recorded. Configured identifiers alone are not provider evidence. |
| AI privacy/legal gate | AI analysis defaults off and requires explicit user consent and deployment-supplied notices. Production readiness rejects enabled AI while its legal-use review is unverified. | Issue #128 remains open. No counsel review of vendors, processing, retention, training/improvement, subprocessors, and disclosures is recorded. Keep AI disabled. |
| Monitoring and alerts | `/healthz` provides process liveness; `/readyz` checks database and bucket availability plus configured readiness requirements. Issue #141 documents failure categories and response guidance. | No monitoring provider, uptime/error/job/payment alert route, on-call assignment, alert-delivery test, or incident record is configured here. Health endpoints do not create alerts. |

## Fail-closed application configuration

`PRODUCTION_READINESS_REQUIRED=false` is the local-development default. A deployment that intends to serve real case data must set it to `true` through protected deployment configuration. Do not copy secret values into this checklist or source control. Inject `AUTH_JWT_SECRET`, `AUTH_ENCRYPTION_KEY`, storage/payment credentials, and other secrets through the approved secret manager.

With the flag enabled, readiness checks require:

- demo mode off; authentication and case/material access on; strong authentication signing/encryption keys and secure cookies;
- production KMS configuration, no local/Moto object-store endpoint, and an HTTPS support URL;
- PostgreSQL with `sslmode=require`, `verify-ca`, or `verify-full`;
- live Stripe secret-key format, webhook secret, and both package price identifiers; and
- AI analysis off until the legal-use review is resolved.

`GET /readyz` returns 503 when configuration is incomplete or any required evidence gate is still unverified. Case and document paths also return 503 before authentication/data access while readiness is unmet. The repository intentionally has unresolved, non-configurable blockers for deletion-aware backup restoration, payment-provider test evidence, and alert-delivery evidence. This prevents a settings-only change from being mistaken for operational verification. A successful readiness response in a future implementation will still not be production sign-off.

`GET /healthz` only indicates that the process answered. `/readyz` probes the configured database and object-store bucket after the production configuration gate. These probes do not verify TLS termination, private access policy, effective KMS permissions, backup scope, object-version purge, legal approval, provider payment behavior, or alert delivery.

## Backup, restore, and deletion procedure

**Current state: operationally blocked.** Application-level deletion reconciliation is implemented, but no production backup inventory, initialized production ledger, or restore evidence is recorded. Do not restore a production backup into an environment that can serve users until the ledger's production controls are verified and reconciliation succeeds. Do not claim provider-managed backup purge.

Before any future production restore:

1. Identify the exact database and object-storage backup/snapshot/replica inventory, backup timestamps, retention, encryption, access roles, and restore dependencies in an operator-controlled record.
2. Keep the restored database, workers, exports, and user traffic isolated. A snapshot can predate a deletion tombstone; the independently stored ledger must therefore be available and protected separately from that snapshot.
3. Before production case-data traffic is enabled, initialize the ledger from the authoritative database using the documented one-time command. During recovery, use the already initialized ledger; never initialize it from a stale restored snapshot. If there is no complete deletion record, stop and do not expose the restored data.
4. Run `python -m app.deletion_ledger reconcile` against the isolated restore. The command restores missing tombstones, removes restored database rows and derived records, and purges the associated S3 object versions. API and worker startup repeat reconciliation before serving or polling, but they do not replace the operator's isolated restore and verification steps.
5. Run a restore exercise with synthetic data and a synthetic deletion before launch and after material changes. Record the actual restore point, deletion case, reconciliation result, access-denial result, reviewer, timestamp, and follow-up. No such exercise has been performed or recorded by this repository task.

In-app Spec 44 deletion removes active application data and known S3 object versions for selected keys. It does not purge provider-managed database backups, snapshots, replicas, or disaster-recovery copies. A restore from a snapshot preceding deletion can restore deleted content; the external ledger reconciliation removes it before the application serves that restored database. This code path is implemented, but its production ledger controls and provider restore behavior remain an unresolved #134/#139 evidence gate.

## Security and operations checklist

Complete each item using deployment evidence; placeholders below are labels, not secrets:

- [ ] **Owner and scope:** `ENVIRONMENT=<operator value>`; `DEPLOYMENT_OWNER=<role/team>`; `REVIEWED_AT_UTC=<timestamp>`; `REVIEW_RECORD=<internal evidence reference>`.
- [ ] **Secrets:** `SECRET_MANAGER=<approved service>`; confirm production secrets are injected at runtime, scoped to the service, rotated under policy, and absent from source, images, logs, alerts, and support payloads. Do not record secret values.
- [ ] **Transport and access:** record HTTPS ingress/TLS policy and database TLS mode; verify bucket public access is blocked; review least-privilege app/worker identities for only required bucket, KMS, database, payment, and AI operations.
- [ ] **Authentication and authorization:** record exact tested build/environment and results for login/session revocation, secure cookies/CSRF, case membership, unauthorized/unauthenticated denial, delegate revocation, and case/document endpoints. Do not infer production behavior from unit tests alone.
- [ ] **Safe logging:** review proxy, API, worker, database, and provider logs for resource identifiers, filenames, case content, tokens, cookies, credentials, prompts, and provider output. Configure access-log redaction/disablement where paths may expose identifiers.
- [ ] **AI gate:** leave `AI_ANALYSIS_ENABLED=false` until issue #128 is resolved and counsel has reviewed exact data flows, providers, retention/training settings, subprocessors, and disclosures. Record legal approval in the appropriate protected business record, not in this checklist as a claim.
- [ ] **Payments:** complete the test-mode scenarios and evidence in Spec 49 / issue #138; confirm rollback/disable controls. Do not make a live customer charge as a test, and do not infer payment success from a browser redirect.
- [ ] **Backups and restore:** `BACKUP_INVENTORY=<internal record>`; `RETENTION_POLICY=<approved policy>`; `RESTORE_EXERCISE=<internal evidence reference>`. Verify that the initialized deletion ledger is in a separate versioned bucket with protected IAM/KMS and no expiration; demonstrate reconciliation after restoring a pre-deletion snapshot using [the restore runbook](deletion-ledger-restore.md). Repository code and procedures exist; production configuration and a successful exercise are not evidenced here.
- [ ] **Monitoring and incident response:** `MONITORING_PROVIDER=<operator value>`; `SEV1_ROUTE=<operator value>`; `SEV2_ROUTE=<operator value>`; `ON_CALL_OWNER=<role/team>`; `ALERT_DELIVERY_TEST=<internal result reference>`. Exercise delivery to actual recipients and record the time, synthetic alert identifier, receiver, and result. These routes and delivery are not configured here.
- [ ] **Sign-off:** `RESPONSIBLE_OPERATOR=<role/team>`; `SIGN_OFF_RECORD=<internal evidence reference>`. Leave issue #139 open until production security checklist review, restore/deletion verification, and alert-delivery evidence are actually recorded.

Never put credentials, real case details, customer data, payment details, or raw provider payloads in these fields. Use internal evidence references with access controls rather than attaching sensitive records to the repository or issue.
