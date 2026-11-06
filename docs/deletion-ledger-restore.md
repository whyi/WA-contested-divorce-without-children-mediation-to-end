# Permanent-deletion ledger and database restore procedure

The database tombstone table is not an independent deletion record: an older database snapshot can omit later tombstones. Case-data deployments therefore require a separate, versioned S3 bucket configured as `DELETION_LEDGER_BUCKET`. Each confirmed deletion writes an opaque scope type and UUID plus the relevant opaque S3 object keys to that bucket before the database deletion barrier is committed. A failed ledger write fails the deletion request closed. The entries contain no names, email addresses, or document content.

## Ledger bucket controls

- Use a dedicated bucket, separate from both the application database and `S3_BUCKET`.
- Enable S3 versioning. The API checks that versioning is enabled and that the one-time initialization marker exists.
- Do not configure expiration or lifecycle cleanup for `casework-deletions/v1/`.
- The application role may list, read, and write ledger objects, but must not delete ledger objects or versions. Restrict bucket-policy, versioning, and IAM administration to a separate break-glass role. Do not grant the application role broad `s3:*` access to this bucket.
- Keep the ledger bucket available in the recovery region/account used for a database restore. Protect its credentials and KMS key independently from database backups.
- Ledger entries contain UUIDs, scope types, and the opaque source-object keys required for restore reconciliation; they do not contain names, email addresses, or document content.

## One-time initialization

Before enabling case-data traffic on an existing deployment:

1. Create and secure the dedicated ledger bucket, enable versioning, and configure its KMS/IAM policy.
2. With the authoritative production database and ledger bucket selected, run `python -m app.deletion_ledger initialize` once. The command copies every existing tombstone before writing the initialization marker; it refuses to overwrite an initialized ledger.
3. Back up the ledger bucket configuration and verify the marker and all copied entries are readable using the production application role.
4. Configure `DELETION_LEDGER_BUCKET` identically for the API, extraction worker, and analysis worker.
5. Enable case-data traffic only after the initialization evidence is recorded.

If a deployment has already lost the authoritative database and has no initialized external ledger, historical deletions cannot be inferred from a snapshot that predates those deletions. Do not initialize from that stale snapshot and claim restore protection.

## Database restore

1. Stop or isolate the API and all background workers. Do not route user traffic to the restored database.
2. Restore the database snapshot and point the recovery environment at the preserved deletion-ledger bucket and data bucket.
3. Run `python -m app.deletion_ledger reconcile`. The command restores missing tombstones, purges restored object versions for deleted scopes, removes restored database rows and derived records, and exits nonzero on any failure.
4. Verify the command completed successfully, then start the API. When case-data access is enabled, API startup replays the ledger again before accepting requests; readiness also checks ledger versioning and initialization.
5. Start workers only after reconciliation; each worker also reconciles before polling jobs. Restore traffic only after API startup and readiness succeed. Preserve command output, restored snapshot identifier, ledger bucket/versioning evidence, and operator/time in the recovery record.

Reconciliation is idempotent. Do not manually clear ledger entries or tombstones to make a failed restore pass.

## Evidence still required

Unit tests exercise restoring deleted scopes into a simulated pre-deletion database state. They do not prove provider backup inventories, replica behavior, IAM policy enforcement, KMS recovery, or a production point-in-time restore. Run and record a restore exercise against the deployment's actual backup and recovery environment before closing issue #134.
