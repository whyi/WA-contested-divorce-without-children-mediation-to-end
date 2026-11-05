# Spec 33: Existing Opposing Offer Intake

- **Status:** Implemented
- **Related issue:** [#120 — Capture an existing opposing offer during case intake](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/120)
- **Related specifications:** [Spec 05: Case Materials Import](../05-case-materials-import/spec-05-case-materials-import.md), [Spec 21: Settlement Offer Response and Finalization](../21-settlement-offer-response-and-finalization/spec-21-settlement-offer-response-and-finalization.md), [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 24: Counteroffer Attempt Inheritance](../24-counteroffer-attempt-inheritance/spec-24-counteroffer-attempt-inheritance.md), [Spec 26: Wizard Intake Sections](../26-wizard-intake-sections/spec-26-wizard-intake-sections.md), [Spec 27: Modified Offer Review](../27-modified-offer-review/spec-27-modified-offer-review.md)
- **Superseded historical requirements:** None. This spec is additive; historical specs are unchanged. It amends earlier specs only by adding an intake answer and by allowing attempt 1 of an existing-offer case to be an initial incoming offer rather than a user-authored proposal (FR-33-06).
- **Objective:** Let a case that begins with an offer already made by the opposing party record that offer at intake, in both document-first and wizard-first setup, and reuse the existing comparison workflow without inventing a prior user proposal.
- **Scope:** Case setup, the authenticated case API, and the settlement offer-response read model. Offer parsing, AI analysis, attempt limits, export, and freeze rules are unchanged.

## Functional requirements

- **FR-33-01 — Intake question:** Case setup in both the document-first (`upload`) and wizard (`wizard`) paths asks whether the opposing party has already made an offer. Legacy cases without an answer remain supported and show the question on their preparation page.
- **FR-33-02 — Offer source rule:** If the answer is yes, at least one source is required: an uploaded offer document belonging to the case, or non-empty free-text notes. Both may be supplied; either alone is accepted. Whitespace-only notes are empty. If the answer is no, notes and documents must be absent.
- **FR-33-03 — Server enforcement:** The rule in FR-33-02 is enforced by the API at every persistence boundary: `POST /cases` (`existing_offer`) and `PUT /cases/{case_id}/existing-offer`. Client-side validation is only a convenience. Because no document can exist before the case does, `POST /cases` with "yes" requires notes; a document-only offer is saved with the PUT after the document is imported. Clients cannot write the reserved `existing_offer` key through free-form `metadata`.
- **FR-33-04 — Free-form notes:** Notes are stored verbatim (trimmed of surrounding whitespace, maximum 20,000 characters). They may be conversational or shorthand; no asset table is required before an asset inventory exists.
- **FR-33-05 — Asset mapping:** When the case has an asset inventory (`property_assets`), `PUT /cases/{case_id}/existing-offer/asset-terms` relates a term note to individual assets, identified by inventory position and verified by asset name. It is rejected with 409 when there is no offer, no inventory, or an asset reference is stale. Mapping never alters the stored notes or document references.
- **FR-33-06 — Offer origin:** The offer-response read model exposes `offer_origin`: `initial_incoming_offer` for attempt 1 of a case whose attempt snapshot recorded an existing offer; `counteroffer_response` for any attempt after attempt 1; otherwise `initial_user_proposal`. The origin is derived; no prior user proposal, attempt, or proposal version is created for an incoming offer. The comparison UI is shared across origins and labels the origin.
- **FR-33-07 — Authorization and security:** Reads and writes use the existing authenticated case-membership checks; viewers cannot write; finalized cases are read-only; documents must belong to the same case; offer data is returned with `Cache-Control: no-store`. The yes/no answer cannot change once a negotiation attempt exists. Writes lock the case row, are idempotent, and database failures return a retryable 503 without partial state.
- **FR-33-08 — Accessible UI:** The question is a labelled fieldset with radio buttons; conditional notes use a labelled textarea; validation and save status messages are announced through live regions; controls are keyboard operable and use theme tokens.

## Acceptance criteria

1. "Offer exists" with neither a document nor notes cannot be saved through the API or proceed in either setup UI; file-only, notes-only, and both are accepted.
2. Notes remain free-form, are preserved when asset terms are mapped, and can be mapped to assets after inventory creation.
3. `offer_origin` distinguishes an initial incoming offer, a user's first proposal, and a counteroffer response, and the same comparison UI is reused.
4. Unauthorized, viewer, cross-case-document, and stale-asset requests are rejected; free-form metadata cannot bypass the rule.

## Implementation status

- Implemented in `src/app/existing_offer.py` (validation, endpoints, origin derivation), `POST /cases` in `src/app/main.py`, the offer-response read model, and the case-setup/preparation UI in `src/app/static/index.html`. No schema migration is required; the intake is stored under `metadata_json["existing_offer"]`.
- Tests: `tests/test_existing_offer.py`.
- Limitations: offer documents are attached by selecting already-imported case documents (the import pipeline stores no original filename, so they are listed by type, size, and date). Offer terms are not parsed or analyzed automatically. The wizard remains a preview-only screen, so the real wizard-first path is the case-creation dialog plus the shared preparation page.
