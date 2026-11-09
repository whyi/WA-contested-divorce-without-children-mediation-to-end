# Spec 100: Close an Accepted Case and Permanently Freeze Its Attempts

- **Status:** Implemented; PR review
- **Related issue:** [#334 — Add a close-your-case action to accepted-offer completion](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/334)
- **Related issues:** [#82 — Open a dedicated completion page after offer acceptance](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/82), [#108 — Add clear actions to settlement completion page](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/108), and [#126 — Keep closed cases reopenable and provide complete user data export](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/126)
- **Related specifications:** [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 25: Accepted Offer Completion Page](../25-accepted-offer-completion-page/spec-25-accepted-offer-completion-page.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), and [Spec 35: Attempt Finalization and Snapshot](../35-attempt-finalization-snapshot/spec-35-attempt-finalization-snapshot.md)
- **Amends:** Specs 25 and 32 only for the authenticated accepted-offer completion action and the immutability of negotiation attempts after accepted case closure. Existing specifications remain unchanged.
- **Objective:** Let a user explicitly close the product case from the accepted-offer completion page and permanently lock every negotiation attempt without deleting case data or removing the ability to reopen the case for review and export.
- **Scope:** Authenticated accepted-offer completion, user-confirmed accepted case closure, server-enforced immutability of every existing negotiation attempt, and preservation of Spec 32 reopen/export behavior. Fictional demos, legal case status, and permanent deletion are out of scope.

## Functional requirements

- **FR-100-01 — Separate completion actions:** On the authenticated accepted-offer completion page, show **Close your case** as a distinct action from **Back to your case**. Keep the existing return navigation available and functional.
- **FR-100-02 — Confirm intent:** Before closing, explain that all negotiation attempts will become permanently read-only, case data will not be deleted, and the closed case can still be reopened for review and export. The user must confirm. Canceling makes no request and changes no state.
- **FR-100-03 — Verify accepted context:** Enable the close action only after the server-authorized page has verified that the case and offer response are valid and accepted. Do not expose this action as a real-case operation in the fictional demo.
- **FR-100-04 — Existing lifecycle and authorization:** Close the case through the existing authenticated, owner-authorized case lifecycle and its existing session, CSRF, and error-handling protections. Do not create a competing closure endpoint or report success before the server confirms the operation.
- **FR-100-05 — Permanently lock every attempt:** On confirmed accepted closure, persist an immutable closure-time state for every negotiation attempt in the case, including attempts that were not already finalized or frozen. Preserve any existing finalization snapshots without replacing or weakening them. Enforce the lock server-side across all attempt mutation, outcome, finalization, and next-attempt creation routes.
- **FR-100-06 — Lock survives reopening:** Reopening an accepted-closed case remains available under Spec 32 for review and export, but never restores editability of its existing attempts and never permits a new negotiation attempt. Other Spec 32 reopen, retention, and export behavior remains unchanged.
- **FR-100-07 — Preserve case data and entitlements:** Accepted closure does not delete or purge documents, attachments, attempt history, snapshots, generated files, lifecycle events, or credits. Existing export includes the retained attempt history and closure state.
- **FR-100-08 — Accurate process boundary:** State that closing the product workspace does not itself resolve a divorce, establish legal effect, file documents, or change legal status. Do not imply that the application sent or delivered any proposal.
- **FR-100-09 — Accessible outcomes:** Announce closure success, cancellation, and errors accessibly. On failure, keep the page usable and do not show a success state or navigate as if closure succeeded.
- **FR-100-10 — Demo isolation:** Keep fictional accepted-offer completion behavior unchanged; demo actions must not call authenticated case-closure or attempt-lock routes.

## Acceptance criteria

1. The authenticated accepted-offer completion page presents both **Back to your case** and **Close your case** as distinct actions.
2. The close confirmation describes the permanent attempt lock, retained case data, and continued reopen/export access.
3. Canceling confirmation changes nothing. Invalid context, authorization failure, or server error is announced and never appears successful.
4. After confirmed closure, every attempt is immutable on the server, including attempts without a prior finalized snapshot; no attempt can be edited, have its outcome changed, be finalized differently, or spawn a successor.
5. Reopening the case preserves all attempts, closure-time state, snapshots, files, credits, and export access, while all attempts remain read-only and no new attempt can be created.
6. Existing finalized/frozen attempt snapshots and the Spec 32 deletion, retention, closure, reopen, and export boundaries are preserved.
7. Fictional demo behavior remains isolated.
8. Automated tests cover accepted-context validation, confirmation and cancellation, owner authorization, server errors, attempt immutability, reopen persistence of the lock, export preservation, and demo isolation.

## Implementation

- Added a nullable case-level `attempts_locked_at` marker and a migration that backfills previously accepted-closed cases.
- Accepted closure sets the persistent lock; the lock survives reopening and is included in case export metadata. Other closure reasons do not set it.
- Settlement writes, offer-response mutations, asset-mediation mutations/uploads, and new wizard attempts enforce the lock on the server. Accepted completion remains idempotently verifiable after a successful closure.
- The authenticated completion page displays the close action only after accepted state is verified. It requires confirmation, reports failures without navigation, and moves to Account only after the server confirms the attempt lock. Demo completion retains no real-case close action.
- Backend and browser UAT tests cover lock persistence, accepted closure, cancellation/error behavior, both completion API paths, reopen behavior, and demo isolation.
