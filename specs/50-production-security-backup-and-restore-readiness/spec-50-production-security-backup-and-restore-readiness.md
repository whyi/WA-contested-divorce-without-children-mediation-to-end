# Spec 50: Production Security, Backup, and Restore Readiness

- **Status:** Repository readiness guard and operator runbook added; production evidence outstanding
- **Related issue:** [#139 — Verify production security, backups, monitoring, and recovery](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/139)
- **Related specifications:** [Spec 44: Immediate Permanent Deletion](../44-immediate-permanent-deletion/spec-44-immediate-permanent-deletion.md), [Spec 49: One-Time Payment Provider Readiness](../49-payment-provider-readiness/spec-49-payment-provider-readiness.md)
- **Related issues:** [#128 — Legal review of AI processing](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/128), [#134 — Immediate permanent deletion](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/134), [#138 — Payment provider readiness](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/138), [#141 — Failure and support runbook](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/141)

## Objective and boundary

Define repository-verifiable configuration gates and an evidence-based operator checklist for launch review. This specification does not certify a deployment, complete a legal review, configure a cloud provider, or claim a backup restore, backup purge, or alert-delivery test.

The existing Compose file is a local-development stack using local Postgres and Moto. It is not a production deployment definition. PR #167 adds an independent deletion ledger and application restore-reconciliation path, but the repository still has no production backup inventory, monitoring provider, alert route, or provider restore evidence.

## Requirements

- **FR-50-01 — Explicit production profile:** `PRODUCTION_READINESS_REQUIRED` defaults to false for local development. When true, `/readyz` checks the required production settings before runtime probes. Missing settings return HTTP 503 with a generic response and safe check codes in server logs; secret values are never returned.
- **FR-50-02 — Required configuration:** Production readiness requires non-demo operation, authentication with strong signing and encryption secrets, secure cookies, case and case-material access enabled, an AWS KMS key, a non-local object-storage endpoint, a support destination, PostgreSQL with TLS required, and configured live Stripe package credentials and price identifiers. Values that contain secrets must be injected by the deployment's approved secret manager, not committed to source or copied into evidence.
- **FR-50-03 — Fail-closed data access:** While production-readiness checks fail, case and document routes return HTTP 503 before authentication or data access. The readiness check does not replace authorization or membership checks.
- **FR-50-04 — Unverified gates remain blocking:** With production readiness required, the application reports the backup/deletion-reconciliation, payment-provider test-evidence, and alert-delivery gates as unmet. These gates cannot be cleared by adding a configuration value. They require implemented controls and recorded, independently verifiable operational evidence. Enabling AI analysis also blocks readiness while its legal-use review is unverified.
- **FR-50-05 — Runtime probe scope:** `/healthz` is a liveness response. `/readyz` additionally probes the configured database and object-store bucket. Neither endpoint proves TLS termination, private-bucket policy, KMS authorization, backup retention, deletion purge, payment behavior, alert delivery, or launch approval.
- **FR-50-06 — Backup restore and tombstones:** Spec 44's active-database tombstones prevent stale application work against the database state in which those tombstones exist. PR #167 adds a separate, versioned S3 deletion ledger, an explicit one-time initialization command, a reconciliation command, and API/worker startup reconciliation. A restore from a snapshot preceding a deletion must be reconciled against the previously initialized ledger before traffic resumes. The code path does not prove that a production ledger is initialized, separately protected, or available during recovery; do not expose restored data until those controls and a real restore exercise are verified. The implementation purges affected application database rows and configured S3 object versions; it does not purge provider-managed snapshots or replicas.
- **FR-50-07 — Evidence-based operations:** The deployment owner records actual environment, reviewer, timestamp, test identifiers, outcome, and follow-up for each operational gate without recording secrets, case contents, personal data, or payment-method details. A missing record is an unmet gate, not a pass.
- **FR-50-08 — Scope separation:** Reversible case closure remains governed by Spec 32 and is not permanent deletion. A successful in-app deletion is not evidence that provider-managed database backups, snapshots, replicas, or disaster-recovery copies were purged.

## Repository implementation

`Settings.production_readiness_errors()` returns only non-sensitive check identifiers. `PRODUCTION_READINESS_REQUIRED=true` causes `/readyz` to fail closed and causes `/cases` and `/documents` paths to return 503 when any check is unmet. Production mode intentionally cannot report ready until deletion-aware restore reconciliation has been exercised in the deployment and payment-provider test and alert-delivery evidence have been recorded.

Configuration tests verify missing-security/provider settings and the permanent evidence blockers. Route tests verify that incomplete readiness prevents database/object-store probes and case-data access. Those tests are mocked repository checks, not production operational evidence.

## Current status

No production deployment definition or production configuration is present in the repository. The application reconciliation implementation and operator procedure are present, but no production ledger initialization, backup inventory, restore exercise, provider backup purge, Stripe test-mode transaction, or alert-delivery result is recorded. Issue #139 remains open until the responsible operator verifies these controls, records the required evidence, and signs off.
