# Owner-Beta Operations Runbook

This runbook covers routine UAT operations and the CloudWatch alerts provisioned
by Terraform. It is not a production incident-response commitment. The
owner-beta environment is a single-operator UAT service; no 24/7 on-call
coverage is configured. Use synthetic data only.

## Alert setup and scope

Terraform sends operational alarms and the existing AWS Budget notifications
to `budget_notification_email`. After the first approved apply, the recipient
must confirm the Amazon SNS email subscription before alarm delivery works.
Record a redacted confirmation reference; never put the address in this
runbook.

| Alarm | Trigger | First response |
|---|---|---|
| API 5xx | At least 5 HTTP API server errors in 5 minutes | Check API Gateway metrics and redacted API/ECS logs; compare with the current deployment. |
| ECS task shortfall | Desired tasks exceed running tasks for 2 of 3 one-minute periods | Check ECS service events, task stop reasons, image pull, secrets access, and `/readyz`. |
| RDS high CPU | Average CPU exceeds 80% for 3 consecutive 5-minute periods | Check database connections, workload, and recent UAT activity; do not scale without reviewing cost. |
| RDS low storage | Free storage falls below 5 GiB | Stop uploads and growth-producing work; review retained synthetic data and instance/storage changes before cleanup or scaling. |
| Monthly cost | Actual AWS spend exceeds the configured 80% or 100% threshold | Review the account bill and active resources. The budget is an alert, not a cap or automatic stop. |

CloudWatch alarms are threshold signals, not availability guarantees. Missing
metrics are treated as non-breaching; an alarm that is quiet is not proof that
the application is healthy. Check `/readyz` and perform the relevant smoke
checks after deployments. Do not copy case details, credentials, tokens,
request bodies, email addresses, or payment data into incident notes.

## UAT incident handling

1. Record the UTC time, environment identifier, alert name, deployed commit, and
   redacted evidence reference in the approved private record.
2. Check `/healthz` for process liveness and `/readyz` for configured readiness.
   If readiness fails, stop UAT writes and inspect the safe readiness check
   codes and recent redacted logs.
3. For an ECS task failure, inspect service events and the stopped task's
   container exit status. Never print task environment values or Secrets
   Manager contents.
4. If there is a suspected unauthorized access, data exposure, or wrong AWS
   resource target, stop the ECS service by setting desired count to zero,
   preserve relevant access/audit records, and investigate before restarting.
   This interrupts UAT; it does not delete the case or ledger.
5. For a database or storage failure, do not retry destructive operations
   blindly. Preserve the deletion ledger and follow
   [the restore procedure](../../../docs/deletion-ledger-restore.md) if a
   snapshot restore is approved.
6. Record the cause, corrective action, reviewer, and whether owner-only
   smoke tests passed before resuming UAT. Escalate AWS account, billing, or
   identity-provider concerns to the account owner.

## Deployments and rollback limits

- The ECS deployment circuit breaker is enabled and can roll back a failed ECS
  deployment. This does not undo a database migration, restore deleted data,
  or prove that the prior application version is compatible with the current
  schema.
- The deploy script requires a clean committed source tree, pushes an
  immutable commit/timestamp image tag, runs forward migrations, and registers
  new application and bootstrap task-definition revisions before updating the
  ECS service. Preserve the printed tag and task-definition ARN in the
  deployment record. Terraform ignores the service's externally selected task
  definition so a routine infrastructure apply does not silently revert the
  running application image.
- `rollback.sh <image-tag>` requires an exact interactive confirmation and an
  existing immutable ECR tag. It deploys the selected app image without
  running a migration or changing the database schema. Use it only when the
  previous app version is known to be schema-compatible; this command is not
  proof of a tested rollback or database recovery.
- ECR lifecycle cleanup retains only the ten most recent images. A prior image
  may therefore be unavailable, in which case rollback refuses to proceed.
- Do not run Alembic downgrade as an incident shortcut. If a release is
  unhealthy, stop further deployments and writes as appropriate, record the
  current task definition and schema revision, and obtain an operator-reviewed
  recovery plan.
- The one-time `--initialize-ledger` flag is for the initial deployment only.
  Never use it to repair or overwrite an initialized deletion ledger.

## Secret handling and rotation

- `bootstrap-secrets.sh` generates and fills missing values but intentionally
  leaves populated Secrets Manager values unchanged. It is not a rotation
  command.
- Rotate SES SMTP credentials through the SES/IAM operator workflow, update the
  corresponding Secrets Manager versions using an approved protected channel,
  and start a fresh ECS deployment so containers load the new values. Verify
  delivery only to the verified SES sandbox recipient.
- Rotating `AUTH_JWT_SECRET` invalidates existing sessions; plan an owner
  sign-in/recovery window and deploy new tasks after updating the value.
- Do not rotate `AUTH_ENCRYPTION_KEY` in place. The application uses it to
  decrypt persisted TOTP secrets and external-provider tokens. A safe rotation
  requires a separately implemented and tested re-encryption migration.
- Changing the owner email requires coordinating the account allowlist, sender
  verification, and recovery path. Do not update only one of those values.
- Never pass secret values as command-line literals, commit them, or paste them
  into a ticket or run record.

## Operational evidence

For each reviewed deployment or incident, record only:

```text
Environment identifier:
UTC timestamp:
Deployed commit/image reference:
Alarm or change reference:
Action and outcome:
Readiness/smoke-check result:
Reviewer role:
Redacted evidence reference:
Follow-up:
```

No AWS deployment, alert-delivery test, secret rotation, rollback rehearsal,
backup restore, monitoring owner, or on-call response has been performed by
adding this runbook or its Terraform alarms and deployment commands.
