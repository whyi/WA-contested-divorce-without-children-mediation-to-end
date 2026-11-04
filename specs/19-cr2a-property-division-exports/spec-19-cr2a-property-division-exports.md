# Spec 19: CR 2A Proposal and Property-Division Exports

- **Status:** Implemented (live provider validation requires deployment credentials)
- **Related issue:** [#70 — Generate CR 2A proposals and property schedules from selected scenarios](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/70)
- **Related specification:** [Spec 16: Evidence-Traced Settlement Planning](../16-evidence-traced-settlement-planning/spec-16-evidence-traced-settlement-planning.md)
- **Objective:** Let an authorized case member turn a deliberately selected, current settlement scenario into editable DOCX and XLSX drafts, then explicitly download or deliver both files through a connected Google Drive, Dropbox, or configured email service.
- **Scope:** Real authorized, non-demo case workflows, scenario-based document generation, optional account linking, and user-confirmed external delivery. This specification does not define legal advice, execution, filing, or service.
- **Policy relationship:** This specification extends Spec 16. It supersedes FR-16-28 and FR-16-30 only to the extent they prohibit user-requested CR 2A-style draft generation and explicit, confirmed delivery to a user-selected destination. All other Spec 16 privacy, provenance, authorization, AI-consent, and no-automatic-delivery requirements remain in force. Existing specifications are not edited.

## 1. Document Generation

- **FR-19-01 — Explicit current selection:** Generate exports only for a scenario explicitly selected by the user from a current run. Revalidate case membership, write role, and scenario/profile/ledger revisions for every generation or delivery request. Reject stale scenarios.
- **FR-19-02 — Editable CR 2A DOCX:** Generate an editable DOCX proposal organized after the user-provided CR 2A Agreement example. Include user-entered parties, proposed terms, dates, selected-scenario summary, and unsigned signature areas where appropriate. Use the example as a layout reference only; never copy its populated personal information into code, fixtures, logs, or templates.
- **FR-19-03 — Honest legal status:** Clearly mark the output as an unsigned draft for review, not a court-filed or executed agreement. Do not promise legal sufficiency or label a signed CR 2A agreement categorically nonbinding. Advise review by qualified Washington counsel before signing or sharing.
- **FR-19-04 — Editable XLSX schedule:** Generate a separate workbook organized after the user-provided property-division workbook example. Include the selected scenario's asset/debt allocations, separate/community/unresolved categories, readable totals, and an assumptions sheet. Use formulas for workbook totals where suitable and preserve unresolved amounts as unresolved. Never include private AI reasoning or source-document excerpts by default.
- **FR-19-05 — Safe file handling:** Provide separate downloads with generic filenames. Return private case exports with `Cache-Control: no-store`; do not persist generated file contents on the server. Bound document sizes and validate all user-entered fields.
- **FR-19-06 — No fictional case exports:** Keep exports and delivery unavailable from the public fictional `/demo`; do not convert demo values into purported case agreements.

## 2. Connected Destinations

- **FR-19-07 — Google Drive:** Allow the authenticated user to connect and disconnect a Google account with OAuth state/CSRF protection and least-privilege `drive.file` scope. Upload both files privately to a user-selected or clearly displayed destination; do not create public share links.
- **FR-19-08 — Dropbox:** Allow the authenticated user to connect and disconnect a Dropbox account using OAuth state/PKCE and the minimum write scope needed to upload both files. Upload both files to the connected app folder; do not create shared links.
- **FR-19-09 — Email:** When SMTP is configured, allow the user to enter and confirm one recipient email address. Send both files as attachments from the configured application sender; disclose the sender and recipient before confirmation.
- **FR-19-10 — Credential handling:** Encrypt provider tokens at rest with the configured application encryption key. Do not return or log tokens, OAuth codes, document contents, or case details. Revoke provider grants on disconnect where supported; report revocation failure while removing local credentials.
- **FR-19-11 — Configured availability:** Report each destination's setup/connection status. If OAuth credentials or SMTP are missing, disable that delivery path with an explicit explanation while preserving DOCX/XLSX downloads.
- **FR-19-12 — Explicit per-delivery confirmation:** Before upload or email, display the exact provider/destination or recipient and both filenames. Require a deliberate confirmation for every delivery. Scenario selection, preview, generation, and download must never cause an upload, email, filing, or AI-provider call.
- **FR-19-13 — Delivery audit and failure:** Record only the case/user, channel, outcome, and minimal destination metadata required for audit; never store the exported files or sensitive content in audit data. Report provider errors and partial two-file uploads explicitly, without success-shaped fallback or automatic retry.
- **FR-19-14 — Separate from AI consent:** Provider linking and document delivery do not imply or reuse AI-analysis consent. No export content is sent to AI.

## 3. Accessibility and Compatibility

- **FR-19-15 — Review controls:** Keep all fields labeled, validate inline, expose connection/delivery state with accessible status messaging, and make confirmation and disconnect controls keyboard-operable.
- **FR-19-16 — Existing workflow:** Preserve current scenario calculation and selection behavior, case authorization, revision checks, and DOCX download. Add XLSX download and destinations without changing the public demo or storing draft files.
- **FR-19-17 — Responsive behavior:** Keep document and destination controls usable on narrow screens without horizontal page overflow.

## 4. Acceptance Criteria

1. A user-selected current case scenario produces separately downloadable, editable DOCX and XLSX files with no private source notes or AI reasoning.
2. The DOCX is clearly an unsigned CR 2A-style proposal draft and warns users to obtain Washington counsel review; it makes no unsupported claim about legal effect.
3. The workbook contains selected scenario allocations, formulas/totals, and visible unresolved amounts and assumptions.
4. Google Drive, Dropbox, and email require the relevant configured credentials, an authenticated account or SMTP sender, and an explicit per-delivery destination confirmation.
5. Delivery sends both files only after confirmation; no selection, preview, generation, or download sends files.
6. Stale selections, unauthorized users, invalid terms, missing configuration, and provider failures are reported without exposing case data or credentials.
7. Disconnect removes local tokens and attempts provider revocation. No actual provider integration is represented as available when unconfigured.
8. The public fictional demo remains isolated and cannot generate or deliver case documents.
