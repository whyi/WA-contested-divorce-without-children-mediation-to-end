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

Stored materials are not extracted on upload or status polling. A separate
PostgreSQL-backed extraction worker and per-document status API are available
for the later consent-authorized analysis flow; no job is enqueued until that
flow records the user's affirmative consent. PDF page text and source
provenance are retained for downstream review. OCR is not configured, so pages
without selectable text are marked as needing attention rather than reported
as analyzed. The extraction worker does not call an AI provider.

AI analysis is a separate, asynchronous workflow. It remains disabled unless
`AI_ANALYSIS_ENABLED`, `BEDROCK_MODEL_ID`, `BEDROCK_REGION`,
`AI_ANALYSIS_NOTICE_VERSION`, and `AI_ANALYSIS_DATA_HANDLING_NOTICE` are
configured. Before a request can be queued, the user sees the provider/model,
purpose, selected document data sent, and deployment-supplied handling notice
and must explicitly consent. Analysis reads only completed extracted text;
verified proposals and exact source quotations remain separate from case
data. The `analysis-worker` service does not call Bedrock while idle or when
analysis is disabled. Local Compose keeps the feature disabled in demo mode.

Authorized case members can review each verified proposal against its source,
record an accept/edit/reject decision, and explicitly adopt only a selected
subset. Adopted values are stored as append-only case-profile facts with
source, consent, model, and decision provenance; conflicting values remain
visible together. Review and adoption do not overwrite the existing case JSON
profile or trigger another AI request.

Authorized case members can also read and replace relationship milestones and
property acquisition facts through `GET /cases/{case_id}/property-tracing` and
`PUT /cases/{case_id}/property-tracing`. Milestones and asset facts are stored
in dedicated case JSONB fields; the response derives separate-property,
community-property, post-separation, or review-required candidates from the
reported facts. These are organizational prompts, not legal determinations.
The fictional analysis preview and browser-only wizard do not send these facts
to the API. Apply database migration `0007_property_tracing` before using the
new case fields.

Evidence-grounded settlement planning is available only in an authorized,
non-demo case workspace after migration `0008_settlement_planning`. It stores
append-only, cent-denominated ledger events, requires current profile and
ledger revisions for writes, and validates source references against active,
source-backed adopted facts. Scenario calculations are bounded to 12 explicit
date, tracing, and proposed-allocation combinations; AI ranking is optional and
requires a separate, revocable purpose-specific consent. Configure
`AI_ANALYSIS_ENABLED`, `BEDROCK_MODEL_ID`, `BEDROCK_REGION`, and
`SETTLEMENT_PLANNING_DATA_HANDLING_NOTICE` before the provider ranking can be
used. The consent notice lists the configured provider, model, region, data
sent, and handling notice. Calculated candidates remain available without AI
ranking, and provider or response failures are returned separately from the
calculated results. The selected scenario can produce an editable, nonbinding
DOCX draft; it is not stored, sent, or filed automatically.
The public `/demo` page has a fictional date-range preview: users can drag the
start/end markers on the asset chart or enter `Start Date` and `End Date
(Division Date)` in calendar controls. Three sample share scenarios recalculate
from the selected interval. They are deterministic examples, not AI rankings or
legal conclusions; the end date is not necessarily a separation or
characterization date. The demo is not connected to case data, saved, or sent
to an AI provider.

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

The codebase uses the Bedrock Converse API for consent-authorized analysis.
Every proposal must match an exact quotation from its source and, for PDFs,
the cited page. Documents are treated as untrusted data; model output is
persisted as a suggestion and is never applied to the case profile. Provider
credentials remain server-side, and document text, prompts, and quotations
must not be written to logs.
Offer recommendations, cloud-drive imports, and outbound email are not
enabled. Existing document-processing code remains available in the codebase;
case/document and materials-import endpoints fail closed unless authentication
and case-membership authorization are explicitly enabled.
