# Spec 120: Your Case Opens the Final Timeline Circle

- **Issue:** [#377](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/377)
- **Amends:** Spec 65 signed-in Your case navigation only. Existing
  specifications remain unchanged.

## Requirements

1. The signed-in **Your case** header link and homepage open-case actions
   resolve the final available timeline circle, not Account. This rule is
   independent of the last viewed historical attempt.
2. Resolve the active case from the authenticated dashboard or, when none is
   active, the existing closed-case API. Verify workspace identity and closure
   state. For a closed case verify the closure timestamp still matches.
3. Use the maximum saved attempt ordinal (or #1 for an untouched workspace).
   Future disabled circles are not destinations. If the timeline includes an
   Offer Accepted circle, use the verified same-origin accepted-completion
   target instead. An open previously accepted/locked case without that circle
   goes to its latest attempt, preserving existing reopened-case behavior.
4. Closed destinations include `view=closed`; navigation never reopens,
   modifies, creates or closes a case. Accepted and historical locks remain
   unchanged. Account itself remains available through its distinct link.
5. Failed lookup, mismatched identity/closure, malformed attempts or unsafe
   completion targets produce the existing accessible dashboard error/retry.
   No Account fallback or success-shaped destination is permitted.
6. With no active or closed case, retain the new-case start choice.

## Regression coverage

- Signed-in homepage and Account header links, desktop/mobile, reload,
  active/closed ordinary and accepted cases, reopened cases and historical
  attempt context.
- Maximum ordinal, closed read-only destination, no case mutations, no Account
  interstitial, lookup failure/retry and rejected foreign/wrong-case targets.
