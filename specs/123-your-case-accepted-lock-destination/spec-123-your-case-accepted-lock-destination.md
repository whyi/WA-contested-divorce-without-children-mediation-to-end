# Spec 123: Your Case Preserves Accepted Completion Across Locks

- **Issue:** [#381](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/381)
- **Amends:** Spec 122 requirement 3 and earlier reopened-case routing exceptions
  in Specs 120 and 121. Historical specifications remain unchanged.

## Requirements

1. The global **Your case** link must open the verified saved accepted
   completion destination whenever `accepted_offer_url` is present, including
   reopened cases with `attempts_locked_at` and completed, locked responses.
   Apply the same rule from completion, attempt, Account and homepage views.
2. Clicking **Your case** from accepted completion must not return to an
   attempt. Explicit **Back to attempt #N** navigation remains available.
3. If no accepted target exists, open the latest saved attempt. Preserve
   existing closed-view parameters, ownership/context verification, same-origin
   validation, explicit errors and retry behavior.
4. Navigation must not write case data, clear locks, restore editability,
   consume credits or change closure status. Spec 100's retained read-only
   review and export boundaries remain unchanged.

## Regression verification

- Reproduce the prior incorrect attempt destination before fixing the resolver.
- At desktop/mobile widths, verify asset and selection accepted targets for
  first and third attempts with and without persistent locks.
- Click the header from completion itself, reload, explicitly return to the
  attempt and click again; also verify Account and homepage entry.
- Preserve rejected/counteroffer fallback and invalid-target failures.
- Verify the actual authenticated HTTPS 8002 accepted-and-locked case without
  substituting workspace/response state and without case mutations.
