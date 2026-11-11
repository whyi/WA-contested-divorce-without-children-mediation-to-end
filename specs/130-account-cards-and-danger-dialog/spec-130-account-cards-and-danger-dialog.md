# Spec 130: Account Cards and Permanent Deletion Dialog

- **Issue:** [#402](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/402)
- **Amends:** Specs 124 and 129 for Account presentation and Spec 44 for
  placement of the existing account-deletion controls only. Retain all
  backend deletion safeguards and historical specifications.

## Requirements

1. Use matching neutral cards for Account information, Your plan, Your case,
   and Permanently delete data. Remove the divider immediately under Account
   information. Keep the plan card separate and preserve its Upgrade action.
2. Label active and closed case sections Your case. Do not display case titles,
   including in action accessible names. Keep status and existing case actions
   together in a row, wrapping only when necessary on narrow screens.
3. Give the permanent-deletion heading a prominent, theme-accessible red color.
   The card contains only its heading and a red Delete my account button.
4. Open an accessible modal with the existing password, optional MFA/recovery
   code, and exact confirmation phrase fields. Explain irreversible deletion
   and existing backup limitations inside the modal.
5. Provide Permanently Delete and Cancel buttons. Use the same red treatment
   for both destructive buttons. Do not stack another confirmation modal.
6. Preserve the authenticated, CSRF-protected deletion endpoint and payload.
   Validate inputs, prevent duplicate submissions, and keep the modal open
   with an explicit error on failure. Disable cancellation during processing.
   Cancel/Escape otherwise clear secrets and restore focus to the opener.
7. Success closes the modal and returns to the existing signed-out flow.

## Verification

- Verify neutral card backgrounds, no first-row divider, removed case titles,
  red actions, mobile layout, modal focus, Cancel, and Escape.
- Test missing/incorrect confirmation, exact deletion payload, pending request
  controls, failure/retry, and success with synthetic data only.
- Preserve case export, close, reopen, and destination validation regressions.
