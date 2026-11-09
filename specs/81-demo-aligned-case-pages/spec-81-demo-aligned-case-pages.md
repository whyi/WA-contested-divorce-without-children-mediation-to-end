# Spec 81: Demo-aligned real case pages

## Amendments

This additive specification supersedes the documents-screen presentation in
specs 77 and 78, and amends the separate real-case presentation in specs 79 and
80. Prior specifications remain historical records. Spec 76's removal of the
technical negotiation planner remains in force.

## Documents entry

- Selecting **I have documents** creates the case once and opens the document
  selection page directly, without an intermediate confirmation or offer question.
- Reuse the existing demo document-page template, including the heading hierarchy,
  PDF/DOCX selector, selected-file list, removal controls, disabled empty-state
  **Next**, and **Back to Asset Overview** link.
- Do not retain the previous materials-workflow page, cloud-picker cards, import
  button, offer checkbox, analysis/consent/review panels, or duplicate Back controls.
  Remove their unused event handlers and styles rather than hiding the old page.
- Real-account copy must distinguish selection from storage. Selection stays local;
  **Next** saves files to the existing case and opens Asset Overview. It does not
  request AI analysis. Demo selection remains browser-local and never uploads.
- Preserve the case when returning to Asset Overview. Do not delete a new case
  merely because the user follows Back.
- Enforce server-provided file type, 2 MB size, and account attachment limits.
  Keep selected files and stable import identities after a failure. Reconcile an
  uncertain previous write before retrying; do not duplicate successful siblings.

## Real case presentation

- Reuse Demo 1's Asset Overview and Case file management structures and styles for
  Free accounts. Use Demo 2's attempt presentation allowance for paid entitlement.
- Free preparation shows only the first attempt; paid preparation allows three
  displayed attempt positions. Preserve existing saved historical attempts rather
  than deleting user data. Future positions are disabled and do not grant credits.
- Use verified billing entitlement, not a hardcoded email or fictional account data.
- Reuse the milestone editor, four-column comparison table, timeline controls,
  trend chart, and discussion-scenario card layout. Do not populate real cases with
  fictional dates, balances, or inferred party ownership.
- Allow explicit dated, nullable signed balances in integer cents. Display missing
  values and incomplete totals as unavailable; debts are entered as negative values.
  Preserve cents when displaying user-entered amounts.
- Save overrides and milestones in revisioned case metadata, independent of source
  records. Owner-only writes require case locking and optimistic revision checks.
  Closed cases and frozen/finalized attempts remain read-only. Historical views
  read only their saved profile, never current overrides or wizard answers.
- Keep source records accessible in a separate disclosure. Local comparisons do
  not restore the removed planner, AI ranking, or fictional proposal downloads.

## File management

- Use the demo file-manager layout with real server documents and Add, Download,
  Replace, Delete, and refresh operations. Do not fabricate original filenames.
- Replacement uploads first, then permanently deletes the old file only after
  confirmed upload success. A spare attachment slot is required.
- Surface failures and refresh the file list so retained replacements are visible.
  Offer retry using the original import identity. Never show successful replacement
  when either upload or deletion failed.
- Deletion requires explicit confirmation and immediately returns the attachment
  slot through the existing server deletion API.

## Verification

- Chromium tests exercise direct creation, demo-template structure, responsive
  document selection, deferred imports, partial failure/idempotent retry, session
  expiry, Free/paid attempt counts, saved balances, reload, and deletion recovery.
- Backend tests cover nullable integer amounts, date/category uniqueness, bounds,
  exact totals, owner access, revision conflicts, read-only states, and logged,
  retryable storage failures. Existing document-processing APIs remain available.
