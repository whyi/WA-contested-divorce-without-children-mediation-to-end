# Spec 82: Restore the Real-Account Proposal Workflow

- **Status:** Specified; implementation and regression tests in the same pull request
- **Related issue:** [#328 — Restore the real-account proposal workflow for the MVP](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/328)
- **Amends:** Spec 76 by restoring an authenticated, real-case proposal workspace. Spec 76's removal requirements are superseded only for this workspace; its requirements to preserve case data, account controls, demo boundaries, and completion behavior remain.
- **Aligns with:** Spec 79's owner-only MVP baseline and the existing server-side attempt, authorization, consent, and finalization contracts.

## Requirements

1. Provide an explicit, authenticated entry from the user's saved case preparation view into that case's server-backed proposal workspace. Opening or refreshing a case must not silently create an attempt or replace the saved preparation path.
2. Keep the workspace bound to the signed-in user's owned case and saved attempts. Signed-out users cannot read or change it, and fictional demo state is never used for a real case.
3. Allow the user to review and edit both parties' offer values, calculate and select scenarios, generate mediator-facing drafts, and finalize a proposal attempt.
4. Preserve explicit AI consent boundaries, CSRF and revision checks, attempt-credit rules, retryable draft failures, and immutable snapshots after successful finalization.
5. Delivery remains user-managed: the application does not send proposal documents to either party or mediator and does not verify delivery or receipt. Any recorded delivery or response is explicitly user-reported.
6. Preserve fictional demo flows and existing case export, closure/reopen, deletion, and data-retention behavior.

## Acceptance Criteria

- Browser tests cover the signed-in case path, explicit workspace entry, edits, scenario/draft/finalization actions, and demo isolation.
- Authorization and persistence tests cover access to the selected case and attempt lifecycle.
- Tests confirm no native browser dialogs, automatic document delivery, or app-verified receipt.
- Existing specifications remain unchanged; this specification supersedes only the removal decision in Spec 76.
