# Spec 102: Rejected-offer continuation at the attempt limit

This additive specification amends the rejection continuation controls in
[spec 93](../93-real-mediator-response-workflow/spec-93-real-mediator-response-workflow.md)
and applies the existing
[spec 94](../94-counteroffer-next-upgrade/spec-94-counteroffer-next-upgrade.md)
credit-notice interaction to rejected offers. Existing specifications remain
unchanged.

## Requirements

- In an active real case with `Offer rejected`, keep `Prepare another attempt`
  activatable when the server-provided attempt limit has been reached.
- At exhaustion, use the same disabled styling and `aria-disabled="true"` as
  counteroffer Next. Mouse and keyboard activation open the same branded
  `More attempts need credits` notice through the existing shared continuation
  handler. Do not save a response, create an attempt, consume credits, or navigate.
- With quota remaining, retain the existing response-save and next-attempt
  navigation behavior. Do not show the credit notice.
- Actually disable the control while busy and for historical, stopped, closed,
  or finalized cases. Preserve stop-workflow confirmation and server enforcement.
- Preserve fictional-demo behavior. Do not use browser-native alert/confirm.

## Regression coverage

Chromium entry tests cover Free and paid exhaustion with mouse and keyboard,
no mutation/navigation, reload, paid continuation with quota remaining, and
inactive/historical controls. Existing rejection completion coverage remains.
