# Spec 16: Evidence-Traced Settlement Planning

- **Status:** Implemented (initial workflow; Washington counsel review required)
- **Related issue:** [#63 — Build evidence-grounded property tracing, ranked settlement scenarios, and offer drafts](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/63)
- **Depends on:** [Spec 08: Consent-Based Document Analysis](../08-consent-based-document-analysis/spec-08-consent-based-document-analysis.md), [Spec 09: Review and Selectively Adopt AI Document Suggestions](../09-ai-suggestion-review/spec-09-ai-suggestion-review.md), and [Spec 15: Property Acquisition Tracing](../15-property-acquisition-tracing/spec-15-property-acquisition-tracing.md)
- **Objective:** Help Washington no-children divorce users inspect evidence-linked source-of-funds calculations, compare a small number of explicitly hypothetical settlement scenarios, and prepare an editable, nonbinding mediation-offer draft.
- **Scope:** Real authorized case data only; reviewed/adopted or user-entered facts; dated asset/account events; reproducible calculations under explicitly chosen accounting assumptions; bounded scenario generation and AI ranking; editable DOCX offer drafts. This is not a court filing, legal conclusion, valuation, prediction, or substitute for counsel.
- **Jurisdiction:** Washington State only. The rule profile must cite current, reviewed primary authorities and must not infer that a marriage-duration percentage, equal split, or one tracing convention is a universal legal rule.

## Washington Authority Baseline

- **Dissolution distribution:** [RCW 26.09.080](https://app.leg.wa.gov/RCW/default.aspx?cite=26.09.080) calls for a just and equitable disposition of all property, community and separate, considering the nature/extent of each, relationship duration, and economic circumstances at the time of division. It does not prescribe equal division or a marriage-duration percentage.
- **Characterization:** [RCW 26.16.010](https://app.leg.wa.gov/RCW/default.aspx?cite=26.16.010) and [RCW 26.16.030](https://app.leg.wa.gov/RCW/default.aspx?cite=26.16.030) describe separate/community-property categories and presumptions. Relevant published opinions include [*Connell v. Francisco*, 127 Wn.2d 339 (1995)](https://www.lexisnexis.com/clients/wareports/), [*In re Marriage of Skarbek*, 100 Wn. App. 444 (2000)](https://www.lexisnexis.com/clients/wareports/), and [*In re Marriage of White*, 105 Wn. App. 545 (2001)](https://www.lexisnexis.com/clients/wareports/). Characterization, tracing, title, commingling, contributions, and appreciation require fact-specific review; no single accounting convention is silently treated as controlling law.
- **Committed intimate relationships:** *Connell v. Francisco* identifies nonexclusive factors including continuous cohabitation, duration, purpose, pooling of resources/services, and intent. [*In re Marriage of Pennington*, 142 Wn.2d 592 (2000)](https://www.lexisnexis.com/clients/wareports/) addresses equitable division of CIR property. A CIR is a distinct scenario assumption, not a finding based on dates alone.
- **Mediation and court documents:** [RCW 7.07.030](https://app.leg.wa.gov/RCW/default.aspx?cite=7.07.030), [RCW 7.07.040](https://app.leg.wa.gov/RCW/default.aspx?cite=7.07.040), and [RCW 7.07.070](https://app.leg.wa.gov/RCW/default.aspx?cite=7.07.070) address mediation privilege/confidentiality and exceptions; do not make a blanket confidentiality claim. [RCW 26.09.070](https://app.leg.wa.gov/RCW/default.aspx?cite=26.09.070) and [CR 2A](https://www.courts.wa.gov/court_rules/) address written agreements/consents and court treatment. The [Washington statewide dissolution forms](https://www.courts.wa.gov/forms/?fa=forms.contribute&formID=13) cover court documents, not a universal nonbinding mediation-offer form.
- **Source review:** These references are a product-design baseline, not a substitute for review by Washington family-law counsel. Before deployment, verify citations, amendments, controlling status, and each user-facing summary against the current official sources.

## 1. Evidence and Fact Provenance

- **FR-16-01 — Reviewed sources only:** Planning may use facts the case member explicitly entered or reviewed/adopted. Unreviewed extraction proposals are not facts.
- **FR-16-02 — Provenance:** Each source-backed fact retains its case-fact identity and, where available, source document ID/digest, page, exact quote, review status, and actor-entered/assumed status.
- **FR-16-03 — Conflict preservation:** Conflicting values remain separate alternatives. Do not select a winner, silently merge values, or replace a missing date with an inferred date.
- **FR-16-04 — Uncertainty display:** Mark facts as user-reported, source-supported, disputed, missing, or scenario-assumed. A classification or calculation must expose which inputs and assumptions produced it.
- **FR-16-05 — Washington authority:** The UI and AI must distinguish statutory factors, cited Washington decisions, case facts, and user assumptions. Do not fabricate citations or imply a model-generated factor is binding law.

## 2. Dated Source-of-Funds Ledger

- **FR-16-06 — Event history:** Model dated acquisitions, contributions/deposits, withdrawals, transfers, income, expenses, debt payments, and valuations per asset/account. Events are immutable once referenced by a scenario; corrections append a replacement/reversal and preserve the original.
- **FR-16-07 — Monetary precision:** Store and calculate dollar amounts in integer cents. Reject invalid dates, unsupported currencies, non-positive event magnitudes where a positive magnitude is required, and arithmetic overflow.
- **FR-16-08 — Source allocations:** Track separate, community, and unresolved source components independently. A contribution records an explicit source allocation and supporting fact or user-assumption provenance. Unknown source is never silently treated as community or separate.
- **FR-16-09 — Transfers:** A transfer links a source-account outflow to a destination-account inflow and carries the selected source components forward without creating value. Reject unbalanced, duplicate, or cross-case transfer links.
- **FR-16-10 — Withdrawals:** A withdrawal must identify source allocations or name a scenario-selected accounting convention. Keep pro-rata, separate-first, community-first, and unresolved treatment as distinct, clearly labeled calculations; none is silently presented as the legally correct method.
- **FR-16-11 — Valuation changes:** Revalue an asset at dated user-provided values. Allocate increases/decreases only under an explicitly identified calculation convention; if source balances or valuation inputs are insufficient, keep the affected amount unresolved.
- **FR-16-12 — Invariants:** Reject any event sequence that creates a negative source bucket, overdraws an account, duplicates value in a transfer, or produces a current total inconsistent with the user-provided valuation. Return field/event-specific validation errors.
- **FR-16-13 — Auditability:** Show the ordered events, amounts by source bucket, derived balances, valuation changes, unresolved amount, and provenance at each step. Calculations are deterministic and reproducible from the saved inputs.

## 3. Scenario Generation, Calculation, and Ranking

- **FR-16-14 — Scenario axes:** Allow explicit alternatives for CIR recognition and date window, marriage/separation dates, disputed source facts, and supported tracing assumptions. A scenario changes assumptions only; it never mutates source facts or the case profile.
- **FR-16-15 — Bounded set:** Generate a small, deduplicated set from material alternatives, capped at 12 scenarios per run. Do not construct an unbounded Cartesian product. Record which alternative each scenario tests and which alternatives were omitted by the cap.
- **FR-16-16 — Reproducible outcomes:** Calculate property/debt totals and proposed party allocations in deterministic server code from the scenario's ledger and explicit assumptions. Each output includes the inputs, formulas/method labels, currency, and unresolved amount.
- **FR-16-17 — No default division percentage:** Require a scenario's proposed division terms to be user-entered or explicitly scenario-assumed. Do not default Washington division to 50/50 or derive a percentage solely from marriage duration. Clearly distinguish a user's proposed settlement allocation from any court outcome.
- **FR-16-18 — User objective:** Let the user state their negotiation objective and priorities. Do not assume a party identity, treat maximum dollar recovery as the only objective, or silently optimize a legal/court outcome.
- **FR-16-19 — AI ranking only:** With separate, purpose-specific consent, AI may rank the bounded, server-calculated scenarios and explain trade-offs using the provided facts, user objective, and a curated Washington authority set. AI must not invent facts, scenario amounts, legal rules, or citations. It may return only IDs from the supplied candidates.
- **FR-16-20 — Honest ranking:** Return up to three highlighted scenarios and allow inspection of all generated scenarios. Explain source support, contrary facts, key assumptions, and what would change the ranking. Do not report court-success, counteroffer, or acceptance probabilities unless validated empirical data and a separately reviewed specification support them.
- **FR-16-21 — Failure behavior:** If the AI response is invalid, cites an unknown authority, references an absent scenario, or cannot explain a source-supported ranking, return a visible error and preserve the calculated scenario list. Do not invent a successful fallback or silently claim the scenarios were AI-ranked.
- **FR-16-22 — Non-advice notice:** Label ranked scenarios as decision-support, not legal advice or an outcome prediction. Encourage review with qualified Washington counsel/mediator before relying on or sharing them.

## 4. Consent, Case Security, and Retention

- **FR-16-23 — Separate informed consent:** Scenario ranking and drafting are separate AI purposes from fact extraction. Before any provider call, disclose provider/model, region, exact data categories sent, purpose, and configured handling notice; require affirmative consent for that run.
- **FR-16-24 — Data minimization:** Send only the reviewed facts and scenario inputs needed for the requested ranking or selected-draft text. Do not send account credentials, unrelated documents, full case history, or source documents by default.
- **FR-16-25 — Authorization:** All real-case operations require active case membership; only non-viewer members can create or change a ledger, run scenarios, select a scenario, or create a draft. Do not expose real-case data to the unauthenticated demo.
- **FR-16-26 — Audit and retention:** Store the consent snapshot (provider, model, region, purpose, data categories, handling notice), actor, scenario input/result snapshot, AI response, selected scenario, and timestamps with the case. Return generated DOCX bytes with `no-store`; do not retain the shareable draft server-side by default. Never log document text, quotes, or generated legal narratives.

## 5. Mediation Offer Draft

- **FR-16-27 — User selection:** Drafting is available only after the user selects a scenario. It does not silently choose, accept, adopt, or transmit an offer.
- **FR-16-28 — Editable draft:** Produce an editable DOCX with parties, proposed terms, asset/debt schedules, user-editable effective/response dates, and a clear “nonbinding draft—review before sharing” notice. Do not claim that a universal or court-mandated offer form exists.
- **FR-16-29 — Separate private notes:** Keep provenance, disputed facts, ledger event details, and internal AI reasoning outside the shareable offer body by default. Keep scenario-run evidence and traces in the authorized case record; the downloadable offer contains only the selected calculation summary, assumptions, and user-entered terms.
- **FR-16-30 — No filing or delivery:** Never file with a court, email, serve, or otherwise transmit the draft. Require an explicit user download/export action.

## 6. Accessibility and Compatibility

- **FR-16-31 — Review UI:** Provide an accessible event ledger, source-status cues, scenario comparison table, top-three highlight, complete scenario list, and a selected-scenario offer-draft action. Support keyboard use, responsive layouts, and announced async/error states.
- **FR-16-32 — Existing records:** Cases without new ledger/scenario state remain readable and unchanged. Preserve existing profile facts, inventory, and negotiation events.
- **FR-16-33 — Fictional demo:** The public `/demo` may display a fixed sample scenario comparison without sign-in, but it must be visibly fictional, unranked, and disconnected from case data, persistence, and AI processing. Enumerate every combination in the stated sample assumption set and show `Start Date` separately from `End Date (Division Date)`; do not imply the demo's date assumptions are legal rules or that relationship-characterization and division dates are always the same.

## 7. Acceptance Criteria

1. A user can trace contributions, withdrawals, transfers, mixed funds, and value changes across dated events, with separate/community/unresolved buckets and source provenance.
2. Invalid, unbalanced, unsupported, or ambiguous events fail explicitly; unresolved values are visible and never silently reclassified.
3. Different CIR/date, source, and tracing assumptions create reproducible, bounded, side-by-side scenarios without mutating case facts.
4. No default equal split or marriage-duration percentage is applied; every proposed allocation is tied to an explicit assumption.
5. After separate consent, AI ranks only server-calculated scenario IDs, cites only supplied authorities/evidence, explains trade-offs, and highlights up to three; all scenarios remain inspectable.
6. Missing evidence, unsupported AI output, or provider failure is visible and never converted into a fabricated scenario or a success-shaped response.
7. A user-selected scenario produces an editable, nonbinding DOCX offer draft; private source notes are separate; no automatic sending or filing occurs.
8. All operations enforce case membership and role authorization; extraction-only consent cannot authorize settlement planning.
9. Automated tests cover arithmetic invariants, provenance/conflicts, CIR alternatives, bounded scenario generation, AI output validation, consent, authorization, docx rendering, and failure cases.
