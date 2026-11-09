# Spec 94: Visible counteroffer Next and one plan-limit notice

This additive specification amends spec 93. Prior specifications remain unchanged.

- Show the counteroffer panel's bottom **Next** button even when the real case
  has reached its plan's attempt limit.
- At the plan limit, use disabled styling and `aria-disabled="true"` while
  retaining click and keyboard activation solely for an upgrade/credit-purchase
  alert. Do not submit a continuation, create an attempt or navigate.
- Truly disable the button while saving or viewing an inactive/historical case.
  Eligible paid cases retain normal continuation behavior and styling.
- Display the counteroffer plan-limit explanation once, not both in the limit
  paragraph and response status. Errors remain visible in the response status.
- Preserve counteroffer notes/files and restore the same button state on reload.
  Server-side attempt-limit enforcement remains unchanged.
