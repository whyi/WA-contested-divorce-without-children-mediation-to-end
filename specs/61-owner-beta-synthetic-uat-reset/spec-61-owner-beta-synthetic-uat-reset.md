# Spec 61: Owner-Beta Synthetic UAT Case Reset

- **Status:** Implemented; deployment and an actual UAT reset have not been run
- **Related issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related pull request:** [#216 — Add AWS infrastructure for owner-only UAT](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/216)
- **Related specifications:** [Spec 58: Owner-Only Authentication](../58-owner-only-authentication/spec-58-owner-only-authentication.md), [Spec 59: Owner-Beta Deployment Readiness Gate](../59-owner-beta-deployment-readiness/spec-59-owner-beta-deployment-readiness.md), [Spec 60: Owner-Beta AWS Infrastructure](../60-owner-beta-aws-infrastructure/spec-60-owner-beta-aws-infrastructure.md)
- **Objective:** Let the owner repeat UAT from an empty case baseline while preserving the owner account and permanent-deletion protections.

## Requirements

1. The reset retains the owner login, password/MFA configuration, and account. It permanently deletes only the one registered owner case and all case-linked database data and stored object versions.
2. Case deletion must use the existing permanent-deletion barrier, external deletion ledger, and object-version purge. The reset never removes or rewrites tombstones and never reuses a deleted case UUID.
3. Every new case created by the owner through the account-backed case-creation or first-upload paths is recorded in a dedicated registry only when the UAT reset feature is explicitly enabled.
4. The reset refuses to delete an existing owner case unless it matches the registry. It refuses inconsistent memberships, suspended ownership, multiple cases, unsupported registry versions, and missing/incomplete account state. An already-empty baseline is an idempotent no-op.
5. Reset is disabled by default. When enabled, the application configuration requires the owner-beta readiness gate, owner-beta mode, non-demo mode, no production-readiness mode, no AI/live Stripe, the dedicated `owner_beta_uat` database name, a matching owner-beta RDS endpoint prefix, and owner-beta document/ledger bucket prefixes.
6. Before mutation, the command verifies full owner-beta readiness and S3/initialized-ledger readiness. The operator wrapper requires the exact phrase `RESET OWNER-BETA UAT CASE`, confirms the AWS caller account matches Terraform state, and runs the command in the dedicated ECS bootstrap task.
7. The baseline is the owner's active account with no case. The owner starts a new synthetic case through either supported preparation path. No real client material may be used in UAT.
8. The reset is destructive and must not run automatically during application startup, deployment, CI, or ordinary UAT tests.

## Acceptance criteria

- Reset is off by default, and unsafe/non-UAT database or bucket settings are rejected before the app starts or any reset work begins.
- First account-backed case creation and the document-first case-creation path both register the current owner case in the UAT registry.
- Reset with a wrong confirmation, unsafe resource identity, unready deletion ledger, unregistered case, or inconsistent account state performs no case deletion.
- A successful reset preserves the owner, writes the permanent case tombstone to the external ledger, purges all stored object versions, removes case-linked records, clears the registry pointer, and exits nonzero if any deletion step fails.
- Repeating reset with no active case is a no-op; the next owner-created case is registered and can be reset independently with a new UUID.
- Documentation clearly distinguishes the empty case baseline from database snapshot restore and states the account/ledger preservation behavior.
- Unit tests cover safety refusals, registration, deletion, storage purge, ledger persistence, owner preservation, and idempotence.

## Out of scope

Recreating the owner account, resetting authentication, deleting ledger records, restoring a database snapshot, populating legal/case sample facts, deleting an unregistered existing case, or claiming that a deployed UAT reset or backup-restore exercise has been completed.
