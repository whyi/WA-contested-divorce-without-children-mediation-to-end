# Spec 59: Owner-Beta Deployment Readiness Gate

- **Status:** Implemented as an opt-in application configuration gate; cloud provisioning is not implemented
- **Related issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 57: Owner-Only Beta Environment Boundaries](../57-owner-beta-environment-boundaries/spec-57-owner-beta-environment-boundaries.md), [Spec 58: Owner-Only Authentication Gate](../58-owner-only-authentication/spec-58-owner-only-authentication.md)
- **Objective:** Keep owner-beta case workflows unavailable until the runtime is configured for a private, encrypted, non-demo UAT deployment without enabling live payments or AI.

## Requirements

1. `OWNER_BETA_READINESS_REQUIRED` defaults to false so local development and existing demos retain their current behavior.
2. When enabled, `/readyz`, case/document routes, the account dashboard, and billing routes fail closed unless owner-only authentication is enabled, demo mode is off, account-backed case and material access are enabled, authentication secrets are sufficiently strong, the public auth origins use HTTPS, PostgreSQL requires TLS, and object storage is remote and encrypted with the configured KMS key. Extraction and analysis workers refuse to start while the same readiness checks fail.
3. UAT readiness requires configured email delivery (`SMTP_HOST` and `AUTH_EMAIL_FROM`). An operator must separately verify that messages are captured by a test sink or restricted to an approved owner destination; the application cannot prove that provider-side policy.
4. When UAT readiness is required, application startup rejects AI analysis, live Stripe credentials, and static AWS credentials. Stripe test credentials may be used. UAT AI remains disabled pending its separate legal and provider gates.
5. Readiness reports stable check codes only and never include configured addresses, credentials, or resource connection strings.
6. This gate does not provision cloud resources, prove network/HTTPS termination, verify effective IAM/KMS policies, establish backups, test recovery, or certify UAT. Those controls require deployment-specific operator evidence.

## Deployment direction

The selected direction is AWS ECS/Fargate with an AWS-managed HTTPS endpoint because no custom domain is currently available. The ECS, networking, managed database, bucket, KMS, email-sink, secrets, and HTTPS endpoint resources are not provisioned or defined by this specification.

## Acceptance criteria

- Default configuration leaves the owner-beta readiness gate disabled.
- An incomplete, loadable hosted UAT configuration reports safe failure codes, makes `/readyz`, case/document, account-dashboard, and billing routes return 503 before data access, and prevents extraction/analysis workers from processing jobs. Invalid or unsafe configuration combinations fail during settings validation.
- A complete configuration using dedicated TLS PostgreSQL, remote HTTPS object storage, KMS, HTTPS auth origins, owner-only authentication, and configured email delivery reports no application readiness errors.
- Enabling AI, configuring live Stripe credentials, or supplying static AWS credentials while the UAT gate is enabled is rejected.
- Existing production readiness checks and local demo behavior remain unchanged.
- Documentation clearly distinguishes application configuration checks from actual cloud provisioning and operational verification.
