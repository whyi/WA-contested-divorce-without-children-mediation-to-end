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
  The sender may differ from the owner email; use a different address when the
  owner's mailbox provider drops messages that appear to come from itself. The
  SMTP IAM user must be allowed `ses:SendRawEmail` for the sender identity.
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

   Provide the owner email, the verified SES sender email (blank reuses the
   owner email), and the SES SMTP username/password when prompted. Do not enable
   tracing (`set -x`) or capture the prompt session.
5. On first deployment only, build/push the image, apply migrations, initialize
   the deletion ledger, and start the service:

   ```sh
   ./deploy.sh --initialize-ledger
   ```

   The deploy script requires a clean committed source tree and tags each
   image with its commit and build timestamp. ECR tags are immutable. Later
   code deployments use `./deploy.sh` without the initialization flag. Never
   initialize an already initialized ledger or use a production backup.
   Preserve the printed image tag with the deployment record. To roll back the
   application image, use `./rollback.sh <image-tag>` only after confirming
   that the older application is compatible with the current database schema
   and taking any required approved backup. Rollback never reverses migrations.
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

## One-click deployment from GitHub Actions

### Optional Google sign-in

Google sign-in requires a Web application OAuth client with the exact redirect
URI `<uat_url>/api/auth/oidc/google/callback`. Start the login on that same
HTTPS endpoint, not a local preview. The owner-email allowlist remains enforced.
Existing password accounts must explicitly link Google instead of automatically
merging identities with matching email addresses.

Store the Google client secret as a **plaintext string** in an existing
Secrets Manager secret in `us-west-2`, in the deployment account, using the
default Secrets Manager encryption key. Never put its value in GitHub variables,
Terraform variables/state, source control, or deployment logs.

Set these GitHub Environment variables in `owner-beta-uat`:

- `UAT_GOOGLE_CLIENT_ID`: the OAuth client ID.
- `UAT_GOOGLE_CLIENT_SECRET_ARN`: the existing secret ARN (not the secret value).

Configure both variables together. The image deployment injects the client ID
and secret reference into each task container without fetching the secret. It
preserves other runtime settings, including owner-only access. With neither
variable set, existing task configuration is preserved.

In the existing Terraform workspace, also set `google_client_id` and
`google_client_secret_arn` to the same values. Terraform wires the task settings
and grants the ECS **execution role** `secretsmanager:GetSecretValue` on only
that secret. This permission must exist before deployment; the Actions deploy
role does not need permission to read the secret or edit IAM. If the matching
inline policy was provisioned separately, import it before applying Terraform:
resource `aws_iam_role_policy.google_login_secret[0]`, import ID
`<project_name>-execution:<project_name>-read-google-login-secret`.

Run **Deploy UAT** to build latest `main`, run migrations and deploy the image
with these settings. Verify `/healthz`, `/readyz` and `/api/auth/providers`
(`google: true`). Then complete Google consent in a browser using an allowed
test account; provider availability alone does not prove a successful login.

After the initial local provisioning, **Actions > Deploy UAT > Run workflow**
deploys the latest `main` to the existing UAT service. It builds an immutable
image, runs forward migrations, updates ECS, and checks `/healthz` and `/readyz`.
Only after those checks succeed does the run summary show **Open UAT**.
It never applies Terraform, resets cases, or initializes the deletion ledger.
Runs are serialized and cannot be dispatched from another branch. Deployment
uses GitHub runner minutes and AWS resources; it is manual, not run on every PR.

### One-time connection setup

1. Create the GitHub Environment `owner-beta-uat` under repository Settings.
   Restrict deployment branches to `main`; add a required reviewer if your
   GitHub plan supports it. Do not allow untrusted PR code to use this environment.
2. In the AWS UAT account, configure the GitHub OIDC provider
   `https://token.actions.githubusercontent.com` with audience `sts.amazonaws.com`.
   Create a dedicated deployment role with this trust policy, replacing
   `<UAT_ACCOUNT_ID>`:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": {
         "Federated": "arn:aws:iam::<UAT_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
       },
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {
         "StringEquals": {
           "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
           "token.actions.githubusercontent.com:sub": "repo:whyi/WA-contested-divorce-without-children-mediation-to-end:environment:owner-beta-uat"
         }
       }
     }]
   }
   ```

   Scope its permissions to the existing UAT resources: ECR image upload/read
   (`GetAuthorizationToken` requires resource `*`; repository actions
   `BatchCheckLayerAvailability`, `InitiateLayerUpload`, `UploadLayerPart`,
   `CompleteLayerUpload`, `PutImage`, `DescribeImages` target only the UAT
   repository); ECS `DescribeTaskDefinition` and `RegisterTaskDefinition`,
   `RunTask` on UAT bootstrap task revisions with the UAT cluster condition,
   `DescribeTasks` for that cluster, and `UpdateService`/`DescribeServices` on
   the UAT service. Allow `iam:PassRole` only for the existing ECS application,
   bootstrap, and execution roles, with `iam:PassedToService` equal to
   `ecs-tasks.amazonaws.com`. Do not grant administrator access, secret-reading
   access, or access to production resources. Task containers use their existing
   roles to read runtime secrets. Review the exact resource ARNs in your account.
3. Store the role ARN as Environment **variable** `UAT_AWS_ROLE_ARN`.
   This uses short-lived credentials, not an AWS access key stored in GitHub.
4. On the computer that holds the existing Terraform state, export only the
   required resource identifiers to Environment variable
   `UAT_DEPLOYMENT_OUTPUTS_JSON`:

   ```sh
   cd deploy/aws/owner-beta
   terraform output -json |
     python3 deployment_config.py export |
     gh variable set UAT_DEPLOYMENT_OUTPUTS_JSON \
       --env owner-beta-uat \
       --repo whyi/WA-contested-divorce-without-children-mediation-to-end
   ```

   This does not upload Terraform state or runtime secret values. The variable
   contains account/resource identifiers and the endpoint; do not treat them as
   secrets or put private data in it. Repeat this export if infrastructure
   identifiers change. CLI authentication and environment-management permission
   are required for this setup.

The button is available once the workflow is on `main`, but it cannot deploy
until the AWS trust, IAM permissions, and both environment variables are configured.
Failures remain visible; a failed deployment does not publish a success URL.
Existing local `./deploy.sh` continues to use Terraform outputs when the
environment variable is not set.

## Operations and teardown

- Operational alarms and first-response guidance are documented in the
  [owner-beta operations runbook](operations-runbook.md). Confirm the SNS email
  subscription after the first apply; alarm configuration alone does not prove
  delivery. The same verified address receives budget notifications and
  threshold alarms.
- ECS desired count, RDS size, and monthly alert are Terraform variables; do
  not scale resources without reviewing the cost impact. The cost alert is
  informational and not a hard cap.
- ECR retains the ten most recent images. An older image may no longer be
  available for rollback after lifecycle cleanup; the rollback script fails
  closed if its exact immutable tag is missing.
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
SES SMTP user, backup/restore evidence, confirmed alert delivery, monitoring
owner/on-call integration, or a completed UAT record. CloudWatch alarms,
operator runbooks, immutable image deployments, and a guarded image rollback
command are defined, but neither a deployment nor an end-to-end UAT run is
claimed. Rollback does not restore the database schema. Remaining work is
tracked under #209.
