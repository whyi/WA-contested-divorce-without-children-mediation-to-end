# Spec 02: Overall Requirements

- **Status:** Draft
- **Objective:** Define a secure, AI-assisted workflow for Washington State
  contested divorce cases without children, from gathering case materials
  through iterative settlement negotiations and preparation for decree.
- **Scope note:** This draft captures the product direction and core workflow.
  Legal requirements must be supported by authoritative citations before
  implementation or treatment as complete. AI output is decision support, not
  legal advice or a guarantee of an outcome.

## 1. End-to-End Workflow

### 1.1 Authentication and case access

1. `LOGIN`: The user signs in to an account. Successful sign-in proceeds to
   case setup; failed sign-in remains at `LOGIN` and displays an actionable
   error. The login experience must support social sign-in using an
   OpenID Connect (OIDC) identity provider. Candidate providers include
   Google, Apple, and Microsoft; the initial provider set is an open decision.
   Account registration and recovery remain open decisions.
2. The system authorizes the account for the selected case before allowing
   access to its data. Signing in does not, by itself, verify that a person is
   a party or legal representative or establish legal authority to act.

Authentication and case-level authorization are prerequisites for uploading,
importing, viewing, or changing case materials and for every later workflow
action. The current application has no authentication or authorization and
must not be used with real case information until appropriate controls are
implemented.

### 1.2 Materials preparation: choose a mode

After creating or opening a case, the user chooses one of two modes. Both modes
produce a common, reviewable case-information workspace and proceed to AI
analysis.

#### Mode A: “My case materials are ready — organize them for me”

The user can add documents from their device or connect an external storage
provider. Candidate providers include Google Drive, Microsoft OneDrive, and
Dropbox; exact providers, permissions, and implementation order are open
decisions.

The system imports only files the user selects, stores working copies in
access-controlled object storage (AWS S3 in the selected initial architecture),
and analyzes them to extract candidate case facts and settlement terms. The
system may prefill corresponding wizard fields, but must preserve a link from
each populated value to its source document and location where available.
Extracted values are drafts: the user must be able to inspect, correct, reject,
or mark them unknown. Uncertain or conflicting information must be surfaced,
not silently resolved or presented as fact.

#### Mode B: “Guide me through the wizard”

The user enters party information and settlement facts and terms through
guided steps. The system saves progress server-side and indicates whether
changes are saving, saved, or failed to save.

At any point before AI analysis, the user can choose “Add supporting materials”
and provide device uploads or files selected from a connected provider, as in
Mode A. The system analyzes these materials and presents proposed additions or
conflicts for review before updating the case-information workspace.

The workflow is for cases without children. Child custody and parenting-plan
fields are out of scope.

### 1.3 AI analysis and offer iteration

After materials are gathered, the system analyzes the reviewed case
information and available negotiation history to propose a settlement offer.
The proposal should explain its assumptions, supporting source materials,
estimated trade-offs, and material uncertainties. The system must not promise
that an offer is “best,” guarantees acceptance, or prevents all financial
losses. It must not invent facts or legal requirements when source information
is missing.

The user reviews and edits the proposed terms. The system may generate a
readable offer document, such as a PDF, from the approved terms. Before any
external communication, the user must inspect the final document and
explicitly confirm the recipient and send action. No offer may be sent
automatically by the AI.

After sending, the negotiation is tracked through explicit user-reported
outcomes, such as `ACCEPTED`, `REJECTED`, or `COUNTEROFFER_RECEIVED`. The user
may add a counteroffer document or other supporting materials. The system
records the response and documents, updates the analysis, and proposes a
revised response for user review. This cycle may repeat until the user records
acceptance or chooses to stop.

Acceptance ends the offer-iteration loop; it does not itself establish that a
legally sufficient settlement, court filing, or decree exists. Settlement
confirmation, required forms, legal review, decree generation, and filing
must be specified with authoritative legal sources before those functions are
built or represented as complete.

## 2. Functional Requirements

- **FR-02-01 — Sign-in and case authorization:** The system must require a
  signed-in, case-authorized account before exposing or changing case data.
- **FR-02-02 — Social sign-in:** The login experience must support
  authentication through configured OIDC social identity providers. The
  system must validate the provider's authentication response and must not
  receive or store the user's provider password. A provider login must not,
  by itself, grant access to any case or prove party identity or legal
  authority. Account linking and duplicate-account handling must not grant
  access across accounts without an authenticated, explicit linking flow.
- **FR-02-03 — Select materials-preparation mode:** For each case, the user
  must be able to choose either the AI-assisted existing-materials mode or
  guided wizard mode. Both must lead to the same case-information workspace
  and subsequent analysis workflow.
- **FR-02-04 — Import selected materials:** The system must accept supported
  documents selected for upload or import from an enabled external provider.
  It must not import an entire account or drive by default. It must show
  import progress and report unsupported files, permission failures, and
  import errors without claiming a failed import succeeded.
- **FR-02-05 — Secure document storage:** Imported working copies and derived
  case data must be stored with access controls that prevent access by
  unauthorized users. Encryption, key management, retention, deletion, and
  backup requirements must be defined before real case data is accepted.
- **FR-02-06 — Extract and map with provenance:** AI-extracted values proposed
  for wizard fields must retain source-document provenance where available.
  The system must distinguish extracted content from user-confirmed content,
  flag uncertainty and conflicts, and allow the user to correct or reject
  proposed values.
- **FR-02-07 — Guided entry and persistence:** Guided steps must provide
  previous and next navigation, preserve entered data, validate required
  fields before forward progression, and show saving, saved, or save-failed
  status. Required-field rules must be defined from product needs and
  authoritative legal sources, not guessed by the AI.
- **FR-02-08 — Add materials from guided mode:** The user must be able to add
  supporting materials during guided entry. Extracted values or conflicts must
  be presented for user review before changing the case-information
  workspace.
- **FR-02-09 — Generate explainable offer proposal:** The AI must base a
  proposal on available case information and negotiation history, identify
  material assumptions and uncertainties, and show the user the proposed
  terms and trade-offs before the user can approve them for document
  generation.
- **FR-02-10 — User-controlled outbound offer:** The system must let the user
  review and edit an offer document and explicitly confirm both its recipient
  and sending. The AI must not send an email or other external communication
  without that confirmation. Sent content, recipient, time, and user-confirmed
  action must be retained in the case history, subject to the retention policy.
- **FR-02-11 — Record negotiation outcome:** After an offer is sent, the user
  must be able to record an outcome such as accepted, rejected, or
  counteroffer received, and attach relevant new materials.
- **FR-02-12 — Iterate with review:** New outcomes and materials must be
  included in a subsequent analysis. Revised recommendations and documents
  require user review and approval; previous offers and outcomes must remain
  available in the negotiation history.
- **FR-02-13 — Stop or close the loop:** The user must be able to stop
  negotiation iterations. Recording acceptance ends the offer loop but must
  not be represented as court approval, filing, or entry of a decree.

## 3. Non-Functional Requirements

- **NFR-02-01 — Responsiveness:** Ordinary wizard navigation and save
  acknowledgement should complete within 200 ms at the 95th percentile under a
  benchmark environment and load profile defined before release. Document
  ingestion and AI analysis are asynchronous operations and must show progress;
  their service-level targets remain to be defined.
- **NFR-02-02 — Recovery and authorization:** A user must be able to resume
  successfully saved progress after reconnection, subject to authentication,
  case authorization, and retention policy. Expired or revoked access must not
  expose case content.
- **NFR-02-03 — AI transparency:** AI-generated extractions and offers must be
  distinguishable from user-provided or user-confirmed information. Material
  assumptions, uncertainty, conflicts, and source references must be
  available to the user.
- **NFR-02-04 — Auditability:** Material uploads/imports, extraction review,
  user edits, offer versions, approvals, send actions, and reported outcomes
  must have an attributable, time-ordered history. Logs must not expose
  credentials or unnecessarily duplicate sensitive document contents.

## 4. Dependencies and Open Decisions

- Choose initial OIDC social sign-in providers, account registration and
  recovery behavior, secure account linking, case access grants, and any
  identity or representative-authority verification.
- Choose initial document types, size limits, malware-scanning approach, and
  extraction support.
- Select external storage providers and define OAuth scopes, token storage,
  revocation, provider failure handling, and whether imported files are copied
  or accessed in place.
- Define encryption, key management, retention, deletion, backup, data
  residency, and incident-response requirements for sensitive family-law data.
- Define the case data model, field mapping, confidence handling, conflict
  resolution, and human-review experience for AI extraction.
- Define what “realistic” offer recommendations mean, which financial and
  legal assumptions may be used, how sources are presented, and what
  professional review or disclaimers are required. No recommendation can
  guarantee acceptance or a no-loss outcome.
- Choose email delivery provider, sender identity, recipient verification,
  editable document format, and handling of bounced or disputed delivery.
- Define negotiation history, acceptance confirmation, stopping conditions,
  and any post-acceptance settlement or decree workflow.
- Add authoritative Washington State sources and verification dates for
  eligibility, required disclosures, settlement agreements, court forms,
  procedure, and filing.
- Define performance benchmark and load targets.

## 5. Legal Requirements

Legal requirements for forms, eligibility, disclosure, procedure, review, and
filing must be added here with authoritative citations and the date each
source was verified. No case-specific legal requirements are asserted by this
draft.
