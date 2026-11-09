# Spec 105: View Closed Cases Without Reopening

- **Status:** Implemented; PR review
- **Related issue:** [#336 — View closed cases without reopening them](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/336)
- **Related issues:** [#126 — Keep closed cases reopenable and provide complete user data export](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/126) and [#334 — Add a close-your-case action to accepted-offer completion](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/334)
- **Related specifications:** [Spec 32: Reopenable Case Closure and Complete Data Export](../32-reopenable-case-closure-and-export/spec-32-reopenable-case-closure-and-export.md) and [Spec 100: Close an Accepted Case and Permanently Freeze Its Attempts](../100-accepted-case-close-freezes-attempts/spec-100-accepted-case-close-freezes-attempts.md)
- **Amends:** Spec 32 only to add a read-only viewing action for closed cases. Existing reopen, export, retention, and credit requirements remain unchanged.
- **Objective:** Allow an owner to inspect a closed case without reopening it or changing its lifecycle state.
- **Scope:** My Account closed-case actions and authenticated read-only case review. Case reopening, permanent deletion, legal case status, and changing case content are out of scope.

## Functional requirements

- **FR-105-01 — Separate view and reopen actions:** Show **View** immediately to the left of **Reopen** for each closed case in My Account. Keep **Reopen** and **Export data** available as separate actions.
- **FR-105-02 — View without lifecycle change:** Selecting **View** opens only the selected case for review. It does not call the reopen endpoint or change the case's closed status, closure reason, attempt lock, or credits.
- **FR-105-03 — Verify closed-case access:** A direct read-only URL must verify the authenticated owner and confirm that the selected case is still listed as closed before exposing its contents. Do not treat a query parameter alone as authorization or proof of closure.
- **FR-105-04 — Read-only review:** Display saved case information, negotiation attempts, and available case files without edit, upload, deletion, response, finalization, or new-attempt actions. Disable or omit mutating controls and prevent mutation requests from the read-only view.
- **FR-105-05 — Preserve accepted locks:** Viewing an accepted-closed case does not unlock any attempt. Its negotiation attempts remain read-only before, during, and after viewing.
- **FR-105-06 — Return to Account:** Provide a clear route back to My Account. After returning, the case remains listed as closed with View, Reopen, and Export actions.
- **FR-105-07 — Errors and accessibility:** Announce loading and errors accessibly. If authentication, ownership, or closed status cannot be verified, do not show case data; provide an actionable return to Account.

## Acceptance criteria

1. Closed-case rows render **View**, **Reopen**, and **Export data** in that order.
2. View opens the selected case in a visibly identified read-only state without issuing a reopen request or mutation request.
3. The server-confirmed case remains closed with the same closure reason and attempt-lock state.
4. Direct navigation to a read-only URL is rejected from the viewing flow unless the case is authenticated, owner-accessible, and currently closed.
5. Edit, upload, deletion, mediation response, proposal finalization, and next-attempt controls cannot mutate data from the read-only view.
6. Accepted-closed cases retain their persistent attempt lock.
7. Returning to Account preserves all existing Reopen and Export behavior.
8. Browser regression tests cover action order, selected-case navigation, read-only affordances, no-mutation behavior, and preservation of closed state.

## Implementation

- Added an owner-authorized View action before Reopen in each Account closed-case row.
- The view route verifies the selected case against the authenticated closed-case list and loads its existing workspace in read-only mode.
- Read-only mode shows a closed-case banner and Account return link, disables or omits mutating controls, preserves safe navigation and downloads, and blocks non-GET API requests client-side. Existing server-side closed-case authorization remains authoritative.
- Added browser regression tests for ordering, closed-state verification, navigation, mutation isolation, and Account actions.
