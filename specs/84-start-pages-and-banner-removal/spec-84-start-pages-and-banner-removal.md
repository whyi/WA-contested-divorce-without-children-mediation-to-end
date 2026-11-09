# Spec 84: Start landing pages and removal of floating attempt banners

## Amendments

This additive specification amends specs 77, 80, 81, 82, and 83. Historical
specifications remain unchanged. The shared demo-based case layouts and optional
offer editor remain in use.

## Starting-point landing pages

- Replace the new-case and existing-case start-choice dialogs with normal page
  sections. Preserve the existing documents/guided choices and explanatory copy,
  with the heading **Choose your starting point** for real cases.
- A signed-in account without a case lands directly on the new-case starting-point
  page. Choosing a mode creates one case and opens that workflow. No Cancel button,
  modal backdrop, or second confirmation is present.
- The real documents page's **Back** button opens the existing case's starting-point
  page. Refresh preserves this destination. Selecting documents or guided mode
  opens the existing case, never creates a duplicate, and preserves saved work.
- Preserve disabled pending choices, explicit retryable errors, and saved case
  identity when creation has succeeded but navigation has not completed.
- Demo start choices also use a normal page section without Cancel or a backdrop.
  Existing demo case persistence and plan-specific attempts remain intact.

## Document offer placement

- Place the offer/counteroffer checkbox beneath the document selection and selected
  file list, before the Back/Next actions, not beneath the page heading.
- Its text/file editor and save controls remain visible only when checked.
  Preserve existing save, reload, confirmation, and failure recovery behavior.

## Attempt presentation

- Delete the floating attempt banners from real and demo markup, associated script
  references, fixed-position styles, and body-padding offsets. Do not hide them or
  retain unused banner placeholders.
- Preserve the non-floating ordinal attempt navigation and its current/read-only
  states.
- Remove the additional **Snapshot date** input from the real Asset Overview.
  Current attempt editing continues without requiring another date field. Existing
  dated balances and milestones remain stored; saved timeline selection supplies
  the existing entry date, or the current UTC date identifies the first entry.
  This date is an entry date, not evidence that an attempt was completed.
- Historical/finalized attempt views remain read-only and use only their captured
  profile. Removing the date input does not unfreeze completed attempts.

## Acceptance

- Verify initial signed-in start pages and Back destination as non-modal sections,
  with no Cancel, and refresh/selection without duplicate creation or deletion.
- Verify the lower checkbox position, checked-only text/file editor, current
  balance editing without a date input, and historical read-only behavior.
- Verify neither real nor Demo 1/Demo 2 has a floating banner or body-padding offset
  at desktop, tablet, and mobile widths.
