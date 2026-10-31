# WA-contested-divorce-without-children-mediation-to-end
AI-driven SDD wizard guiding Washington State contested no-children divorce cases from mandatory settlement conference to final decree.

## Repository workflow

Read the applicable specification in `specs/` before making changes. Use the
audit harness normally for validation:

```sh
bash harness/validate.sh
```

Only when the user's prompt explicitly asks to implement a specification
(for example, “read the latest spec and implement it” or “implement the spec”),
opt in to capturing that implementation request and its results:

```sh
INTERACTION_CAPTURE=1 \
INTERACTION_PROMPT='Implement the latest specification' \
INTERACTION_LOG=interactions/<spec-number>-<name>/response-<spec-number>-<name>.md \
bash harness/validate.sh -- <command> [arguments...]
```

In capture mode, the harness records the exact prompt, invocation timestamp,
combined command output, and exit status. Add relevant non-shell tool outputs
and the assistant's final response to that same entry. Ordinary questions,
planning, clarifications, and unrelated work should not be logged. Without
`INTERACTION_CAPTURE=1`, the harness validates normally and writes no
interaction log.

## Application foundation

The initial application foundation follows
[Spec 01](specs/01-tech-stack-override/01-tech-stack-override.md): Python 3.11+,
FastAPI, PostgreSQL, S3-compatible object storage, and a Docker image with
LibreOffice for DOCX-to-PDF rendering. AWS S3 is the selected object-storage
provider; local development uses Moto through the S3 API. Azure Blob Storage is
not implemented in this first iteration.

The app serves an English landing page at `http://localhost:8000/`. It presents
the two planned preparation modes and social sign-in choices. After sign-in,
the account dashboard shows the authenticated user's authorized case
memberships. An account with no authorized cases sees two starting actions:
upload existing case materials or use the step-by-step wizard. The materials
page supports local multi-file selection, drag-and-drop, file review/removal,
and explicit import confirmation. Device uploads and their idempotent import
API remain disabled in the local preview because `CASE_DATA_ENABLED` is false.
Google Drive and Dropbox pickers are not configured and remain unavailable;
provider registration, minimum scopes, token lifecycle, and deployment settings
must be established before enabling them. The wizard remains a preview-only
screen. The local Docker Compose preview enables a demo-only account (`demo` /
`demo`) to exercise sign-in and the empty dashboard. Demo mode is restricted to
localhost and never enables case-data APIs. Outside that local preview,
authentication and case-data APIs remain disabled by default; case/document
APIs require explicit authentication and case-membership configuration. Every
case is protected by an explicit case-membership grant, and signup or social
login never grants case access. Do not submit real case information.

Run locally with Docker Compose:

```sh
docker compose up --build
```

The API documentation is at `/docs`. PostgreSQL migrations run as the API
container starts. The Compose demo signing key and `demo` / `demo` account are
public development credentials, not secrets; never copy them to any shared or
public deployment. `DEMO_MODE_ENABLED` is localhost-only and incompatible with
case-data access. Enable `CASE_DATA_ENABLED` only after deciding how to handle
existing records; unassigned existing cases remain inaccessible. The compose
configuration binds the API and local S3 endpoint to localhost and uses
development-only S3 mock credentials.

Authentication requires deployment-managed values for `AUTH_ENABLED`,
`AUTH_JWT_SECRET` (at least 32 bytes), and email delivery
(`SMTP_HOST`, `AUTH_EMAIL_FROM`; SMTP credentials when required). Google
sign-in requires `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. TOTP enrollment
requires `AUTH_ENCRYPTION_KEY` (at least 32 bytes). Configure the public URL,
issuer, audience, secure-cookie policy, and WebAuthn RP ID/origin for the
deployment. Keep `AUTH_ENABLED=false` until the decisions in
[Spec 03](specs/03-authentication/spec-03-authentication.md) are approved and
the deployment has been reviewed. Do not use the development defaults or
handle real case information before production secret management, operational
email delivery, retention, and account-recovery policies are established.

Case-material storage is separately gated by `CASE_MATERIALS_ENABLED` and
requires authenticated case-data access. Production case-data access requires
`S3_KMS_KEY_ID` for a customer-managed AWS KMS key; uploads explicitly request
SSE-KMS, and there is no unencrypted production fallback. Loopback-only local
S3 development does not use KMS. Production buckets must block public access,
and the application role must be limited to the configured bucket and KMS key.
Before enabling real uploads, document the
retention period, backup/versioning behavior, legal-hold process, and deletion
policy. Source files remain while retained in a case; an authorized case
member can delete a file, and linked extracted or derived data must also be
removed or made inaccessible. The current deletion endpoint removes the source
object and document metadata; do not enable real materials until the policy
and cleanup of all derived data are operationally covered.

For running the Python app outside Compose, copy `.env.example` to `.env`,
install the project with `python -m pip install -e .`, and ensure PostgreSQL,
the configured S3 endpoint, and LibreOffice are available.

The codebase includes a Bedrock Converse extraction helper configured with
`BEDROCK_MODEL_ID` (and optionally `BEDROCK_REGION`). It validates each
proposed field against an exact quote from its named source document. The
helper is not exposed through an API while authentication is deferred.
Offer recommendations, cloud-drive imports, and outbound email are not
enabled. Existing document-processing code remains available in the codebase;
case/document and materials-import endpoints fail closed unless authentication
and case-membership authorization are explicitly enabled.
