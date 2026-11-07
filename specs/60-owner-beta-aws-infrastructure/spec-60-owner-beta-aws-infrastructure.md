# Spec 60: Owner-Beta AWS Infrastructure

- **Status:** Infrastructure as code and immutable image deployment tooling prepared; AWS resources and end-to-end UAT are not provisioned or verified
- **Related issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 57: Owner-Beta Environment Boundaries](../57-owner-beta-environment-boundaries/spec-57-owner-beta-environment-boundaries.md), [Spec 58: Owner-Only Authentication](../58-owner-only-authentication/spec-58-owner-only-authentication.md), [Spec 59: Owner-Beta Deployment Readiness Gate](../59-owner-beta-deployment-readiness/spec-59-owner-beta-deployment-readiness.md)
- **Objective:** Define a repeatable, isolated AWS deployment for synthetic-data owner UAT without treating application readiness as evidence that cloud resources or operations have been verified.

## Deployment decisions

1. Use AWS ECS/Fargate in `us-west-2` by default, with an AWS-managed HTTPS hostname and no custom domain.
2. Set an account-wide monthly AWS Budgets notification threshold of $100 by default. This is an alert only: it is not a spending cap, automatic shutdown, or cost guarantee. Review current regional prices and the Terraform plan before provisioning.
3. Use a public API Gateway HTTPS endpoint with server-side owner authentication and allowlisting. “Owner-only” describes access to account-backed product workflows; it does not mean the endpoint is private-network/VPN-only. API throttling is abuse mitigation, not access control.
4. Keep UAT resources and credentials separate from production. Use synthetic data only. Do not enable AI analysis or live Stripe payments.
5. The Terraform stack prepares resources but does not create AWS resources until an operator reviews and applies it with an explicitly configured AWS account.

## Infrastructure requirements

- **INF-60-01 — HTTPS ingress:** API Gateway HTTP API supplies the HTTPS URL and connects to the ECS API through a VPC Link and Cloud Map. The stage applies a modest default request throttle.
- **INF-60-02 — Network isolation:** PostgreSQL is private and accepts connections only from the application security group. ECS ingress accepts the API port only from the VPC Link. Fargate tasks use public IPs for outbound AWS and SES access; security-group ingress does not permit direct public connections to the task.
- **INF-60-03 — Application runtime:** A Fargate task hosts the API and extraction/analysis workers. The service starts at desired count zero. The deployment script requires a clean committed source tree, pushes a unique immutable image tag, registers task-definition revisions for that image, runs migrations, initializes the deletion ledger only when explicitly requested, then starts the service. A confirmed rollback command can deploy a retained image but never reverses database migrations.
- **INF-60-04 — Persistence and encryption:** PostgreSQL uses managed master credentials, TLS, encryption, and seven-day backups. Document and deletion-ledger S3 buckets are private, versioned, and KMS-encrypted. The application role cannot delete ledger objects or versions.
- **INF-60-05 — Secrets:** Application runtime values are stored in Secrets Manager and injected into ECS. Bootstrap must avoid printing secret values, must use a private temporary directory, and must preserve already-populated authentication keys when resuming after partial failure. Terraform state and local secret inputs must be excluded from version control.
- **INF-60-06 — External services:** SES SMTP is configured manually with a verified sender and sandbox recipient. AI and live payment credentials are not provisioned. Do not send real case material to UAT.
- **INF-60-07 — Cost notification:** AWS Budgets sends account-wide actual-cost alerts at the configured thresholds. Notifications may be delayed and cannot prevent charges.
- **INF-60-08 — Teardown safety:** S3 buckets must not be force-destroyed by Terraform. Operators review and remove only the named UAT bucket contents under an approved teardown procedure. RDS deletion does not create a final snapshot; operators create an approved snapshot/export before teardown if evidence must be retained. KMS key deletion uses the configured waiting period.

## Acceptance criteria

- Terraform formats and validates locally, and deployment scripts pass shell syntax checks without requiring AWS credentials.
- Runtime environment and ECS secret names do not overlap; no plaintext secret values or `.tfstate`/`.tfvars` files are committed.
- The database URL bootstrap uses the configured database name and percent-encodes credentials; partial secret bootstrap can resume without changing existing key values.
- ECR release images use immutable tags; ECS deployment revisions record the selected image, and the guarded rollback command requires an existing image tag.
- The API endpoint and VPC Link wiring use HTTPS at the public edge; application authentication remains the server-side owner boundary.
- The deployment documentation distinguishes the informational $100 monthly alert from a hard cap and states that provisioning can incur charges even while ECS desired count is zero.
- No AWS resource is applied and no UAT readiness, email delivery, restore exercise, or end-to-end user workflow is claimed as verified by the IaC change alone.
- Before issue #209 can be closed, an operator must approve the actual AWS account and cost exposure, configure the budget recipient and SES credentials, apply the reviewed plan, deploy the application, and record owner-only end-to-end UAT and recovery evidence.

## Out of scope

Creating AWS resources, spending approval, a hard cost ceiling, a network-private/VPN-only endpoint, custom DNS, CI/CD, synthetic fixture/reset tooling, production availability, production disaster recovery, AI enablement, live payment enablement, or completion of issue #209.
