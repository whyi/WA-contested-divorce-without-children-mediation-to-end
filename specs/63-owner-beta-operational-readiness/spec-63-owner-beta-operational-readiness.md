# Spec 63: Owner-Beta Operational Readiness

- **Status:** CloudWatch alarms and operator runbook implemented; AWS apply and alert delivery are pending
- **Related issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related pull requests:** [#216 — Add AWS infrastructure for owner-only UAT](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/216), [#221 — Add repeatable owner-beta UAT suite](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/221)
- **Related specifications:** [Spec 50: Production Security, Backup, and Restore Readiness](../50-production-security-backup-and-restore-readiness/spec-50-production-security-backup-and-restore-readiness.md), [Spec 60: Owner-Beta AWS Infrastructure](../60-owner-beta-aws-infrastructure/spec-60-owner-beta-aws-infrastructure.md), [Spec 62: Owner-Beta Repeatable UAT Suite](../62-owner-beta-uat-suite/spec-62-owner-beta-uat-suite.md)
- **Objective:** Add actionable infrastructure alarms and document safe owner-beta deployment, incident, secret-handling, and recovery boundaries without claiming operational evidence that has not been produced.

## Requirements

1. Operational notifications use the existing protected `budget_notification_email` input and require explicit SNS subscription confirmation.
2. Terraform alerts on API Gateway HTTP API 5xx volume, ECS desired-versus-running task shortfall, sustained RDS CPU, and low RDS free storage. Existing AWS Budget notifications remain informational and do not stop resources.
3. Alarm descriptions and runbooks contain no secrets or case contents. Missing metrics must not be presented as proof of health.
4. The operator runbook documents first response, deployment circuit-breaker scope, destructive recovery boundaries, and minimal redacted evidence.
5. The operator runbook explicitly records that the mutable `latest` image workflow has no tested application rollback and that Alembic downgrade is not an incident shortcut.
6. Secret rotation guidance distinguishes session-key rotation from encryption-key rotation. `AUTH_ENCRYPTION_KEY` must not be rotated in place until persisted ciphertext has a tested re-encryption migration.
7. Documentation and Terraform configuration must state that AWS resources, SNS delivery, rollback, restore, monitoring ownership, and on-call response have not been verified by this change.

## Acceptance criteria

- Terraform validates the SNS topic/subscription and alarm resources without AWS credentials.
- API 5xx, ECS task shortfall, RDS CPU, RDS storage, and cost alarms route to the configured alert recipient.
- Deployment documentation links to the response runbook and identifies subscription confirmation and known rollback limitations.
- Local documentation links resolve and `git diff --check` passes.
- No AWS resources are applied and no live alert delivery, rollback, restore, or UAT operation is claimed as complete.

## Out of scope

Applying Terraform, confirming the SNS subscription, choosing an on-call rotation, performing a secret rotation, adding immutable image promotion, changing database migration strategy, or performing a backup/restore exercise.
