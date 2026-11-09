# Spec 112: Response-only changes on the latest reopened accepted attempt

Tracking issue: [#352](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/352).

## Amendment

Amends Specs [100](../100-accepted-case-close-freezes-attempts/spec-100-accepted-case-close-freezes-attempts.md),
[107](../107-accepted-closure-lifecycle/spec-107-accepted-closure-lifecycle.md)
and [110](../110-completion-lifecycle-actions/spec-110-completion-lifecycle-actions.md)
only for the latest reopened attempt's response outcome and Next action.
Historical specifications remain unchanged.

## Requirements

- On the latest attempt after reopening an accepted case, keep proposal values,
  dates, sent documents, attachments, counteroffer notes, frozen snapshots and
  attempt creation permanently read-only.
- Enable only the response-outcome radio group and its visible Next button.
  Persist outcome changes with revision checks and preserve them across reloads.
  Closed cases and historical attempts remain fully read-only.
- The server permits only an outcome-only update on the latest sent, completed,
  permanently locked attempt in an actually open case. Preserve owner checks,
  CSRF, revision conflicts, scope/deletion checks and explicit errors. Reject
  attempts to bundle notes, attachments, proposal selection or other fields.
- With Accepted selected, Next navigates to verified accepted completion without
  subscription gating or an unnecessary mutation.
- With any other response selected, Next shows a Subscription required dialog
  and blocks progression for every plan, including paid accounts. Do not start
  checkout, consume credit or create another attempt.
- Keep alternate continue/stop buttons unavailable in this reopened response-only
  mode. Retain the removed Offer Accepted timeline circle after reopening.
- While saving, disable response controls and Next. On failure preserve the
  persisted selection, announce the error and permit retry.
- Ordinary open attempts, closed review and fictional demos retain their existing
  workflows. This amendment does not unlock editing of historical proposal data.

## Validation

- Exercise accept/close/reopen, change outcome, reload and return to accepted;
  assert retained snapshot, materials, notes and lock timestamp.
- Reject closed/historical/stale/unsent and extra-field outcome-only requests.
- Test Free and paid response persistence, accepted completion navigation and
  nonaccepted subscription dialogs without continuation, credit use or checkout.
- Verify unrelated attempt controls remain disabled, saving/failure behavior,
  historical/closed state and existing lifecycle regressions.
