# WA-contested-divorce-without-children-mediation-to-end
AI-driven SDD wizard guiding Washington State contested no-children divorce cases from mandatory settlement conference to final decree.

## Repository workflow

Read the applicable specification in `specs/` before making changes. Run checks
with `bash harness/validate.sh`. To run another command and capture its output,
invocation, timestamp, and exit status, use
`INTERACTION_LOG=interactions/<spec-number>-<name>/response-<spec-number>-<name>.md bash harness/validate.sh -- <command> [arguments...]`.
The harness appends each execution to the selected log; without `INTERACTION_LOG`,
it uses `interactions/00-initialization/response-00-init.md`.

## Application foundation

The initial application foundation follows
[Spec 01](specs/01-tech-stack-override/01-tech-stack-override.md): Python 3.11+,
FastAPI, PostgreSQL, S3-compatible object storage, and a Docker image with
LibreOffice for DOCX-to-PDF rendering. AWS S3 is the selected object-storage
provider; local development uses MinIO through the S3 API. Azure Blob Storage is
not implemented in this first iteration.

Run locally with Docker Compose:

```sh
docker compose up --build
```

The API is available at `http://localhost:8000`; OpenAPI documentation is at
`/docs`. PostgreSQL migrations run as the API container starts. The compose
configuration binds the API to localhost and uses development-only MinIO
credentials. This foundation has no authentication or authorization and is not
suitable for real case information or public deployment. Add identity, access
control, retention, and production secret management before handling sensitive
documents.

For running the Python app outside Compose, copy `.env.example` to `.env`,
install the project with `python -m pip install -e .`, and ensure PostgreSQL,
the configured S3 endpoint, and LibreOffice are available.

Document uploads are size- and format-checked. DOCX templates are rendered in a
Jinja sandbox; uploaded edits are parsed into a review-pending extraction record.
Extracted wording is not automatically interpreted as legal terms or applied to
case data because the spec does not define a field-mapping or approval workflow.
This keeps document processing auditable without guessing at legal meaning.
