# Spec 65: Direct Entry After Sign-In

- **Status:** Implemented; automated tests passing
- **Related issue:** [#241 — Open the active case or new-case start choice directly after sign-in; remove the Active cases workspace page](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/241)
- **Parent issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 04: Initial Onboarding Empty-State Dashboard and Dual-Path Routing](../04-initial-onboarding-empty-state/requirements.md), [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md), [Spec 44: Single-Case Demo Flow](../44-single-case-demo-flow/spec-44-single-case-demo-flow.md), [Spec 64: One General Account Type](../64-single-general-account/spec-64-single-general-account.md)
- **Superseded historical requirements:** No historical specification is edited. This spec supersedes, for signed-in accounts only, the case-list dashboard ("Your case workspace" with an "Active cases" list) that Spec 04 and Spec 34 FR-34-15 describe, and amends Spec 32 FR-32-09 as stated below. Spec 44 FR-44-02 (no case-list dashboard in demos) is extended, unchanged, to real accounts.
- **Objective:** After sign-in, take the user straight to the work: their case, or the new-case start choice. Never show a case-list page first.

## Requirements

- **FR-65-01 — Active case:** When the account owns an active case, sign-in and every later visit to the app while signed in open that case's working screen: its guided-wizard or documents path when the case has one, otherwise the attempt/settlement screen. The user clicks nothing to reach it.
- **FR-65-02 — No case:** When the account owns no case, the new-case start choice (documents or guided wizard, with the existing-offer question) opens immediately. Cancelling it leaves a visible "Start a new case" action; no list page appears.
- **FR-65-03 — Only a closed case:** When the account's only case is closed, the app shows the closed case with its Reopen and Export actions and no empty case list. An account cannot create a second case (Spec 64 FR-64-03).
- **FR-65-04 — Removed page:** No signed-in screen shows "Your case workspace" or "Active cases", a case-list heading, or a case tile. The dashboard status endpoint is unchanged.
- **FR-65-05 — Replace navigation:** The entry decision navigates with replace semantics so the browser Back button never bounces between the entry and the case.
- **FR-65-06 — Return links:** Links that used to return to the case list now lead to the case: the completion pages' "Back to your case" link re-enters the app (which opens the case), and the case screen's back link opens the Account area. The guided wizard's finish button is "Save draft" and keeps the user on the case instead of navigating to a list.
- **FR-65-07 — Account area:** An "Account" entry (`/?view=account`) in the header, available whenever the user is signed in, opens the account area without redirecting. It holds the closed-cases list (Reopen, Export data) and permanent account deletion, plus a "Back to your case" link. Per-case export and attempt-credit purchase stay on the case's own screen. This amends Spec 32 FR-32-09: the closed-cases section moves from the case list into the account area and, per FR-65-03, appears directly when no active case exists.
- **FR-65-08 — Unchanged surfaces:** Signed-out visitors, sign-in and recovery, Demo 1 and Demo 2, and the case, attempt, wizard, and document screens themselves are unchanged.
- **FR-65-09 — States:** Loading, retryable error, and expired-session states keep working. The start-choice dialog and the redirect keep correct keyboard focus and screen-reader announcements, and the page never flashes the removed list.

## Acceptance criteria

1. Signing in with an active case opens that case without first rendering a case list.
2. Signing in with no case shows the documents-vs-wizard choice at once; cancelling leaves a "Start a new case" button.
3. Signing in with only a closed case offers Reopen and Export and no "Active cases" list.
4. The text "Your case workspace" and "Active cases" does not appear in any signed-in screen.
5. Back does not loop; the Account entry opens the account tools without redirecting.
6. Automated tests cover the entry decision for active, none, and closed-only accounts and the removed text.

## Implementation boundary

The behavior is implemented in the single-page client; no API contract changes. Account-area content and the case screens are reused as they are.

## Verification

Structure tests are in `tests/test_direct_entry_after_sign_in.py`. The entry decision was also exercised in a browser against PostgreSQL for an account with an active guided-wizard case, no case, only a closed case, and a legacy case without a start path, confirming direct entry, no flash of the removed list, and the Account area.
