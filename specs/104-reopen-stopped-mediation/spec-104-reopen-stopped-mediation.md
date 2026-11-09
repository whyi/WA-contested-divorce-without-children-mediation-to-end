# Spec 104: Resume stopped mediation when reopening a case

This additive specification amends the reversible stopped closure behavior in
[Spec 93](../93-real-mediator-response-workflow/spec-93-real-mediator-response-workflow.md).
Existing specifications remain unchanged.

- Reopening a case clears the current attempt's mediation `stopped` flag in the
  same transaction and increments its response revision to reject stale writes.
- Preserve historical attempt states, frozen proposal snapshots, response data,
  attachments, completion records, and unused credits. Do not create an attempt
  or increase the plan's attempt limit.
- With quota exhausted, an active reopened rejection uses the existing credit
  notice; with quota remaining, normal continuation remains available.
- Closed and intentionally stopped cases remain inactive until explicitly reopened.
- Regression tests cover resuming the latest stopped response without modifying
  historical responses and preserving nonstopped mediation data.
