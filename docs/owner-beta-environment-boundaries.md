# Owner-Only Beta Environment Boundaries

This document records the intended separation for the owner-only beta and
repeatable UAT work in [Spec 57](../specs/57-owner-beta-environment-boundaries/spec-57-owner-beta-environment-boundaries.md)
and [issue #209](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209).
It is a boundary definition, not a deployment runbook or evidence that a
private environment exists.

## Current repository state

The repository contains a local Docker Compose stack using local Postgres and
Moto. It does not contain a hosted UAT deployment definition or a verified
production deployment. Do not treat the Compose stack, its development
credentials, or its demo account as a private-beta environment. See the
[production security, backup, and restore readiness runbook](production-security-backup-restore-readiness.md)
for existing production gates.

## Environment matrix

| Environment | Use | Data allowed | Hard boundary |
|---|---|---|---|
| Local development | Build and test locally | Synthetic fixtures and fictional preview data | Local Postgres and Moto only; no real case materials or live integrations |
| Public Demo 1/2 | Public fictional preview | Temporary browser-local fictional state | No account-backed case API, uploaded case documents, or AI analysis |
| Owner-only UAT (future) | Repeatable product-owner testing | Synthetic cases and synthetic test uploads only | HTTPS, server-side owner allowlist, and dedicated database, buckets, encryption keys, credentials, and deployment configuration |
| Production (future) | Approved real-user service | User data handled under approved policies | Separate host, database, buckets, KMS key, secrets, and provider configuration; governed by production readiness and release sign-off |

## UAT operating rules

- UAT must deny unauthenticated users and any account other than the
  specifically designated owner. Enforce this on registration and sign-in at
  the server, not just in page routing or deployment obscurity.
- The application has an opt-in server-side gate using
  `OWNER_BETA_ENABLED=true` and a deployment-injected `OWNER_BETA_EMAIL`. Keep
  the address in protected deployment configuration, never source control.
  The gate is not a substitute for isolated UAT infrastructure or HTTPS.
- Use synthetic case names, amounts, dates, documents, and responses. Do not
  upload actual client, opposing-party, or other sensitive case materials.
- Keep the UAT database, object storage, KMS key, signing/encryption secrets,
  email credentials, and external-provider credentials separate from local and
  production resources. Never restore a production backup into UAT.
- Keep payments disabled or on provider test credentials. Keep AI disabled
  until the separate legal and provider review gates are met. Capture test
  email or restrict delivery to an explicitly approved destination.
- Require fixture/reset, migration, backup, restore, and teardown tooling to
  positively verify a UAT target before making changes. Missing or ambiguous
  environment identity must fail closed; production must never be a reset
  target.
- Record test evidence with the environment and synthetic scenario identified.
  Do not put credentials, case contents, or unnecessary personal data in
  evidence.

## Promotion and readiness

Only reviewed code and explicit configuration move through release controls.
Do not copy UAT database state, uploaded objects, credentials, or provider
resources to production. UAT success is not production approval; evidence from
UAT does not satisfy production backup/restore, legal, payment, AI, alerting, or
release gates unless the responsible reviewer explicitly verifies the
production-specific control.

**Status:** Environment boundaries, an opt-in server-side owner email gate,
and an opt-in UAT deployment-readiness gate are implemented. The readiness
gate does not provision resources. No owner email is configured here, and no
hosted UAT, isolated resources, guarded reset, test-integration setup, or
successful UAT evidence is implemented or verified. AWS ECS/Fargate with an
AWS-managed HTTPS endpoint is the selected deployment direction; the cloud
resources and deployment definition remain outstanding. See
[Spec 58](../specs/58-owner-only-authentication/spec-58-owner-only-authentication.md)
and [Spec 59](../specs/59-owner-beta-deployment-readiness/spec-59-owner-beta-deployment-readiness.md)
for the current application gates.
