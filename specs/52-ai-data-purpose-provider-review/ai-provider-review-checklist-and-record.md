# AI Provider and Data-Purpose Review Checklist and Record

**Status: Blank template. No provider review or qualified-counsel approval is recorded here.** Complete this record only from actual current evidence. Do not infer a provider setting from code, a public marketing page, a configured notice, or an operator-set flag. Keep issue #128 open until both provider and qualified-counsel evidence are supplied and retained.

The `AI_PROVIDER_REVIEW_EVIDENCE_VERIFIED` and `COUNSEL_REVIEW_EVIDENCE_VERIFIED` flags are separate operator-controlled gates. Neither flag is evidence, an attestation, a legal conclusion, or a guarantee. A provider review cannot substitute for counsel review; counsel review cannot establish provider settings or contractual commitments.

## Review identity and exact versions

- Product/repository:
- Issue/PR/release:
- Exact source commit SHA:
- Deployment/configuration identifier:
- Provider account/organization identifier (non-secret; do not include credentials):
- Provider and service/API:
- Exact model provider identifier/version:
- Provider region(s):
- Review date(s):
- Provider reviewer name, role, organization, and authority:
- Review scope/engagement reference:
- Qualified counsel review record reference (separate completed Spec 51 record):
- Evidence custodian and restricted evidence location:

## Evidence inventory

For each claim, record the exact, current evidence reference, document/version/date, relevant section or setting, reviewer, review date, status, and limitations. Preserve signed originals or immutable references under appropriate access controls. Do not copy secrets, case documents, personal data, or credentials into this checklist.

| Topic | Evidence reference/version and exact section or setting | Reviewer/date | Status: verified / not verified / unknown / not applicable | Limits, conditions, and follow-up |
|---|---|---|---|---|
| Executed provider agreement and applicable service terms | | | | |
| Exact service/API and model-specific terms | | | | |
| Provider account and model settings for customer-data use | | | | |
| Provider retention duration and event/data categories | | | | |
| Human access, support access, and human review | | | | |
| Product improvement, evaluation, fine-tuning, and generalized training settings | | | | |
| Deletion request path, timing, scope, and exceptions | | | | |
| Backups, replicas, caches, abuse monitoring, and retained copies | | | | |
| Subprocessors and their locations/services | | | | |
| Security controls, access controls, and incident terms | | | | |
| Data location and cross-border transfer terms | | | | |
| Model/service changes and notification/opt-out rights | | | | |
| Provider support/diagnostic data handling | | | | |
| Deployment logging, APM, proxy, and analytics destinations | | | | |
| Other relevant contractual or operational evidence | | | | |

Unknowns must remain marked unknown and must be reflected in the user notice and decision. Do not interpret absence of a setting or clause as a commitment that case content is not retained, reviewed, improved from, trained on, or shared with subprocessors.

## Actual application processing reviewed

Use the reviewed commit and deployed configuration, not this template's general descriptions, to verify the exact request and notice. Identify each item reviewed by path/version and SHA-256 or immutable artifact reference.

| Material | Exact path/artifact, version, SHA-256 or immutable reference | Reviewed date | Notes |
|---|---|---|---|
| Document-analysis disclosure, consent, request, worker and model call | `src/app/analysis.py`, `src/app/analysis_worker.py`, `src/app/ai.py`, UI state in `src/app/static/index.html` | | |
| Settlement-ranking disclosure, separate consent and model call | `src/app/settlement_routes.py`, `src/app/settlement_ai.py`, `src/app/settlement_planning.py`, UI state in `src/app/static/index.html` | | |
| Current provider/model/region and IAM configuration (redacted evidence) | `BEDROCK_MODEL_ID`, `BEDROCK_REGION`, deployment AWS identity/configuration | | |
| Exact document-analysis notice and version | `AI_ANALYSIS_NOTICE_VERSION`, `AI_ANALYSIS_DATA_HANDLING_NOTICE` and rendered UI | | |
| Exact settlement notice and version | settlement planning notice and rendered UI | | |
| AI-related application, infrastructure, proxy, APM and analytics logs | Enumerate actual configured destinations and retention settings | | |
| Spec 06/08/09/32/41/50/51 and additive Spec 52 | Record exact reviewed versions | | |
| Other processing paths or integrations discovered | Enumerate; include request/response evidence using non-real test data | | |

### Data and purpose determination

For each data category, describe the actual content, endpoint, purpose, retention, access, location, deletion treatment, and evidence. Mark any provider-side behavior unknown when evidence does not establish it.

| Data category / source | Application purpose | Sent to provider? exact fields/representation | Retention/access/training status and evidence | User notice/consent version | Conditions or exclusions |
|---|---|---|---|---|---|
| Selected extracted document text, opaque document ID, page provenance | User-requested document fact suggestions | | | | |
| User objective, adopted fact values/quotes, calculated scenario summaries, curated authority set | Separately user-requested scenario ranking | | | | |
| Other case/profile/ledger/attempt data | | | | | |
| Account identifiers, credentials, tokens | | | | | |
| Provider diagnostics, abuse-monitoring, and support data | | | | | |
| Application/infrastructure logs and telemetry | | | | | |
| Other | | | | | |

### Purpose-by-purpose decision

Do not treat one purpose's consent or contract term as permission for another. Explain the exact evidence and conditions for every determination.

| Purpose | Current code path? | Provider evidence and exact section | Counsel determination/evidence reference | Authorized scope, if any | Unresolved conditions |
|---|---|---|---|---|---|
| User-requested document analysis | Yes — see inventory above | | | | |
| User-requested settlement-scenario ranking | Yes — separate consent and payload | | | | |
| Provider retention or storage | Not controlled by these application calls | | | | |
| Human access/review | Not controlled by these application calls | | | | |
| Product improvement, evaluation, or fine-tuning | No case-content improvement pathway implemented here; vendor-side setting unverified until evidenced | | | | |
| Generalized model training using case content | No training pathway or training-consent flow implemented here; vendor-side setting unverified until evidenced | | | | |
| Other | | | | | |

## User-facing notice and consent record

- Exact final notice text for document analysis (attach or link; include version and SHA-256):
- Exact final notice text for settlement ranking (attach or link; include version and SHA-256):
- Exact provider/model/region displayed:
- Exact data-category/purpose descriptions displayed:
- Provider retention/human-review/improvement/training/deletion/subprocessor details disclosed, including unknowns:
- Distinct consent actions and purpose-specific records verified:
- Evidence that no analysis consent is represented or reused as training consent:
- Required notice changes, redlines, or accessibility/localization variants:
- Counsel-approved wording and separate Spec 51 evidence reference:

## Decision, limitations, and sign-off

- Provider review result and scope:
- Provider reviewer's signed evidence or verifiable record reference/date:
- Contractual/configuration limitations, exclusions, or unresolved questions:
- Required remediation, owner, due date, and production impact:
- Qualified counsel's separate written decision/evidence reference and date:
- Counsel's jurisdictions, qualifications, scope, conditions, and version reviewed:
- No case-content training/product-improvement use authorized by this record unless a separate future approval and consent flow is explicitly documented:
- Date provider evidence was independently verified:
- Date counsel evidence was independently verified:
- Deployment operator and evidence-verification/change ticket:
- Exact deployed release/configuration reviewed:
- Rollback/disable action if settings, contract, model, notices, or reviewed code changes:

Provider reviewer signature / verifiable approval:

Qualified counsel signature / separate Spec 51 reference:

Operator verification and date:

## Readiness flag change record

Complete only after the actual provider evidence above and separate Spec 51 counsel evidence are retained and independently checked against the exact release and deployed configuration.

- [ ] `AI_PROVIDER_REVIEW_EVIDENCE_VERIFIED=true` authorized and recorded by designated operator
- [ ] `COUNSEL_REVIEW_EVIDENCE_VERIFIED=true` authorized and recorded by designated operator under Spec 51
- [ ] `PRODUCTION_READINESS_REQUIRED=true` and all readiness checks independently pass
- [ ] User notice matches the reviewed provider, model, purpose, settings, and conditions
- [ ] No unresolved evidence gap is represented as verified

Flag-change ticket and operator:

Evidence location (restricted, durable, no case contents or secrets):

Date / deployment identifier:

**The checkboxes above are blank by design. A completed checklist and flags still do not guarantee provider behavior, legal compliance, or legal protection.**
