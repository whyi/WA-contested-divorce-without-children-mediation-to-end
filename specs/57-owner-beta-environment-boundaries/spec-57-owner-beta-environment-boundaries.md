# Spec 57: Owner-Only Beta Environment Boundaries

- **Status:** Environment boundaries defined; no hosted UAT environment is implemented or approved
- **Related issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 44: Immediate Permanent Deletion](../44-immediate-permanent-deletion/spec-44-immediate-permanent-deletion.md), [Spec 50: Production Security, Backup, and Restore Readiness](../50-production-security-backup-and-restore-readiness/spec-50-production-security-backup-and-restore-readiness.md), [Spec 53: Release Acceptance Matrix](../53-release-acceptance-matrix/spec-53-release-acceptance-matrix.md)
- **Objective:** Define the non-overlapping data, access, infrastructure, and integration boundaries for local development, public demos, owner-only UAT, and any future production deployment.

## Scope and status

This is the first, documentation-only slice of #209. It defines requirements for later access-control, deployment, reset, and UAT work. It does not create an environment, approve a provider, configure secrets, or prove that any hosted system is private or operational.

The repository currently defines a local Docker Compose stack with Postgres and Moto. It does not define or verify a hosted UAT or production deployment. Existing production readiness requirements in Spec 50 remain authoritative; this spec does not weaken, replace, or satisfy them.

## Environment boundaries

| Environment | Purpose and access | Allowed data | Infrastructure and integrations |
|---|---|---|---|
| Local development | Developer-operated Compose or local process. Never a shared or public service. | Synthetic fixtures and fictional demo content only. No real party or client case materials. | Local Postgres and Moto; development credentials only. No live payments, real case email, or AI processing. |
| Public Demo 1/2 | Public product preview. No account-backed case access. | Fictional, temporary preview state held in the browser as defined by Spec 44 and related demo specifications. No user-uploaded case material. | Public web delivery may serve the preview, but demo actions must not create or access account cases, upload documents, or invoke analysis. |
| Owner-only UAT | A future private, production-like test deployment for the designated product owner. Authentication and server-side owner restriction are required; obscurity or frontend hiding is insufficient. | Synthetic UAT fixtures only, including uploaded test documents. Never real client, opposing-party, or other sensitive case materials. | Dedicated UAT database, object-storage buckets, encryption keys, credentials, and deployment configuration, separate from local and production resources. HTTPS is required. Payments stay disabled or in provider test mode; AI stays disabled until its legal/provider gates are independently approved. Email must be captured by a test sink or otherwise restricted to explicitly approved test destinations. |
| Production | Future service for authorized real users only after independent product, legal, security, provider, and operational approvals. | Real user data only under approved disclosures, retention, access, deletion, and recovery controls. | Separate production host, database, buckets, KMS key, credentials, and provider accounts/configuration from UAT. Production readiness and release sign-off remain governed by Specs 50 and 53. |

## Requirements

1. **Explicit environment identity:** Any future hosted case-data deployment must have an operator-controlled environment identity that the server and operational tooling can verify. Client input, URL paths, and editable request fields are not evidence of environment identity.
2. **No resource sharing:** UAT and production must not share databases, object-storage buckets, encryption keys, application credentials, signing secrets, or provider credentials. Local development resources and credentials must not be reused by either hosted environment.
3. **Owner-only enforcement:** UAT access must be restricted server-side to the designated owner at registration and authentication, in addition to normal case authorization. Public routes and static UI controls do not establish this restriction.
4. **Synthetic-data rule:** UAT fixtures and test uploads must be synthetic. Production data, backups, exports, credentials, or copied case records must not be used to seed or restore UAT.
5. **Preview isolation:** Public Demo 1/2 remain fictional browser previews. They must not be routed to UAT or production case APIs and must not create or mutate account-backed cases.
6. **Safe external services:** UAT payments use no live charge credentials. Payment test mode remains subject to Spec 49 and issue #138. AI remains disabled until the separate legal/provider gates in Spec 52 and issue #128 are completed. Email delivery is restricted to a verified test sink or explicitly approved owner destinations.
7. **Fail-closed operations:** Deployment, migration, fixture creation/reset, backup, restore, and teardown tools must verify the target environment before changing data. A missing, ambiguous, or production target must not be treated as UAT.
8. **No promotion by copying state:** Promote reviewed code and explicit configuration through controlled release steps; do not promote UAT database state, objects, secrets, or provider resources to production.
9. **Evidence is environment-specific:** An access, backup/restore, deletion, payment, AI, or alert check performed in one environment does not count as evidence for another. Record the environment identifier and synthetic test scope without secrets or case contents.
10. **No implied readiness:** A private URL, successful login, passing repository tests, or configured environment variables alone do not prove that UAT is isolated, owner-only, recoverable, or ready for use.

## Acceptance criteria for this boundary-definition slice

- Local development, public demos, owner-only UAT, and future production have distinct purposes, data rules, access rules, and resource boundaries.
- The public demo's fictional/browser-local behavior is explicitly kept separate from account-backed UAT.
- UAT is explicitly described as future/unimplemented, and no document claims a hosted UAT deployment or operational evidence exists.
- Follow-on issue #209 work can implement owner restriction, deployment isolation, guarded fixtures/reset, integration controls, and UAT evidence without changing these boundaries.

## Follow-on work

This definition does not complete #209. The remaining work is to implement owner-only access, provision and verify isolated hosted UAT resources, add environment-guarded synthetic fixtures/reset, configure safe test integrations, record operational controls, and execute the repeatable UAT suite. Production and public-beta gates remain separate.
