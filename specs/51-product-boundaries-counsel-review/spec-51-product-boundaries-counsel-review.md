# Spec 51: Product Boundaries and Qualified Counsel Review Gate

- **Status:** Engineering changes implemented; qualified counsel review and approval evidence pending. This spec does not state or imply that counsel reviewed or approved any product language.
- **Related issue:** [#127 — Define product legal boundaries and obtain counsel-reviewed disclosures](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/127)
- **Related work:** [#123 — Mediator-only iterative offer and outcome workflow](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/123), [#134 — Immediate permanent deletion](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/134)
- **Related specifications:** Specs [21](../21-settlement-offer-response-and-finalization/spec-21-settlement-offer-response-and-finalization.md), [23](../23-explicit-sent-confirmation-freeze/spec-23-explicit-sent-confirmation-freeze.md), [37](../37-mediator-offer-outcome-workflow/spec-37-mediator-offer-outcome-workflow.md), [38](../38-failure-recovery/spec-38-failure-recovery.md), [40](../40-rejection-stop-completion/spec-40-rejection-stop-completion.md), and [44](../44-immediate-permanent-deletion/spec-44-immediate-permanent-deletion.md)
- **Supersession:** Additive only. Historical specifications remain unchanged. This spec does not supersede #123's mediator-only, user-reported delivery workflow, #134's deletion boundaries, or any case-specific review/consent safeguards.

## Objective and limits

Inventory product surfaces that could be mistaken for legal advice, make one consistent factual boundary visible at relevant steps and in downloaded output, and prevent production case-data use until a deployment operator explicitly satisfies counsel-review readiness. This is engineering work, not a legal opinion, counsel review, launch approval, or guarantee of legal protection.

The proposed product disclosure is:

> **Proposed disclosure — pending qualified counsel review.** Casework is a preparation and organization tool, not legal advice or representation. It cannot guarantee correctness, fairness, acceptance, or any particular outcome. Review all source facts, assumptions, calculations, and proposal terms. If you choose to use a proposal, review it, download it, and provide it to your mediator. Downloading is not delivery; the product does not automatically deliver proposals. Any optional external transfer is user-initiated to a destination confirmed in the interface and is not proof of mediator receipt.

The disclosure is deliberately marked proposed and pending. Do not remove that status or represent the text as approved until the exact versioned materials receive qualified counsel review and the approval record required by the accompanying checklist is retained.

## Surface inventory and requirements

- **FR-51-01 — Marketing and onboarding:** The public product overview, account/case onboarding, and fictional examples distinguish preparation/organization from legal advice and representation; avoid outcome promises; and identify the user as the reviewer and mediator-delivery actor. Clearly label proposed language as pending counsel review.
- **FR-51-02 — AI analysis and ranking:** Explain at the analysis/consent and result-review points that AI output is a candidate suggestion, may be incomplete or incorrect, is not a verified fact or legal advice, and cannot be adopted without the existing user review action. Optional scenario ranking does not change deterministic values or guarantee an outcome.
- **FR-51-03 — Deterministic calculations and comparison:** Identify calculations as arithmetic based on entered assumptions and available values, not legal classifications, valuations, findings, or predictions. Missing/unresolved values remain explicitly unavailable. Chart comparisons do not resolve legal rights or guarantee acceptance.
- **FR-51-04 — Generated files:** Every generated DOCX proposal and XLSX schedule identifies itself as an unsigned/proposed draft and carries the proposed, pending-review boundary, review responsibility, mediator-facing purpose, and no-automatic-delivery statement. No download or generated-file response is described as delivery, filing, acceptance, legal approval, or legal resolution. Optional user-confirmed external transfer, if enabled, is distinguished from automatic delivery and does not prove receipt.
- **FR-51-05 — Finalization and completion:** Finalization copy distinguishes saving/freezing a proposal from reviewing it, downloading it, delivering it to a mediator, court filing, and any legal outcome. Accepted and rejection-stop guidance remains neutral and must not imply resolution, enforceability, required next steps, or guaranteed protection.
- **FR-51-06 — No unsupported representations:** Product copy must not claim that Casework is a law firm, is the user's attorney, provides individualized legal advice, has been reviewed or approved by counsel, has sent/delivered/filed a proposal when it has not, or guarantees correctness, fairness, acceptance, or an outcome.
- **FR-51-07 — Production readiness gate:** `COUNSEL_REVIEW_EVIDENCE_VERIFIED` defaults to false. When `PRODUCTION_READINESS_REQUIRED=true`, missing qualified-counsel evidence is a readiness failure and the existing case-data middleware returns 503 for case-data routes, including AI analysis and proposal generation. Only a designated operator may set the evidence flag after completing and retaining the Spec 51 checklist/record. The application cannot verify the quality, identity, scope, or legal sufficiency of that evidence. Local/demo environments may retain their existing preview behavior; they are not production authorization.
- **FR-51-08 — Versioned counsel evidence:** The review record identifies the exact code commit/release, material paths and SHA-256 digests, generated DOCX/XLSX examples, disclosure/consent/terms versions, legal clauses and optional delivery behavior in scope; qualified reviewer credentials/jurisdiction; written approval or redlines; any conditions; and the deployment operator's flag-change evidence. Any material change invalidates prior approval until counsel determines whether re-review is required.
- **FR-51-09 — Historical specs:** Keep Specs 21, 23, 37, 38, and 40, plus the permanent deletion record in Spec 44, unchanged. Maintain their existing user-confirmed, mediator-only, no-inferred-delivery, failure, completion, and deletion constraints.

## Acceptance criteria

1. Product and generated-output surfaces use consistent, factually accurate boundary language visibly marked pending counsel review.
2. Tests assert required disclosures on marketing, onboarding, AI, calculation/comparison, proposal-file, finalization, and completion surfaces and reject unsupported attorney, delivery, or guarantee claims.
3. Generated DOCX and XLSX files both carry the disclosure and make no claim of automatic delivery or confirmed receipt.
4. With production readiness required and counsel evidence unverified, the readiness result includes a safe missing-evidence code and case-data routes are unavailable. The default evidence flag is false.
5. A blank checklist/record template enumerates exact materials/versions and approval evidence; no false review result is populated.
6. No historical specification is modified.

## Implementation boundary and unresolved items

Engineering inventory and proposed copy are in `src/app/static/index.html`, `src/app/offer_documents.py`, and `README.md`. The production gate is in `src/app/config.py` and is configured through `.env.example`. `counsel-review-checklist-and-record.md` is intentionally an uncompleted template.

**Still required before production launch:** a qualified Washington attorney's review of the exact implementation and generated materials, a completed and retained evidence record (including approved/redlined copy and scope), resolution of all review conditions, and operator verification of the deployed version before setting `COUNSEL_REVIEW_EVIDENCE_VERIFIED=true` with `PRODUCTION_READINESS_REQUIRED=true`. The source repository contains no such review or approval.
