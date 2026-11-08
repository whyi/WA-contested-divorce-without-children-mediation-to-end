# Spec 70: Attempt-First Real-Case Workspace

- **Related issue:** [#256](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/256)
- **Amends:** Spec 65 FR-65-01 and Spec 66 FR-66-04 only in the presentation of their real-account attempt screen. Existing case-entry decisions and backend behavior remain unchanged. Historical specifications are preserved.

## Requirements

1. The real-account attempt workspace opens with the title **Negotiation attempts**, existing case controls, attempt progress, scenario selection and proposal work. Do not lead with "Evidence-grounded settlement planning", a technical revision report, or legacy ledger instructions.
2. Preserve legal disclosures and arithmetic caveats in an accessible, default-collapsed **Important review and delivery information** section. The existing proposal-specific disclosure remains available.
3. Put optional AI consent, adopted facts, and append-only ledger controls inside default-collapsed **Advanced evidence and ledger tools**. Preserve all controls, IDs, validation and API behavior. Do not auto-open these tools or force consent for local calculations.
4. Keep scenario calculation and selection accessible outside the legacy tools. Collapse its JSON assumption editor separately, keeping the Calculate and rank scenarios action and its results visible. An empty attempt gives explicit guidance to configure assumptions and calculate/select a scenario; an existing saved attempt continues to restore normally.
5. Replace loading/success revision counters with concise attempt-workspace messages. Error reporting remains explicit and visible. Do not remove backend data, fabricate an attempt or silently claim a scenario exists.
6. Preserve preparation navigation, case access, exports, deletion safeguards, saved proposal/attempt editing, download gates, finalization and response handling. Do not switch real cases to local fictional demo state.

## Acceptance

- The first rendered view shows attempt progress and scenario actions; disclosure and legacy tools are closed.
- Legacy controls and status errors remain functional and reachable by expanding their details.
- Scenario and proposal controls retain their existing IDs and handlers.
- Regression tests verify layout nesting, default collapse and startup messages; existing navigation/settlement tests and repository validation pass.

## Out of scope

Rebuilding the real-account screen to match the demo asset dashboard, introducing a new scenario editor, changing AI consent or calculations, creating a new attempt automatically, and modifying legal disclosure content.
