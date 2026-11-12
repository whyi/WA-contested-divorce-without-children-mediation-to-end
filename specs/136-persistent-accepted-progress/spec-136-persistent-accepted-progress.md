# Spec 136: Persistent Accepted Progress

- **Issue:** [#419](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/419)
- **Amends:** Specs 106 and 109. Supersedes Spec 112's requirement to remove
  the Offer Accepted circle after reopening.

## Requirements

- For an open case with a confirmed accepted offer, always show the green
  Offer Accepted progress circle after the saved attempts, including while
  reviewing any earlier or latest attempt, viewing case files, and reloading.
- Keep the accepted circle navigable to the verified completion page. Mark the
  viewed attempt as selected; on completion, select Offer Accepted instead.
- Apply this rule to both never-closed and reopened cases, including permanently
  locked attempts, and to both asset and selection-based accepted offers.
- Once the saved response is no longer accepted, remove the circle. Do not
  create acceptance from a lock, closure status, or navigation alone.
- Preserve closed-case review, response editing restrictions, and other existing
  lifecycle behavior.

## Verification

Exercise completion-to-attempt and return navigation for every saved attempt,
reload, responsive widths, both offer implementations and open/reopened states.
Check the actual green background, selected step, absence of mutations, and
removal after a response changes away from accepted.
