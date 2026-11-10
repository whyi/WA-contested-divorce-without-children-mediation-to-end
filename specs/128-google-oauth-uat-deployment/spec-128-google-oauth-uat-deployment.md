# Spec 128: Google OAuth UAT Deployment Configuration

- **Issue:** [#394](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/394)
- **Amends:** Spec 60's owner-beta runtime configuration with optional Google
  login configuration. Authentication, consent and owner-only restrictions
  remain unchanged. Historical specifications are not edited.

## Requirements

1. The existing latest-main deployment accepts a paired Google client ID and
   existing Secrets Manager secret ARN from GitHub Environment variables.
2. Deploy the new immutable application image and forward migrations together
   with those settings. Preserve unrelated environment variables and secrets.
3. Keep the secret value out of the runner, repository and Terraform state.
   Inject it through ECS secret references only. Validate paired configuration
   and restrict the reference to the task's AWS account and UAT region.
4. Terraform supports the same optional settings and grants the execution role
   read access only to the selected secret. The deployment role requires no
   additional secret-reading or IAM-management permissions.
5. Keep existing task configuration unchanged when both optional inputs are
   absent. Retain owner-only access and require the exact AWS HTTPS callback.

## Verification

- Unit tests cover optional settings, malformed and partial inputs, cross-account
  rejection, unchanged source definitions and preservation of runtime settings.
- Validate Terraform and deployment configuration.
- After deployment check health, readiness, provider availability and the
  generated Google authorization URL's client ID and callback.
- A real Google login still requires the user to select their own account and
  approve consent; do not claim login success from configuration checks alone.
