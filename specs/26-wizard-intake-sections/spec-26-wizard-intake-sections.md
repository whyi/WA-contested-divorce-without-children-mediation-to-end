# Spec 26: Interactive Wizard Intake Sections

- **Status:** Implemented; automated tests passing
- **Related issue:** [#84 — Make wizard intake sections interactive and support optional file attachments](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/84)
- **Objective:** Make the Wizard demo's Dates, Finances, Issues, Agreements, and Review sections clearly navigable and immediately usable, with optional supporting-file attachments.
- **Scope:** `/demo/wizard` and its browser-local draft. This does not add authenticated case persistence or server-side file upload.

## 1. Section Navigation and Entry

- **FR-26-01 — Responsive section navigation:** Activating a Wizard section link must visibly navigate to and focus the target section, and expose the current section accessibly.
- **FR-26-02 — Actionable empty collections:** If Finances, Issues, or Agreements has no entries, activating its section link must create and focus one blank entry. Users may remove it or add more entries.
- **FR-26-03 — Editable entries:** Support multiple finance items, issues/goals, and agreements with their existing relevant fields; edits, additions, and removals update the review and local draft.
- **FR-26-04 — Return and keyboard use:** Section navigation must work with keyboard activation and retain the page's vertical scroll behavior.

## 2. Optional Attachments and Privacy

- **FR-26-05 — Optional supporting files:** Each finance item, issue/goal, and agreement may have multiple local file attachments, with filenames and removal controls visible.
- **FR-26-06 — Browser-local persistence:** Store selected file data together with the local draft where browser storage permits; restore it on reload and report storage failures visibly.
- **FR-26-07 — No upload in demo:** Files remain in browser-local storage and are not sent to the server or analyzed. The UI must state this clearly.

## 3. Acceptance Criteria

1. Selecting Dates, Finances, Issues, Agreements, or Review visibly moves focus to the corresponding section.
2. Selecting an empty Finances, Issues, or Agreements section presents a focused editable record without requiring a second discovery click.
3. Users can create, edit, and remove multiple entries in each collection; the Review updates accordingly.
4. Each record type supports multiple optional attachments, displays filenames, supports removal, and restores files from local storage where supported.
5. Browser storage errors are visible; no file is uploaded to the server.
6. Existing filed-case gate and unrelated workflow behavior are unchanged.
7. The Wizard clearly tells users how the filed-case and role selections unlock the intake sections.
8. The finish action visibly confirms the browser-local save in Existing demo and clearly states that the separate fictional demo does not use Wizard answers.

## 4. Implementation Status

- Section navigation now moves focus to each destination, marks the active step, and automatically creates the first editable finance, issue, or agreement entry when that collection is empty.
- Existing multi-entry forms, optional attachments, filename/removal UI, browser-local IndexedDB persistence, and visible storage errors are retained.
- Added route-level regression coverage for navigation behavior and local-only attachments.
- The finish action now navigates only after a successful local save and displays an accessible notice in Existing demo so the separate demo's behavior is clear.
- Full automated test suite passes.
