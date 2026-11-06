# WA-contested-divorce-without-children-mediation-to-end
A preparation and organization workspace for Washington divorce-without-children mediation materials and user-reviewed proposals. It is not legal advice, and no outcome is guaranteed.

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
The Google Drive and Dropbox **materials-import** pickers remain unavailable;
they are separate from the provider connections used for proposal exports.
Import-provider registration, scopes, token lifecycle, and deployment settings
must be established before enabling those pickers. The wizard remains a
preview-only screen. The local Docker Compose preview enables a demo-only account (`demo` /
`demo`) to exercise sign-in and the empty dashboard. Demo mode is restricted to
localhost and never enables case-data APIs. Outside that local preview,
authentication and case-data APIs remain disabled by default; case/document
APIs require explicit authentication and case-membership configuration. Every
case is protected by an explicit case-membership grant, and signup or social
login never grants case access. Do not submit real case information.

Case setup asks whether the other party has already made an offer
([Spec 33](specs/33-existing-offer-intake/spec-33-existing-offer-intake.md)).
A "yes" requires an uploaded offer document or non-empty notes, enforced by
the API; notes can later be related to individual assets, and the first
attempt of such a case is labelled an initial incoming offer.

A confirmed final proposal download finalizes the attempt: it saves a snapshot
of both sides' values and the generated files and makes the attempt read-only,
without charging beyond the existing per-version document credit and without
recording the files as sent
([Spec 35](specs/35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md)).

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
with an explicit limitation that vendor-side retention, human access/review,
product improvement/training, subprocessors, and deletion are not independently
verified by this application, and must explicitly consent. Analysis reads only
completed extracted text;
verified proposals and exact source quotations remain separate from case
data. The `analysis-worker` service does not call Bedrock while idle or when
analysis is disabled. Provider-call helpers also fail closed without explicit
purpose-specific consent. Local Compose keeps the feature disabled in demo mode.
Generalized training or product-improvement use of case content is not
implemented in this application and is not authorized by analysis consent.

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
sent, and handling notice; its consent is separate from document-analysis
consent. Calculated candidates remain available without AI
ranking, and provider or response failures are returned separately from the
calculated results. After a user selects a current scenario, the case workflow
can generate an unsigned CR 2A-style DOCX proposal and an editable XLSX
property schedule. These drafts are not stored or sent by generation/download;
a signed agreement may have legal effect. The product-boundary disclosures and
proposal boilerplate are proposed wording pending qualified counsel review;
they are not an attorney opinion or a guarantee of legal protection. Users must
review all facts, assumptions, calculations, and proposal terms. Downloading
does not deliver a proposal; the user is responsible for providing it to the
mediator. The app does not automatically deliver proposals.

Production case-data endpoints, including sensitive analysis and proposal
generation, are blocked when `PRODUCTION_READINESS_REQUIRED=true` until all
readiness checks pass. That includes
`COUNSEL_REVIEW_EVIDENCE_VERIFIED=true`, which may be set only after qualified
counsel has reviewed the exact versioned materials in Spec 51 and the review
record is retained. If AI is enabled in production, it additionally requires
`AI_PROVIDER_REVIEW_EVIDENCE_VERIFIED=true` after current provider evidence is
reviewed under Spec 52. These distinct flags are operator-controlled gates, not
evidence that a review occurred or a guarantee of provider behavior. Both
evidence flags default false; production deployments must explicitly require
readiness. No signed provider evidence or qualified-counsel review is currently
recorded; keep AI out of production until both are independently supplied and
verified.

Migration `0009_cr2a_property_exports` adds encrypted Google Drive/Dropbox
connections and minimal delivery audit records. Google Drive linking uses the
existing `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` with the `drive.file`
scope. Register `${AUTH_PUBLIC_BASE_URL}/api/export-integrations/google_drive/callback`
as an authorized redirect URI (without a duplicate slash). Dropbox delivery
additionally requires `DROPBOX_APP_KEY` and `DROPBOX_APP_SECRET` and the
redirect URI `${AUTH_PUBLIC_BASE_URL}/api/export-integrations/dropbox/callback`.
Provider refresh tokens require `AUTH_ENCRYPTION_KEY` (at least 32 bytes).
Email delivery uses the configured `SMTP_HOST` and `AUTH_EMAIL_FROM` settings.
If a destination is not configured, its delivery option stays unavailable while
DOCX/XLSX downloads remain available within authenticated real-case workflows.
Upload/email occurs only after the user confirms the exact destination; exports
are not sent to AI.
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
existing records; unassigned existing cases remain inaccessible. Compose
publishes the API at `http://192.168.1.17:8001` for the requested LAN preview;
the local S3 endpoint remains bound to localhost. Compose uses development-only
S3 mock credentials.

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

Attempt-credit checkout is disabled in demo mode. For a reviewed production
deployment, configure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
`STRIPE_PRICE_ID_ATTEMPT_CREDITS_5`, and
`STRIPE_PRICE_ID_ATTEMPT_CREDITS_10` with active, one-time USD Stripe Prices
matching the server catalog: 5 credits for USD $5 and 10 credits for USD $8.
Stripe Tax calculates, displays, and collects applicable tax; Stripe emails
receipts. There are no monthly subscriptions. A full refund is available within
30 days only before any credit from the package is used; once used, no package
refund is available. Service-failure credit restoration remains separate.
Another package can be purchased only after the case balance reaches zero.
Register `/api/billing/webhook` for checkout completion, delayed-payment,
expiration, failure, and refund events. Credits are granted only after webhook
signature verification and idempotent payment processing; a browser redirect
alone never grants credits. See [Spec 48](specs/48-credit-package-pricing/spec-48-credit-package-pricing.md)
for approved terms and [Spec 36](specs/36-attempt-credit-packages/spec-36-attempt-credit-packages.md)
for the free first successful finalization per case and subsequent credit policy.

Case-material storage is separately gated by `CASE_MATERIALS_ENABLED` and
requires authenticated case-data access. Production case-data access requires
`S3_KMS_KEY_ID` for a customer-managed AWS KMS key; uploads explicitly request
SSE-KMS, and there is no unencrypted production fallback. Loopback-only local
S3 development does not use KMS. Production buckets must block public access,
and the application role must be limited to the configured bucket and KMS key.
Before enabling real uploads, document the
retention period, backup/versioning behavior, legal-hold process, and deletion
policy. Source files remain while retained in a case; an authorized case
owner can permanently delete a material or case with a separate typed
confirmation. Account deletion requires password reauthentication and removes
all owned cases and credentials. See
[Spec 44](specs/44-immediate-permanent-deletion/spec-44-immediate-permanent-deletion.md)
for the exact API, cascade, and guarantee boundaries. Deletion enumerates and
purges known S3 object versions/delete markers, and requires version-list and
version-delete permissions. A database tombstone blocks stale application
requests and worker retries.

The repository's Compose stack only defines local Postgres and Moto; it does
not define production database snapshots/backups, a restore workflow, or an
independently protected tombstone ledger. Therefore it cannot verify that a
provider-managed database restore will not resurrect deleted records. Do not
claim that provider backups or snapshots were purged, and do not enable real
case materials until the deployment backup/restore and retention guarantees
are operationally configured and verified.

The production-readiness checklist and fail-closed configuration gate are
documented in the
[security, backup, and restore readiness runbook](docs/production-security-backup-restore-readiness.md).
`PRODUCTION_READINESS_REQUIRED=true` keeps `/readyz` and case/document access
unready while required settings or evidence gates are missing. It does not
replace operator sign-off or prove a restore, backup purge, or alert delivery.
The [owner-only beta environment boundaries](docs/owner-beta-environment-boundaries.md)
define the intended separation for local development, public demos, future
owner-only UAT, and future production. A hosted UAT deployment is not currently
defined or verified.

For running the Python app outside Compose, copy `.env.example` to `.env`,
install the project with `python -m pip install -e .`, and ensure PostgreSQL,
the configured S3 endpoint, and LibreOffice are available.

The codebase uses the Bedrock Converse API for consent-authorized analysis.
Every proposal must match an exact quotation from its source and, for PDFs,
the cited page. Documents are treated as untrusted data; model output is
persisted as a suggestion and is never applied to the case profile. Provider
credentials remain server-side, and document text, prompts, and quotations
must not be written to logs. See [Spec 52](specs/52-ai-data-purpose-provider-review/spec-52-ai-data-purpose-provider-review.md)
and its [provider review checklist](specs/52-ai-data-purpose-provider-review/ai-provider-review-checklist-and-record.md)
for the code evidence inventory and unverified provider/counsel evidence.
Offer recommendations, cloud-drive imports, and outbound email are not
enabled. Existing document-processing code remains available in the codebase;
case/document and materials-import endpoints fail closed unless authentication
and case-membership authorization are explicitly enabled.

## Document processing limits

PDFs are processed up to `MAX_PDF_PAGES` pages (default 200, same for all
plans; DOCX has no page limit). Larger PDFs stay stored but extraction ends
`needs_attention`. OCR is not supported, so scanned PDFs need a text-based
version, and encrypted PDFs must be unprotected before upload. See
[Spec 46](specs/46-document-processing-limits/spec-46-document-processing-limits.md).
