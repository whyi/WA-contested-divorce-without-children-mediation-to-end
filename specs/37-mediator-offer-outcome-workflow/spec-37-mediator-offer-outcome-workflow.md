# Spec 37: Mediator-Only Offer Outcome Workflow and Counteroffer Recording

- **Status:** Implemented; focused tests passing; full suite has one known pre-existing failure (`test_main.MainWorkflowTests.test_theme_selection_persistence_and_shared_page_coverage`, hard-coded `#17241f` colors already on `origin/main`)
- **Related issue:** [#123 — Specify mediator-only iterative offer and outcome workflow](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/123)
- **Related specifications:** [Spec 21](../21-settlement-offer-response-and-finalization/spec-21-settlement-offer-response-and-finalization.md), [Spec 22](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 23](../23-explicit-sent-confirmation-freeze/spec-23-explicit-sent-confirmation-freeze.md), [Spec 24](../24-counteroffer-attempt-inheritance/spec-24-counteroffer-attempt-inheritance.md), [Spec 25](../25-accepted-offer-completion-page/), [Spec 27](../27-modified-offer-review/spec-27-modified-offer-review.md), [Spec 28](../28-negotiation-attempt-limits/spec-28-negotiation-attempt-limits.md), [Spec 29](../29-document-credit-consent/spec-29-document-credit-consent.md), [Spec 32](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), [Spec 33](../33-existing-offer-intake/spec-33-existing-offer-intake.md), [Spec 34](../34-party-owned-case-delegation/spec-34-party-owned-case-delegation.md), [Spec 35](../35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md), [Spec 36](../36-attempt-credit-packages/spec-36-attempt-credit-packages.md)
- **Superseded historical requirements:** No historical spec is edited. This spec supersedes only:
  - Spec 21/24 requirement that a `counteroffer` outcome may continue only when a counteroffer **document** is attached: it now also continues when the user has recorded counteroffer values (FR-37-03). A document is no longer mandatory.
  - Spec 28 rejection wording that offers only "Next": rejection now presents an explicit choice between another attempt and stopping (FR-37-06).
  - Spec 23's confirmation label wording is unchanged in behavior; FR-37-01 only adds an explicit, machine-readable statement of what that confirmation does not prove.
- **Objective:** Complete the user-side loop "prepare → download → hand to mediator → record what the mediator reports → choose next step" without implying the app delivered anything or verified any response.
- **Scope:** The remaining #123 behavior only. Already implemented elsewhere and **not** changed: mediator-only proposal copy and no outbound transmission; download metadata `externally_sent:false` (Spec 35); user-confirmed "I reviewed and sent" (Spec 23); freezing, outcome recording, snapshot immutability and credit consumption at finalization (Specs 23, 35, 36); new attempt only on the user's explicit Next, carrying the prior editable state (Spec 24/28); acceptance completion, close and reopen (Specs 25, 32); case ownership/delegation (Spec 34).

## Requirements

- **FR-37-01 — Mediator-only, unverified boundary:** The response read model includes `delivery` = `{recipient: "mediator", sent_to_opposing_party: false, delivery_verified_by_app: false, response_verified_by_app: false, basis: "user_reported"}`. No route transmits a proposal to anyone; downloads keep `externally_sent:false`. The UI states that the user delivers to the mediator and that recorded delivery/response is the user's own report.
- **FR-37-02 — Manual (verbal) counteroffer:** After outcome `counteroffer`, `PUT …/offer-response/counteroffer-values` stores, on the attempt's response record (`settlement_offer_responses.counteroffer_json`), `{source, values:[{asset_id, amount_cents}], note, recorded_at, verified_by_app:false}`. `asset_id` must exist in that attempt's snapshot ledger; duplicates are rejected; extra fields are rejected; values are bounded. No document is required. Values are the user's report of what the mediator relayed (`source: mediator_reported`).
- **FR-37-03 — Continue rule:** `POST …/continue` for a counteroffer requires either an attached counteroffer document or recorded counteroffer values. All other Spec 28 continue preconditions are unchanged.
- **FR-37-04 — Optional document analysis, never silent adoption:** `POST …/counteroffer-values/suggestions` reads the attached counteroffer and returns `{source:"document_analysis", adopted:false, suggestions, warnings}`. It writes nothing. Automatic extraction currently covers XLSX files that follow the product's own export layout; other files return a warning directing the user to manual entry. Document-derived values are persisted only through FR-37-02 with `source: "document_reviewed"` and an explicit `reviewed: true`; otherwise validation fails. No AI-generated number becomes a recorded counteroffer without that action.
- **FR-37-05 — Distinct, editable, auditable values:** The user's own proposal values (`editable_state_json.proposed_values`, frozen per Spec 35) and the counteroffer values are stored separately. Counteroffer values stay editable through the same endpoint until the user starts the next attempt; the endpoint requires the case write authorization, CSRF, the case lock and `expected_attempt_revision`. Once a next attempt exists the record is read-only, so the prior round is preserved. Frozen snapshots, `frozen_snapshot_json` and finalization snapshots are never rewritten. In the next attempt, `prior_attempt` (derived on read from the predecessor: ordinal, outcome, user's proposed values, counteroffer record) is shown alongside the new attempt's editable state, which remains fully editable and revision-controlled by Spec 22/24.
- **FR-37-06 — Rejection choice:** For outcome `rejected` the read model returns `outcome_choices: ["next_attempt","stop_case"]`. The user is never forced into another attempt. *Next attempt* uses the existing continue route. *Stop* is presented as guidance to close the case from the dashboard (existing Spec 32 close, which remains reopenable); a dedicated neutral stop page is **deferred to #131**.
- **FR-37-07 — Acceptance:** Unchanged: `accepted` continues to the Spec 25 completion experience, case close and reopen. No legal conclusion is stated.
- **FR-37-08 — Credit semantics:** Recording outcomes or counteroffer values, and creating the next attempt, consume no credit. Credits are consumed only at successful finalization (Specs 35/36).
- **FR-37-09 — No advice:** Copy is neutral and states no legal conclusion about any outcome.

## Acceptance criteria

1. Counteroffer values can be recorded without a document and mapped per snapshot asset; unknown assets, duplicates, extra fields and stale revisions are rejected; recording requires outcome `counteroffer` and is read-only after the next attempt exists.
2. A counteroffer with only recorded values may continue; one with neither document nor values may not.
3. Document analysis returns unadopted suggestions, writes nothing, and degrades to manual entry for unsupported files; document-derived values require explicit review.
4. The response read model exposes the mediator-only/unverified boundary, the counteroffer record, `prior_attempt`, and rejection choices.
5. Migration `0021_counteroffer_values` adds and removes the nullable `counteroffer_json` column.

## Migration status

`migrations/versions/0021_counteroffer_values.py` (down revision `0020_attempt_credit_packages`) adds nullable JSONB `settlement_offer_responses.counteroffer_json`. Existing rows are unaffected (NULL). Not run against a live database in this change; covered by a unit test of upgrade/downgrade operations.

## Known limitations and deferred items

- **#130 (comparison chart):** No side-by-side chart, toggled comparison or recalculation across both sides is built. This spec supplies the distinct stored data (`prior_attempt`, `counteroffer`) for it.
- **#131 (neutral stop page):** Only the explicit choice and placeholder guidance are provided.
- Automatic document analysis is deterministic (product XLSX layout), not model-based; DOCX/PDF analysis is deferred.
- Counteroffer amounts are the amount allocated to the user as reported; terms-level counteroffer text is not modeled.
- Tests are mock-based unit tests consistent with the repository; no live-database integration run.
