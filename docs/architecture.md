# Architecture & Technology Stack: WA Contested Divorce Mediation-to-Decree Wizard

## 1. Overview
This document defines the core technology stack, database architecture, file storage strategy, and document round-trip conversion pipeline for the Washington State contested divorce mediation-to-decree automation wizard.

The system bridges unstructured mediation negotiations (asset sharing, informal offers, and settlement clauses) with formal Washington State mandatory court forms and custom separation contracts.

---

## 2. Core Technology Stack

### Backend Framework
- **Python 3.11+ / FastAPI:** High-performance asynchronous API framework optimized for handling document uploads, data validation, and multi-step workflow states.

### Database & Storage
- **Relational Database (PostgreSQL):**
  - Manages user sessions, case metadata, negotiation logs (offer/counter-offer history), and structured asset/liability inventories.
- **Object Storage (AWS S3 / Azure Blob Storage):**
  - Secure storage for binary document assets, including generated Word templates, PDF previews, user-edited `.docx` files, and final court form packages.
  - Initial implementation selects AWS S3 and uses MinIO's S3-compatible API for local development; Azure Blob is not implemented.

---

## 3. Document Round-trip & Conversion Pipeline

To support the core user workflow—**"Generate PDF Preview ➔ Edit via Editable Word (`.docx`) ➔ Re-upload & Parse ➔ Update State & Finalize"**—the system integrates the following Python libraries:

1. **Template Generation (`python-docx-template` / `Jinja2`):**
   - Injects structured negotiation data (asset values, agreement clauses) into predefined Word templates to generate initial settlement drafts.
2. **Word-to-PDF Rendering (`docx2pdf` / LibreOffice Headless):**
   - Compiles `.docx` files into clean PDF format for web-based visual preview by users. The Docker/Linux path uses LibreOffice headless; `docx2pdf` is used on Windows/macOS where Microsoft Word is available.
3. **PDF-to-Word Reverse Conversion (`pdf2docx`):**
   - Parses layout, tables, and text structures of PDF documents to provide editable `.docx` files when users request modifications.
4. **Parsing & State Synchronization (`python-docx`, `PyMuPDF`, `pypdf`):**
   - Extracts modified text and clause changes from re-uploaded Word files, updates the Single Source of Truth (SSOT) data model, and injects final data into official Washington State court form PDFs (`FL Divorce 241`, `FL All Family 131`, etc.).

---

## 4. Infrastructure & Deployment

- **Containerization (Docker):**
  - Mandatory for packaging system dependencies. A custom Docker container installs LibreOffice for consistent Linux-side rendering and conversion.
- **Hosting Target:**
  - **AWS ECS (Fargate)** or **Azure Container Apps** to maintain persistent container execution environments, avoiding serverless function execution limits and file system constraints.

## 5. Specification Implementation & TDD

Implementations of repository specifications MUST use test-driven development:

1. Read the applicable specification and identify its observable acceptance criteria.
2. Add or update the automated tests for those criteria before changing production code.
3. Run the focused tests and confirm that the new tests fail for the expected reason.
4. Implement the smallest production change that makes those tests pass.
5. Run the focused tests and the repository validation suite; fix regressions before committing.

Every changed production Python module must have corresponding automated test
coverage. The repository's pre-commit hook checks staged Python changes for a
test-file pairing and runs the test suite. A commit must not proceed if either
check fails.

The hook is a final guard, not proof of test-first ordering: it verifies the
presence of a paired test and passing tests at commit time, but cannot establish
when the test was authored. Contributors and coding agents are responsible for
following and reporting the red-green sequence. A hook installed under
`.git/hooks` is local to one clone; shared enforcement requires distributing a
tracked hook and/or running equivalent pairing and test checks in CI.

## 6. Permanent Deletion Boundary

Case closure remains reversible and is not a deletion mechanism; see Spec 32.
Confirmed permanent deletion is defined by Spec 44. The application stores
uploaded source objects in an S3-compatible bucket, while generated proposal
files and extracted/analysis data are stored in database rows. Deletion
tombstones block active application access and stale work, and the storage
adapter enumerates and deletes all known S3 object versions and delete markers.
Production deletion therefore requires `ListBucketVersions` and
`DeleteObjectVersion` permissions; failure to enumerate or purge is explicit.

The repository has no production database-backup/snapshot configuration,
restore process, or independently retained tombstone ledger. A restore from a
snapshot predating a deletion could therefore restore data without the
tombstone. The application must not claim synchronous purge of provider-managed
backups or non-resurrection after such a restore until deployment-specific
backup and restore behavior is configured and verified.
