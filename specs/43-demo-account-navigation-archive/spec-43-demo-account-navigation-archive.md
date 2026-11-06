# Spec 43: Demo Account Navigation, Entitlements, and Archive

- **Status:** Implemented; focused regression tests pass
- **Related issue:** [#171 — Fix Demo 1 and Essential demo case navigation, limits, and archive behavior](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/171)
- **Related specifications:** [Spec 12: Demo Entry Points](../12-demo-entry-points/spec-12-demo-entry-points.md), [Spec 34: Party-Owned Case with One Invited Operator at a Time](../34-party-owned-case-delegation/spec-34-party-owned-case-delegation.md), [Spec 42: Case Attachment Upload Limits](../42-case-attachment-upload-limits/spec-42-case-attachment-upload-limits.md)
- **Superseded historical requirements:** This spec does not change real-account ownership or case limits. It supersedes demo-only behavior that hard-codes case navigation to Demo 2, renders archived examples as disabled previews, or applies the Free attempt limit to the Essential demo. Spec 30's one-attempt demo behavior remains applicable to Demo 1 (Free).
- **Objective:** Keep each browser-only demo account and its fictional cases isolated and navigable, present the correct demo entitlement, and make demo archiving reversible.
- **Scope:** Demo 1 (Free) and Demo 2 (Essential) dashboards, demo-only case creation/navigation, demo-only archived case state, and the Asset Overview entry path. No real-case persistence, billing, or authorization behavior changes.

## Functional requirements

- **FR-43-01 — Demo identity:** Every demo page resolves to one demo identity (`demo1` or `demo2`). Dashboard entry paths define their identity; subsequent demo intake, Asset Overview, file-management, and return links preserve it.
- **FR-43-02 — Isolated browser state:** Demo 1 and Demo 2 fictional cases and archive state use distinct browser-local storage namespaces. Demo state is never sent to real-case APIs or used to mutate authenticated cases.
- **FR-43-03 — Demo case identifiers:** A demo case is addressed with a demo-specific query parameter, never the authenticated `case_id` parameter. Demo identifiers must not trigger real-case entitlement, membership, or case-limit checks.
- **FR-43-04 — Return navigation:** “My cases” and intake back links return to the dashboard belonging to the current demo identity, preserving the selected case context when returning to Asset Overview.
- **FR-43-05 — Demo 1 default:** Demo 1 starts with no created cases. Completing the selected fictional intake route creates/reuses a browser-local demo case and returns to the Demo 1 Asset Overview. Returning to “My cases” shows that case on the Demo 1 dashboard.
- **FR-43-06 — Essential dashboard:** Demo 2 starts with the existing fictional active case `XYZ vs ABC` and retains a visible action for starting another fictional case until its three-active-case demo capacity is reached. Free supports one active demo case; archived cases do not count toward active capacity. Each case limit is enforced in the demo UI and by its local state transition.
- **FR-43-07 — Correct plan behavior:** Demo 1 (Free) has one active case and one attempt per case; Demo 2 (Essential) has three active cases and three attempts per case, matching the catalog in Spec 30. Essential must never display Free-plan limits or Free-plan upgrade/limit errors. Plan messaging shown by a demo is derived from the demo identity and must not be inferred from a real signed-in account or stale client state. Real accounts continue to use trusted server entitlement.
- **FR-43-08 — Reversible archive:** Each active demo case can be archived without deletion. It disappears from Active cases and appears in an enabled Archived cases list. Restoring it moves the same case and its browser-local work back to Active cases. Archiving or restoring one case does not change another case or the other demo identity.
- **FR-43-09 — Persistence and error visibility:** Demo case creation, archive, and restore survive reloads in the same browser. Invalid or unavailable local storage must produce a visible error; it must not silently replace the user's demo state with an empty list.
- **FR-43-10 — Real-case isolation:** Demo navigation and archive controls do not call real-case close/reopen/delete endpoints, create account-owned cases, or change real-case plan entitlements.

## Acceptance criteria

1. Starting Demo 1 Free, choosing an intake path, and reaching Asset Overview preserves `demo1`; selecting “My cases” returns to the Demo 1 dashboard with the same created case.
2. The Essential dashboard shows `XYZ vs ABC` as active and keeps an enabled action to start a new demo case.
3. Completing an intake started from Essential returns to Essential; no page in that flow presents a Free-plan limit.
4. Archiving an active demo case removes it from Active cases and lists it under Archived cases; restoring it returns the same case to Active cases.
5. Archive/restore and created cases persist after reload and remain isolated between Demo 1 and Essential.
6. Demo identifiers never populate the real `case_id` query parameter or call real-case entitlement/case mutation APIs.
7. Existing authenticated case access, ownership, billing, close/reopen, and permanent-deletion behavior remains unchanged.
8. Demo 1 stops at one active case and one attempt per case; Essential permits up to three active cases and three attempts per case, with no Free-limit messaging in the Essential flow.

## Out of scope

Real-account archiving (which remains governed by case close/reopen), concurrent demo collaboration, real billing changes, changes to the one-case-per-party rule, or deletion of demo data outside the browser.
