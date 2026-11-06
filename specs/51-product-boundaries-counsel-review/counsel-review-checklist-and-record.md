# Spec 51 Counsel Review Checklist and Record Template

**Status:** Template only — no qualified counsel review or approval is recorded here. Do not set `COUNSEL_REVIEW_EVIDENCE_VERIFIED=true` until a qualified reviewer completes this record and the evidence is retained.

## Review package identity

- Product/repository:
- PR/release identifier:
- Exact source commit SHA:
- Deployment/configuration identifier:
- Review date(s):
- Reviewer name:
- Jurisdiction(s) and bar/license identifier:
- Qualification/role relevant to Washington family-law product review:
- Engagement or written scope reference:

## Exact materials reviewed

Record each material's version/commit, path or generated artifact name, and SHA-256 digest. Attach copies or a durable evidence link. Include all pages/states and both themes where presentation changes.

| Material/version | Exact path or artifact | SHA-256 / immutable reference | Reviewed (date) | Notes/redlines |
|---|---|---|---|---|
| Marketing/homepage and footer | `src/app/static/index.html` — public landing page and expectation disclosure | | | |
| Signup, account and case onboarding | `src/app/static/index.html` — account section and `case-create-dialog` | | | |
| AI analysis notice, consent, suggestions and adoption | `src/app/static/index.html`, `src/app/analysis.py`, `src/app/ai.py` | | | |
| Settlement scenario ranking/consent | `src/app/static/index.html`, `src/app/settlement_routes.py`, `src/app/settlement_ai.py` | | | |
| Deterministic planning, asset allocation, chart and comparison | `src/app/settlement_planning.py`, `src/app/offer_comparison.py`, `src/app/static/index.html` | | | |
| Proposal generation/template wording and generated DOCX | `src/app/offer_documents.py`; attach exact `.docx` generated from representative non-real test data | | | |
| Generated property schedule | `src/app/offer_documents.py`; attach exact `.xlsx` generated from representative non-real test data | | | |
| Proposal download, optional external transfer and destination confirmation | `src/app/settlement_routes.py`, `src/app/export_delivery.py`, `src/app/static/index.html` | | | |
| Finalization, user sent-confirmation, delivery/response claims | `src/app/settlement_routes.py`, `src/app/offer_response.py`, `src/app/static/index.html` | | | |
| Accepted and rejected completion guidance | `src/app/static/index.html`, Spec 40 | | | |
| Product terms, marketing claims, consent and relevant privacy notices | Enumerate exact file paths and versions | | | |
| Data deletion and backup/restore statements relevant to product claims | Spec 44 and exact deployed deletion/backup disclosures | | | |
| Proposed product disclosure | Spec 51; enumerate every rendered copy and generated-file copy | | | |
| Other materials in scope | Add each exact file, version and digest | | | |

## Review scope and evidence

- Confirm the reviewer examined actual rendered UI and both generated file formats, not only this checklist.
- Confirm actual delivery mechanisms, including optional user-confirmed email/cloud transfers, are accurately described; distinguish sending from downloading, delivery from receipt, and user reports from system verification.
- Record evaluation of statutes, court/procedure claims, proposal boilerplate, signatures, generated templates, AI analysis/ranking, calculations, comparisons, completion prompts, privacy/data handling, and any promises or disclaimers.
- Written approval evidence (attach signed letter/email or durable system-of-record reference; include date and exact approved materials/version):
- Approved language (attach exact final copy/version):
- Redlines and disposition:
- Conditions, exclusions, jurisdictions, audience, use restrictions, and required ongoing notices:
- Findings/review issues still open:
- Counsel's statement of scope limits (if applicable):

## Decision

- [ ] Approved for the explicitly described scope and exact versions above.
- [ ] Approved subject to the conditions below; production remains blocked until conditions are met.
- [ ] Not approved; production remains blocked.
- [ ] Further review required; production remains blocked.

Conditions and required changes:

Reviewer signature / verifiable approval evidence:

Date:

## Version-change and launch evidence

- Material changes since reviewed commit and counsel's re-review determination:
- Exact deployed commit/release:
- Checklist/approval evidence location and access controls:
- Operator who verified the evidence:
- Operator's flag-change ticket/change record:
- Date `COUNSEL_REVIEW_EVIDENCE_VERIFIED` was enabled:
- Confirmation `PRODUCTION_READINESS_REQUIRED=true` in the deployed environment:
- Rollback/disable action if reviewed materials change:

The configuration flag is an operator-controlled gate only. It is not proof that review occurred, an attorney opinion, legal approval, or a guarantee of legal protection.
