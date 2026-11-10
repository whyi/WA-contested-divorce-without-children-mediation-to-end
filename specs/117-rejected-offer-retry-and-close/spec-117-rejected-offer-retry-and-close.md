# Spec 117: Final Rejected Offer Retry and Case Closure

- **Issue:** [#372](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/372)
- **Amends:** Specs 113 and 114 for the latest authenticated rejected-offer
  actions only. Existing specifications remain unchanged.
- **Scope:** The latest/current attempt, including a reopened case and cases
  with remaining credits. Historical attempts remain read-only. Fictional
  demos and accepted/counteroffer actions remain unchanged.

## Requirements

1. Selecting and successfully saving **Offer rejected** hides the generic
   **Next** button. Show **Try another attempt** and **Close Case** side by
   side, including at a 320px viewport, without horizontal overflow.
2. Try another attempt uses the existing continuation flow. Available credits
   allow a new attempt; exhausted plans show the existing credit notice;
   reopened locked cases show the existing subscription notice without creating
   an attempt or removing prior locks. The notice-opening action remains
   keyboard-accessible and is not falsely marked aria-disabled.
3. Close Case asks for confirmation explaining retained materials/unused
   credits, reopening, and that product closure does not change legal status.
   Cancel performs no mutation. Confirm uses the existing owner-authorized,
   CSRF-protected `POST /cases/{case_id}/close` with reason `stopped`.
4. This is reversible product closure, not acceptance, permanent deletion,
   or the mediation `stop` action. It creates no permanent accepted-attempt
   lock. Any pre-existing locks survive closure/reopening. Spec 100's
   accepted-case closure behavior is not changed.
5. Disable actions while saving the selected outcome or closing. On confirmed
   server closure (`closed_at` for the expected case ID), return to Account, where
   Closed cases provides review/reopen/export. On errors or an unverified
   response, announce the error, keep the page usable, and never navigate as
   though closure succeeded.
6. Closed/finalized, stopped and historical attempts cannot trigger either
   action. Switching to accepted/counteroffer hides the rejected-offer actions
   and preserves their existing continuation behavior.

## Regression coverage

- Desktop/mobile, ordinary/reopened, remaining/exhausted credits, reload,
  outcome-save failure/in-flight save, and keyboard notice activation.
- Closure cancellation, pending mutation, server failure, unverified response,
  successful Account navigation, exact closure payload and absence of
  mediation-stop/complete mutations.
- Historical/closed/stopped locks and unchanged accepted/counteroffer actions.
