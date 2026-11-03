# Spec 15: Property Acquisition Tracing

- **Status:** Implemented
- **Related issue:** [#61 — Implement Milestone Date Tracking and Property Acquisition Metadata for Asset Division](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/61)
- **Related specifications:** [Spec 11: Relationship Milestone Timeline](../11-relationship-milestone-timeline/spec-11-relationship-milestone-timeline.md) and [Spec 13: Editable Asset Comparison](../13-editable-asset-comparison/spec-13-editable-asset-comparison.md)
- **Objective:** Capture the relationship timeline and asset-acquisition facts in authorized case state, and provide transparent, non-legal candidate classifications for review.
- **Scope:** Four optional case milestone dates; acquisition date, acquisition method, and title status for each asset; protected case APIs and JSONB persistence; deterministic classification candidates and unit tests; corresponding fields in the browser-only intake preview. This does not classify debts, calculate appreciation, determine legal ownership, or make a legal conclusion.

## 1. Case Milestones

- **FR-15-01 — Standard dates:** Support optional cohabitation/CIR start, marriage, separation, and divorce petition filing dates.
- **FR-15-02 — Calendar validation:** Accept valid ISO calendar dates only. Blank or omitted milestone values mean unknown; do not infer dates or impose a fixed ordering.
- **FR-15-03 — Case persistence:** Store milestone dates as structured case state. Reads and writes use the existing authenticated case-membership gate; the public and fictional demo flows must not send case facts to the API.

## 2. Asset Acquisition Facts

- **FR-15-04 — Required facts:** Each property asset records a non-empty name, acquisition date, acquisition method (`purchase`, `inheritance`, `gift`, `pre_existing`, or `other`), and title status (`joint` or `individual`).
- **FR-15-05 — Validation:** Reject malformed dates, unsupported methods or title statuses, blank names, and requests exceeding the documented item limit. Do not silently coerce invalid input.
- **FR-15-06 — Persistence:** Store validated assets as structured case state, separate from the legacy asset/liability inventory. Do not persist derived classifications as source facts.
- **FR-15-07 — Intake preview:** The local wizard exposes acquisition method and joint/individual title inputs in addition to its existing acquisition-date control. It continues to save only in browser storage and must not call case APIs.

## 3. Classification Candidates

- **FR-15-08 — Separate-property candidate:** Mark an asset as a separate-property candidate when its method is inheritance, gift, or pre-existing, or its acquisition date is before the earliest known cohabitation/CIR or marriage date.
- **FR-15-09 — Community-property candidate:** Mark a joint-titled purchase as a community-property candidate only when both the relationship start and separation dates are known and the acquisition date falls inclusively in that window.
- **FR-15-10 — Post-separation candidate:** Mark an asset acquired after a known separation date as a post-separation candidate.
- **FR-15-11 — Review required:** Use `needs_review` when the dates do not establish the relevant window or the facts do not fit the candidate rules, including an individually titled purchase during the relationship window.
- **FR-15-12 — No legal determination:** Every candidate is only an organizational aid. Title, acquisition method, and dates do not by themselves establish legal classification or entitlement. The API and UI must retain the user's reported facts and make no valuation, appreciation, or division calculation.
- **FR-15-13 — Recalculation:** Derive classifications from current stored facts and milestones when responding; do not store a stale classification that survives edits to the facts or dates.

## 4. Protected API and Compatibility

- **FR-15-14 — Case API:** Support case creation with optional milestone/asset state and provide authenticated `GET` and replacement `PUT` operations at `/cases/{case_id}/property-tracing`.
- **FR-15-15 — Authorization:** Use the existing case-membership middleware and return the repository-standard not-found behavior for cases the caller cannot access. Do not introduce a public endpoint for real case facts.
- **FR-15-16 — Backward compatibility:** Existing case records and clients that omit the new data continue to work with empty milestone and asset collections. Preserve the existing `asset_liability_inventory` contract.
- **FR-15-17 — Atomic update:** Validate the complete replacement payload before writing. Persist milestones and asset facts in one database transaction.

## 5. Acceptance Criteria

1. All four milestone dates accept valid dates and reject malformed dates; omitted dates remain unknown.
2. Authorized case data can create, read, and replace milestones and acquisition facts; persistence uses dedicated structured case fields.
3. An asset requires a name, valid acquisition date, supported method, and joint/individual title status.
4. The classifier returns separate, community, post-separation, or review-required candidates according to FR-15-08 through FR-15-11.
5. Candidate classifications are derived on read and are clearly not legal conclusions.
6. Existing case JSON inventory and clients without the new fields remain compatible.
7. The intake preview visibly collects acquisition method and title status, while remaining browser-only and making no API request.
8. Unit tests cover valid and invalid dates, every classification path, and persisted case API behavior.
