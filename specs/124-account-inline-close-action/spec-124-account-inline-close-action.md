# Spec 124: Inline Active Case Closure on Account

- **Issue:** [#382](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/382)
- **Amends:** Spec 119's active-card action layout and retained management
  disclosure. Historical specifications remain unchanged.

## Requirements

1. Use the existing Closed case card/list/action styling for Active case.
   Render **Export data**, **Close case**, and the existing verified destination
   button together in that order. Close case is adjacent to Export data without
   opening a disclosure, at desktop and mobile widths.
2. Remove the **Manage case** disclosure and **Permanently delete case** button
   from Account's active case UI, along with their unused case-deletion handler.
   Account and material deletion controls and backend deletion APIs are unchanged.
3. Close the card's explicit case ID using the existing authenticated reversible
   closure endpoint and confirmation. Cancellation makes no mutation. Prevent
   duplicate submissions and announce errors in the active card's live status;
   failed closure stays active and retryable.
4. Successful closure refreshes Account to the existing Closed case card.
   Retain materials, attempts, purchased credits and existing locks. Do not
   introduce permanent deletion or accepted-completion lock changes.
5. Preserve export and latest-attempt/accepted-page destination validation.

## Verification

- Desktop/mobile tests assert action order, shared styling, immediate visible
  closure, removed disclosure/deletion controls and no horizontal overflow.
- Test export, confirmation, cancellation, failure/retry and successful closure
  with retained export/reopen controls; assert the exact close endpoint/body.
- Check actual authenticated HTTPS 8002 layout without closing the real case.
