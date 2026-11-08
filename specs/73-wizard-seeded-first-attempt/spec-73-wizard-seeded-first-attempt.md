# Spec 73: Wizard-Seeded First Attempt

- **Status:** Specified; implementation and tests in the same pull request
- **Related issue:** [#261 — Wizard Save and continue must open the attempt screen, not the settlement-planning page](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/261)
- **Parent issue:** [#209 — Set up owner-only private beta and repeatable UAT environment](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/209)
- **Related specifications:** [Spec 56: Account-Backed Wizard Intake Draft](../56-account-backed-wizard-intake/spec-56-account-backed-wizard-intake.md), [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 66](../66-wizard-navigation-and-home/spec-66-wizard-navigation-and-home.md), [Spec 70: Attempt-First Real-Case Workspace](../70-attempt-workspace-entry/spec-70-attempt-workspace-entry.md), [Spec 71: Executable Signed-In Entry Contract](../71-signed-in-entry-regressions/spec-71-signed-in-entry-regressions.md)
- **Superseded historical requirements:** No historical specification is edited. This spec amends Spec 66 FR-66-03 (Save and continue also creates Attempt 1) and removes, for this one explicit action only, the "creating a new attempt automatically" exclusion in Spec 70. Spec 71 is unchanged: entry never creates an attempt or reads the wizard intake to decide where to go. Spec 56 requirement 7 is retained: a failed server save never navigates.
- **Objective:** The values a user entered in the guided wizard become Attempt 1 exactly as entered, and the real attempt screen works with those values.

## Product decisions (owner, 2026-11-07)

1. Wizard values go into the attempt exactly as entered.
2. The real attempt screen must work with those entered values, and this is verified end to end.

## Mapping from wizard to attempt (as entered, no legal classification)

| Wizard input | Attempt 1 |
|---|---|
| Each asset or debt with an amount above zero | One ledger asset/debt (stable ID derived from the case and the entry ID) with a single `valuation` event: provenance `user_reported`, amount equal to the entered amount in cents, date = the acquired date if entered, otherwise the date the draft was last saved. The note carries the entered category, owners, holding, and acquisition method as text. |
| Entry with no amount or an amount of zero | Not added; listed as not included, with the reason. |
| Marriage date, or else cohabitation start date, and separation date | One relationship window labelled "As entered in your case information" (`marriage_only` when the start is the marriage date, otherwise `alternate` with a note that the start is the entered cohabitation date and not a legal classification). |
| Cohabitation, marriage, separation, and petition dates that are known | Attempt milestones with those dates. |
| Role (Petitioner or Respondent) | Offer from = the entered role, offer to = the other role. |
| Issues and goals; known agreements | Proposal terms in the entered order ("Issue — topic: outcome", "Agreement — summary (date)"); any beyond the 80-term limit are listed as not included. |
| Anything not entered (proposed amounts, separate or community classification, community share) | Left empty or unresolved. The engine reports each entered amount as an unresolved total. The one required community-share axis uses the existing editable default of 50.00%; it does not affect unresolved amounts. |

## Requirements

- **FR-73-01 — Create the first attempt:** `POST /cases/{case_id}/wizard-attempt` (case owner, write access, closed cases refused) reads the saved wizard draft and creates Attempt 1 in one transaction using the existing ledger, scenario, selection, and attempt rules with no AI step and no consent. It returns `status` = `created`, `exists`, or `needs_information`, the list of `needs`, and a `report`.
- **FR-73-02 — As entered:** The mapping above is the only transformation. Amounts are not rounded or converted beyond dollars to cents, and no classification, tracing, or share is inferred.
- **FR-73-03 — Needs information, never a fake attempt:** When there is no entry with an amount, or no start date (marriage or cohabitation) or separation date, the call writes nothing, returns `needs_information` with the specific missing items, and creates no attempt.
- **FR-73-04 — Idempotent and race-safe:** The case is locked; derived IDs and idempotency keys are deterministic; a second or concurrent call returns `exists` and changes nothing. A case that already has an attempt from any path returns `exists`.
- **FR-73-05 — All or nothing:** A failure leaves no ledger event, scenario run, selection, or attempt behind and returns a retryable error.
- **FR-73-06 — Report and read:** `GET /cases/{case_id}/wizard-attempt` returns `attempt_exists`, the `needs` that would block creation, and the stored `report` (included assets and debts with their entered amounts, dates used, role, counts, and every excluded item with its reason). The report is stored with the case and never contains more than the user entered.
- **FR-73-07 — Existing attempts are immutable:** Later wizard edits do not change an existing attempt (Spec 22). The attempt screen says so next to **Edit case information**.
- **FR-73-08 — Save and continue:** After the draft is saved on the server, the wizard calls the creation endpoint and then opens `/`, which shows the attempt screen, for `created`, `exists`, and `needs_information`. If the call fails, the user stays on the wizard with the error and can retry; the draft stays saved.
- **FR-73-09 — Attempt screen without an attempt:** A wizard-path case with no attempt shows the reason (the `needs`) and two actions: **Create Attempt 1 from your case information** and **Edit case information**. Entry never creates the attempt on its own.
- **FR-73-10 — Attempt screen with the values:** Attempt 1 opens with its progress and a "Values from your case information" panel listing each included asset and debt with its entered amount, the dates and role used, and every excluded item with its reason. The offer and asset comparison lists the same assets with the same totals. The user can edit proposed amounts, terms, dates, and milestones, and the edits persist across reload.
- **FR-73-11 — Security and limits:** Non-members get 404 and non-owner members 403. Entries are bounded by the existing wizard (250 entries) and ledger limits; amounts are never logged.

## Acceptance criteria

1. A wizard with a role, dates, two assets, and one debt, finished with Save and continue, opens Attempt 1 whose panel and comparison show exactly the entered names and amounts.
2. A second Save and continue, a reload, and a sign-in all open the same Attempt 1 and create nothing new.
3. Missing amounts or dates produce `needs_information` and an explanatory screen with the two actions, with nothing written.
4. A forced failure inside creation leaves no partial ledger, run, selection, or attempt.
5. Entered amounts equal the displayed amounts to the cent, and an entry with no amount is reported as not included.
6. Editing a proposed amount on Attempt 1 persists after reload; editing the wizard afterwards does not change Attempt 1.
7. Automated unit, route, and source tests pass, and the full flow was run in a browser against PostgreSQL with object storage.

## Implementation boundary

No change to finalization, credits, scenario mathematics, AI consent, or the documents path. Corrections to entered amounts after Attempt 1 exists use the existing append-only ledger and the attempt's own editable fields.
