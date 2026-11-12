# Spec 141: Viewed Attempt Highlight

- **Issue:** [#429](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/429)
- **Amends:** Specs 88, 106, and 136. Preserve their historical requirements.

## Requirements

- While reviewing an open or reopened case, the green numbered attempt circle
  follows the viewed attempt, not the latest saved attempt. Its selected step
  and rendered background must agree. Other numbered attempts are not green.
- Apply this to navigation from Offer Accepted, switching between saved
  attempts, reloading, and opening case files. Keep the actual latest attempt,
  historical snapshots, edit restrictions, credits, and case data unchanged.
- Preserve Spec 136's separate persistent green Offer Accepted outcome shortcut.
  On its completion page, select Offer Accepted and leave numbered attempts gray.
- Preserve the existing all-gray numbered attempts in closed-case review.
- Use the same viewed-attempt highlight rule in the multi-attempt demo.
- When reviewing an older real attempt, describe the viewed read-only attempt
  in the progress status rather than describing the latest attempt as selected.

## Regression verification

- Extend the existing accepted-offer navigation matrix for both response
  implementations, open/reopened cases, and desktop/mobile widths.
- Visit attempts 3, 2, and 1 from completion and verify selection, actual computed
  circle colors, reload, file navigation, and return to accepted completion.
- Exercise the multi-attempt demo through its real controls and review saved
  attempts after acceptance. Verify only the viewed numbered circle is green.
- Fail on unexpected API requests, page errors, or real-case mutations.
