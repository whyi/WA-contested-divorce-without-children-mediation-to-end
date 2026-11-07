# AWS owner-beta UAT deployment

This Terraform stack is a deployable starting point for the private owner-only
UAT, not evidence that an AWS environment exists. It defaults to `us-west-2`
and a **$100 account-wide monthly cost alert**. It does not impose a hard spend
limit; AWS Budgets notifications can be delayed and do not stop resources.
Actual cost depends on region, traffic, data transfer, email, and account
pricing. Review the Terraform plan and current AWS prices before applying.

## Architecture

- AWS API Gateway HTTP API provides an internet-routable, AWS-managed HTTPS
  hostname; no custom domain is required. Owner-only access to account-backed
  workflows is enforced by server-side authentication and the owner allowlist;
  this is not a network-private or VPN-only endpoint.
- A private API Gateway VPC Link reaches an ECS service through Cloud Map.
- The public HTTPS endpoint applies a modest API Gateway request throttle;
  this is abuse mitigation, not an access-control boundary or cost cap.
- The single ECS/Fargate task contains the API plus extraction and analysis
  workers to reduce idle cost. It starts at desired count zero and has no
  public ingress rule; task security groups accept port 8000 only from the
  VPC Link. Fargate tasks receive public IPs for outbound AWS/SES access, so
  their subnets are public even though inbound access is restricted.
- A private, single-AZ PostgreSQL 16 instance has forced TLS, managed master
  credentials, encryption, and seven-day backups.
- Private versioned document and deletion-ledger buckets use a dedicated KMS
  key. The application role cannot delete ledger objects or versions.
- AWS Secrets Manager supplies database URL, owner identity, authentication
  keys, and SES SMTP credentials to ECS. Terraform never stores secret values.
- AI and live Stripe are not configured. SES must remain in sandbox and the
  owner sender/recipient identity must be verified.

The combined task and single-AZ database are deliberate UAT cost/availability
tradeoffs, not production architecture. Data must be synthetic only. The
deletion ledger is independent from RDS but shares the UAT KMS key; do not
describe this as production-grade disaster recovery.

## Prerequisites

- Terraform 1.6+, AWS CLI v2, Docker, Python 3, OpenSSL, and credentials for a
  dedicated AWS account or isolated deployment account.
- Permission to create VPC, ECS, API Gateway, Cloud Map, RDS, ECR, S3, KMS,
  Secrets Manager, IAM, CloudWatch, and AWS Budgets resources.
- SES sender identity verified in `us-west-2` and a dedicated SES SMTP
  credential. In SES sandbox, the recipient address must also be verified.
- A verified address for AWS Budget alerts. The alert covers the whole AWS
  account because cost-allocation tags are not assumed to be activated.

Do not use production account credentials, databases, buckets, KMS keys,
backups, or provider credentials for UAT.

## Provision and deploy

1. Review the architecture, regional pricing, and all Terraform changes.
   Export credentials for the dedicated AWS account and verify
   `aws sts get-caller-identity`.
2. Initialize and inspect the plan. Supply the alert recipient without
   committing a `.tfvars` file:

   ```sh
   cd deploy/aws/owner-beta
   terraform init
   terraform plan -var='budget_notification_email=<verified-operator-address>'
   ```

3. Only after approving ongoing costs, apply the reviewed plan:

   ```sh
   terraform apply -var='budget_notification_email=<verified-operator-address>'
   ```

   This creates billable AWS resources. The ECS service remains at zero tasks,
   but the VPC Link, database, KMS key, and other resources can incur charges.
4. Populate runtime secrets interactively. The script fills missing secrets
   only, so it can resume after a partial failure without rotating existing
   credentials. It reads the RDS-managed secret, constructs the TLS database
   URL in a private temporary directory, generates authentication secrets, and
   never prints values:

   ```sh
   ./bootstrap-secrets.sh
   ```

   Provide the owner email and verified SES SMTP username/password when
   prompted. Do not enable tracing (`set -x`) or capture the prompt session.
5. On first deployment only, build/push the image, apply migrations, initialize
   the deletion ledger, and start the service:

   ```sh
   ./deploy.sh --initialize-ledger
   ```

   Later code deployments use `./deploy.sh` without the initialization flag.
   Never initialize an already initialized ledger or use a production backup.
6. Confirm the returned URL uses HTTPS. Check `/readyz`, owner-only signup and
   sign-in, email verification, and account-backed workflows using synthetic
   data. A successful `/healthz` is liveness only; it is not UAT sign-off.
7. After signing in as the designated owner, use
   `./reset-synthetic-case.sh` to return the account to a clean, no-active-case
   baseline between UAT runs. The script requires typing an exact confirmation,
   verifies the AWS account, and runs an ECS task that independently checks the
   UAT database name/endpoint, storage bucket prefixes, readiness settings,
   owner identity, and fixture registry. A case is registered automatically
   when created through the account-backed case or first-upload flows. The reset
   permanently deletes that case and every stored object version through the
   deletion ledger; it preserves the owner login, credentials, and immutable
   ledger. It refuses to delete an existing case that was not registered by the
   UAT deployment. Use synthetic data only.
8. Execute and record the scenarios in the
   [owner-beta UAT runbook](uat-runbook.md). The runbook includes an explicit
   blocked state for backup restore until an isolated snapshot restore has
   been reconciled against the initialized deletion ledger.

## Operations and teardown

- ECS desired count, RDS size, and monthly alert are Terraform variables; do
  not scale resources without reviewing the cost impact. The cost alert is
  informational and not a hard cap.
- API Gateway access logs contain only request ID, route key, and status.
  Application logs are retained for 14 days. Do not add case bodies, tokens,
  or email addresses to logs.
- RDS backups retain seven days. The UAT deletion ledger has versioning and
  no lifecycle expiration. Record a synthetic restore exercise before using
  the environment for repeated UAT.
- The reset command restores an empty owner-case baseline, not a database
  snapshot. It does not erase the permanent-deletion ledger or reset account
  authentication settings.
- For teardown, first set the ECS service desired count to zero and wait for
  it to stop. RDS deletion skips a final snapshot; create a separately
  approved snapshot or export first if any synthetic evidence must be retained.
  Then run `terraform destroy`. S3 buckets are intentionally not
  force-destroyed; inspect and remove only the named UAT bucket contents under
  an approved teardown procedure. KMS key deletion is delayed by seven days.

This stack does not create a CI release pipeline, verified email identity,
SES SMTP user, backup/restore evidence, monitoring/on-call integration, or a
completed UAT record. A guarded case reset and repeatable UAT runbook are
provided, but neither a deployment nor an end-to-end UAT run is claimed.
Remaining work is tracked under #209.
