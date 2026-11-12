# Spec 140: Unified Permanent Attempt Locks on Case Closure

- **Issue:** [#427](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/427)
- **Amends:** Spec 104's resumed stopped-mediation behavior and nonaccepted
  reopening editability in Specs 32, 117, and 139. Preserve historical specs.

## Requirements

1. Account, rejected-attempt, and accepted-completion closure use the same
   confirmation, with title **Close your case?** and exactly two buttons,
   **Cancel** and **Close case**:

   > Close this Casework case? Every negotiation attempt will become permanently read-only, even if you later reopen the case. Your case data is not deleted; you can reopen it for review and export. This does not resolve your divorce case, file documents, or change its legal status.

2. Every successful case closure, regardless of reason, sets the existing
   persistent `attempts_locked_at` if it is absent. Repeated closure and
   reopening retain its original timestamp. Reopening an older closed case
   without a lock sets it from the saved closure timestamp.
3. Reopening never clears a stopped mediation state or its revision and never
   restores proposal editing or creates/unlocks negotiation attempts. Apply
   the existing accepted-case attempt lock to ordinary and stopped closures,
   including asset-value edits. Existing accepted-case response-only exceptions
   remain unchanged; this specification does not expand those exceptions.
4. Preserve all case data, files, saved attempt snapshots, credits, review and
   unrestricted case-data exports. No deletion, refund, or credit expiry is
   introduced by closure. Cancel and failed closure must not establish locks.

## Regression verification

- Check identical full rendered copy and button-only controls at every closure
  entry point, including desktop/mobile Account and rejected-attempt flows.
- Close ordinary and stopped cases, reopen, and verify persistent locks,
  unchanged stopped response metadata, blocked asset/proposal/continuation
  writes, retained credits and snapshots, and successful retained exports.
- Preserve idempotent closure, existing accepted completion behavior,
  authorization, failure recovery, and legacy closed-case reopening.
