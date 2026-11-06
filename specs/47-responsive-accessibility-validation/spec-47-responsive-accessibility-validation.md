# Spec 47: Pre-launch Responsive and Accessibility Validation

- **Status:** Validation incomplete; product and deployment decisions remain open
- **Related issue:** [#136 — Validate mobile usability and accessibility across core workflows](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/136)
- **Related specifications:** [Spec 05: Case-Materials Selection and Import](../05-case-materials-import/spec-05-case-materials-import.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), [Spec 35: Attempt Finalization](../35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md), [Spec 39: Toggleable Offer Comparisons](../39-toggleable-offer-comparisons/spec-39-toggleable-offer-comparisons.md), [Spec 40: Rejection-Stop Completion](../40-rejection-stop-completion/spec-40-rejection-stop-completion.md), [Spec 42: Case Attachment Upload Limits](../42-case-attachment-upload-limits/spec-42-case-attachment-upload-limits.md), [Spec 45: Failure Messaging and Recovery](../45-failure-messaging-support-escalation/spec-45-failure-messaging-support-escalation.md), and [Spec 46: Document Processing Limits](../46-document-processing-limits/spec-46-document-processing-limits.md)
- **Historical specs:** Existing specifications are preserved; this specification adds validation scope and records unresolved decisions.
- **Objective:** Establish an evidence-based pre-launch validation process for responsive layouts, keyboard interactions, accessibility semantics, and recovery paths without asserting unapproved standards, browser support, assistive-technology coverage, or launch policy.

## Decisions and approval state

- **Browser/device matrix:** Not approved or specified. No browser support is implied by this specification.
- **Viewport sizes:** For the initial responsive test pass, exercise 320, 375, 768, and 1280 CSS pixels when a capable browser is available. These are requested test widths, not a supported-device promise or a minimum-width policy.
- **Accessibility target:** Proposed baseline only, pending product approval: WCAG 2.2 AA. No official WCAG conformance claim is made.
- **Assistive technology combinations:** Not selected or tested. Product/deployment owners must decide the combinations and manual coverage before declaring the matrix complete.
- **Release-blocking policy:** Not approved. Findings must be recorded with impact and reproducibility; no issue severity is implicitly a launch blocker.
- **Integrated browser availability:** The workspace's integrated browser could not connect to either the loopback preview or its LAN address. A temporary local headless Chromium run is recorded in the evidence report; this is one emulated browser only, not a supported-browser decision or manual AT result.

## Validation scope

Test these workflows in an agreed browser/device/assistive-technology matrix:

1. Materials selection, invalid-file feedback, selected-file review and removal, explicit import, progress, and partial errors; include the Spec 42 2 MiB per-file and attachment-quota messages.
2. Comparison chart controls, their text equivalent, the horizontally scrollable asset table, editable values, and preservation of historical values.
3. Proposal finalization confirmation, cancellation, successful confirmation, and failure/recovery messaging.
4. Rejection-stop confirmation and completion feedback, closed-case return paths, and actionable error states.

For each workflow, record viewport, browser/version, device or emulation details, test steps, expected and observed behavior, evidence, and any limitation. At the requested viewport widths, check for clipped content, unintended page-level horizontal overflow, inaccessible or obscured actions, and usable table/chart alternatives. Keep intentional horizontal scrolling inside the labeled comparison table distinct from page overflow.

## Evidence requirements

- Automated source/DOM checks, unit tests, and an automated accessibility scanner are separate evidence classes. Record exactly which were run and their limits.
- `tests/test_accessibility_markup.py` checks accessible names, resolvable ARIA references, unique IDs, fieldset legends, and image alt attributes in the static page markup. It does not evaluate rendered visibility, keyboard interaction, viewport overflow, contrast, screen-reader output, or WCAG conformance.
- Run an accessibility scanner only when it is already present in repository dependencies or available project tooling; do not add a scanner dependency solely for this validation.
- An automated scanner result is not an assistive-technology test and does not establish conformance.
- Manual keyboard checks must record focus order and visible focus for file select/remove, editing comparisons, finalize confirmation/cancellation, and error/recovery actions.
- Manual assistive-technology checks must name the actual AT/browser versions and tested workflows. Do not infer AT outcomes from DOM roles or automated results.
- Do not claim a browser/device is supported, a minimum viewport is approved, WCAG conformance is achieved, or a defect blocks release unless the responsible product decision is recorded.
- If authentication, provider credentials, storage, or backend access prevents a real-case flow, use fictional demo coverage where possible and identify exactly what could not be exercised. Demo results do not prove authenticated-flow behavior.

## Acceptance criteria

1. Product/deployment owners record the browser/device matrix, viewport policy, manual AT combinations, accessibility target, and release-blocking policy—or explicitly leave each unresolved.
2. Responsive observations at 320, 375, 768, and 1280 CSS pixels are recorded from an actual browser; no untested width is reported as passed.
3. Focused keyboard and assistive-technology checks record steps, observed behavior, and versions; automated checks remain separately identified.
4. Upload select/remove, comparison editing, finalize confirmation/cancellation, and error recovery each have workflow evidence, or an exact access limitation is documented.
5. Reproducible defects are corrected with regression tests; unapproved product decisions and untested requirements remain open rather than being represented as passed.
6. The evidence report is updated before launch review. This specification itself is not a launch approval or accessibility-conformance statement.

## Current validation record

See [Issue 136 validation evidence](../../docs/issue-136-prelaunch-validation-evidence.md). The current record includes static markup tests and limited headless Chromium measurements for fictional demo views. Approved browser/AT decisions, real-device coverage, full keyboard workflow checks, authenticated flows, and assistive-technology evidence remain incomplete. Keep issue #136 open.
